using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Services
{
    public class BookingService : IBookingService
    {
        private readonly IBookingRepository _bookingRepository;
        private readonly ILawyerRepository _lawyerRepository;
        private readonly IPricingRepository _pricingRepository;
        private readonly IChatRoomRepository _chatRoomRepository;
        private readonly INotificationRepository _notificationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<BookingService> _logger;

        public BookingService(
            IBookingRepository bookingRepository,
            ILawyerRepository lawyerRepository,
            IPricingRepository pricingRepository,
            IChatRoomRepository chatRoomRepository,
            INotificationRepository notificationRepository,
            LawyerConnectDbContext context,
            ILogger<BookingService> logger)
        {
            _bookingRepository = bookingRepository;
            _lawyerRepository = lawyerRepository;
            _pricingRepository = pricingRepository;
            _chatRoomRepository = chatRoomRepository;
            _notificationRepository = notificationRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<BookingResponseDto> CreateBookingAsync(int userId, BookingCreateDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Creating booking for user {userId} with lawyer {dto.LawyerId}");

                // Validate booking date is in the future (at least 1 hour from now)
                if (dto.Date <= DateTime.UtcNow.AddHours(1))
                {
                    _logger.LogWarning($"Booking creation failed: Invalid date {dto.Date} for user {userId}");
                    throw new ArgumentException("Booking date must be at least 1 hour in the future");
                }

                // Validate lawyer exists and is verified
                var lawyer = await _lawyerRepository.GetByIdAsync(dto.LawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Booking creation failed: Lawyer {dto.LawyerId} not found");
                    throw new ArgumentException("Lawyer not found");
                }

                if (!lawyer.IsVerified)
                {
                    _logger.LogWarning($"Booking creation failed: Lawyer {dto.LawyerId} is not verified");
                    throw new InvalidOperationException("Cannot book with unverified lawyer");
                }

                // Validate user cannot book with themselves (if they are also a lawyer)
                if (lawyer.UserId == userId)
                {
                    _logger.LogWarning($"Booking creation failed: User {userId} attempted to book with themselves");
                    throw new InvalidOperationException("Cannot book a consultation with yourself");
                }

                // Validate pricing exists for the specialization and interaction type
                var pricing = await _pricingRepository.GetPricingAsync(
                    dto.LawyerId, dto.SpecializationId, dto.InteractionTypeId);

                if (pricing == null)
                {
                    _logger.LogWarning($"Booking creation failed: No pricing found for lawyer {dto.LawyerId}, specialization {dto.SpecializationId}, interaction {dto.InteractionTypeId}");
                    throw new ArgumentException("Pricing not available for this specialization and interaction type");
                }

                // Check for conflicting bookings (same lawyer, overlapping time)
                var conflictingBookings = await _bookingRepository.GetLawyerBookingsForDateAsync(
                    dto.LawyerId, dto.Date, pricing.DurationMinutes);

                if (conflictingBookings.Any(b => b.Status == "Pending" || b.Status == "Confirmed"))
                {
                    _logger.LogWarning($"Booking creation failed: Time slot conflict for lawyer {dto.LawyerId} at {dto.Date}");
                    throw new InvalidOperationException("This time slot is not available");
                }

                // Create booking with price snapshot
                var booking = dto.ToBooking(userId, pricing.Price, pricing.DurationMinutes);

                await _bookingRepository.AddAsync(booking);

                // Create chat room for the booking
                var chatRoom = new ChatRoom
                {
                    BookingId = booking.Id,
                    CreatedAt = DateTime.UtcNow
                };
                await _chatRoomRepository.AddAsync(chatRoom);

                // Create notifications for both client and lawyer
                var clientNotification = new Notification
                {
                    UserId = userId,
                    Title = "Booking Created",
                    Message = $"Your booking with {lawyer.User.FullName} for {dto.Date:MMM dd, yyyy 'at' HH:mm} has been created. Please complete payment to confirm.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(clientNotification);

                var lawyerNotification = new Notification
                {
                    UserId = lawyer.UserId,
                    Title = "New Booking Request",
                    Message = $"You have a new booking request for {dto.Date:MMM dd, yyyy 'at' HH:mm}. Awaiting payment confirmation.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(lawyerNotification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Booking {booking.Id} created successfully for user {userId} with lawyer {dto.LawyerId}");

                return booking.ToBookingResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to create booking for user {userId} with lawyer {dto.LawyerId}");
                throw;
            }
        }

        public async Task<BookingResponseDto?> GetBookingByIdAsync(int id)
        {
            try
            {
                var booking = await _bookingRepository.GetByIdAsync(id);
                if (booking == null)
                {
                    _logger.LogWarning($"Booking {id} not found");
                    return null;
                }

                return booking.ToBookingResponseDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get booking {id}");
                throw;
            }
        }

        public async Task<List<BookingResponseDto>> GetUserBookingsAsync(int userId, int page = 1, int limit = 10)
        {
            try
            {
                var bookings = await _bookingRepository.GetUserBookingsAsync(userId, page, limit);
                return bookings.ToBookingResponseDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get bookings for user {userId}");
                throw;
            }
        }

        public async Task<List<BookingResponseDto>> GetLawyerBookingsAsync(int lawyerId, int page = 1, int limit = 10)
        {
            try
            {
                var bookings = await _bookingRepository.GetLawyerBookingsAsync(lawyerId, page, limit);
                return bookings.ToBookingResponseDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get bookings for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task UpdateBookingStatusAsync(int id, string status)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var booking = await _bookingRepository.GetByIdAsync(id);
                if (booking == null)
                {
                    _logger.LogWarning($"Status update failed: Booking {id} not found");
                    throw new ArgumentException("Booking not found");
                }

                // Validate status transition
                if (!IsValidStatusTransition(booking.Status, status))
                {
                    _logger.LogWarning($"Invalid status transition from {booking.Status} to {status} for booking {id}");
                    throw new InvalidOperationException($"Cannot change status from {booking.Status} to {status}");
                }

                var oldStatus = booking.Status;
                booking.Status = status;
                await _bookingRepository.UpdateAsync(booking);

                // Create status change notification
                await CreateStatusChangeNotificationAsync(booking, oldStatus, status);

                await transaction.CommitAsync();

                _logger.LogInformation($"Booking {id} status updated from {oldStatus} to {status}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to update booking {id} status to {status}");
                throw;
            }
        }

        public async Task CancelBookingAsync(int id)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var booking = await _bookingRepository.GetByIdAsync(id);
                if (booking == null)
                {
                    _logger.LogWarning($"Cancellation failed: Booking {id} not found");
                    throw new ArgumentException("Booking not found");
                }

                // Validate booking can be cancelled
                if (booking.Status == "Completed" || booking.Status == "Cancelled")
                {
                    _logger.LogWarning($"Cancellation failed: Booking {id} is already {booking.Status}");
                    throw new InvalidOperationException($"Cannot cancel booking that is {booking.Status}");
                }

                // Check if booking is too close to start time (less than 24 hours)
                if (booking.Date <= DateTime.UtcNow.AddHours(24) && booking.Status == "Confirmed")
                {
                    _logger.LogWarning($"Cancellation failed: Booking {id} is within 24 hours of start time");
                    throw new InvalidOperationException("Cannot cancel confirmed booking within 24 hours of start time");
                }

                var oldStatus = booking.Status;
                booking.Status = "Cancelled";
                await _bookingRepository.UpdateAsync(booking);

                // Create cancellation notifications for both parties
                var clientNotification = new Notification
                {
                    UserId = booking.UserId,
                    Title = "Booking Cancelled",
                    Message = $"Your booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been cancelled.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(clientNotification);

                var lawyerNotification = new Notification
                {
                    UserId = booking.Lawyer.UserId,
                    Title = "Booking Cancelled",
                    Message = $"A booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been cancelled.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(lawyerNotification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Booking {id} cancelled successfully (was {oldStatus})");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to cancel booking {id}");
                throw;
            }
        }

        public async Task CompleteBookingAsync(int id)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var booking = await _bookingRepository.GetByIdAsync(id);
                if (booking == null)
                {
                    _logger.LogWarning($"Completion failed: Booking {id} not found");
                    throw new ArgumentException("Booking not found");
                }

                // Validate booking can be completed
                if (booking.Status != "Confirmed")
                {
                    _logger.LogWarning($"Completion failed: Booking {id} status is {booking.Status}, expected Confirmed");
                    throw new InvalidOperationException("Only confirmed bookings can be completed");
                }

                // Validate payment is completed
                if (booking.PaymentStatus != "Paid")
                {
                    _logger.LogWarning($"Completion failed: Booking {id} payment status is {booking.PaymentStatus}, expected Paid");
                    throw new InvalidOperationException("Cannot complete booking without payment");
                }

                booking.Status = "Completed";
                await _bookingRepository.UpdateAsync(booking);

                // Create completion notifications
                var clientNotification = new Notification
                {
                    UserId = booking.UserId,
                    Title = "Booking Completed",
                    Message = $"Your consultation has been completed. You can now leave a review for your experience.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(clientNotification);

                var lawyerNotification = new Notification
                {
                    UserId = booking.Lawyer.UserId,
                    Title = "Consultation Completed",
                    Message = $"Your consultation for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been marked as completed.",
                    Type = "Booking",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(lawyerNotification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Booking {id} completed successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to complete booking {id}");
                throw;
            }
        }

        #region Private Helper Methods

        private bool IsValidStatusTransition(string currentStatus, string newStatus)
        {
            // Define valid status transitions
            var validTransitions = new Dictionary<string, List<string>>
            {
                ["Pending"] = new List<string> { "Confirmed", "Cancelled" },
                ["Confirmed"] = new List<string> { "Completed", "Cancelled" },
                ["Completed"] = new List<string>(), // No transitions from completed
                ["Cancelled"] = new List<string>()  // No transitions from cancelled
            };

            return validTransitions.ContainsKey(currentStatus) && 
                   validTransitions[currentStatus].Contains(newStatus);
        }

        private async Task CreateStatusChangeNotificationAsync(Booking booking, string oldStatus, string newStatus)
        {
            string title = newStatus switch
            {
                "Confirmed" => "Booking Confirmed",
                "Completed" => "Booking Completed",
                "Cancelled" => "Booking Cancelled",
                _ => "Booking Status Updated"
            };

            string clientMessage = newStatus switch
            {
                "Confirmed" => $"Your booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been confirmed.",
                "Completed" => "Your consultation has been completed. You can now leave a review.",
                "Cancelled" => $"Your booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been cancelled.",
                _ => $"Your booking status has been updated to {newStatus}."
            };

            string lawyerMessage = newStatus switch
            {
                "Confirmed" => $"A booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been confirmed.",
                "Completed" => $"Your consultation for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been completed.",
                "Cancelled" => $"A booking for {booking.Date:MMM dd, yyyy 'at' HH:mm} has been cancelled.",
                _ => $"A booking status has been updated to {newStatus}."
            };

            // Create notification for client
            var clientNotification = new Notification
            {
                UserId = booking.UserId,
                Title = title,
                Message = clientMessage,
                Type = "Booking",
                IsRead = false,
                CreatedAt = DateTime.UtcNow
            };
            await _notificationRepository.AddAsync(clientNotification);

            // Create notification for lawyer
            var lawyerNotification = new Notification
            {
                UserId = booking.Lawyer.UserId,
                Title = title,
                Message = lawyerMessage,
                Type = "Booking",
                IsRead = false,
                CreatedAt = DateTime.UtcNow
            };
            await _notificationRepository.AddAsync(lawyerNotification);
        }

        #endregion
    }
}
