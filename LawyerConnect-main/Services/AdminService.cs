using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Models;
using LawyerConnect.Repositories;

namespace LawyerConnect.Services
{
    public class AdminService : IAdminService
    {
        private readonly IUserRepository _userRepository;
        private readonly ILawyerRepository _lawyerRepository;
        private readonly IBookingRepository _bookingRepository;
        private readonly IPaymentSessionRepository _paymentSessionRepository;
        private readonly INotificationRepository _notificationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<AdminService> _logger;

        public AdminService(
            IUserRepository userRepository,
            ILawyerRepository lawyerRepository,
            IBookingRepository bookingRepository,
            IPaymentSessionRepository paymentSessionRepository,
            INotificationRepository notificationRepository,
            LawyerConnectDbContext context,
            ILogger<AdminService> logger)
        {
            _userRepository = userRepository;
            _lawyerRepository = lawyerRepository;
            _bookingRepository = bookingRepository;
            _paymentSessionRepository = paymentSessionRepository;
            _notificationRepository = notificationRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<List<UserResponseDto>> GetAllUsersAsync(int page = 1, int limit = 20)
        {
            try
            {
                _logger.LogInformation($"Admin retrieving all users, page {page}, limit {limit}");

                // Validate pagination
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var users = await _userRepository.GetAllAsync();
                var paginatedUsers = users
                    .Skip((page - 1) * limit)
                    .Take(limit)
                    .Select(u => u.ToUserResponseDto())
                    .ToList();

                _logger.LogInformation($"Retrieved {paginatedUsers.Count} users");

                return paginatedUsers;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve users");
                throw;
            }
        }

        public async Task<List<LawyerResponseDto>> GetPendingLawyersAsync(int page = 1, int limit = 20)
        {
            try
            {
                _logger.LogInformation($"Admin retrieving pending lawyers, page {page}, limit {limit}");

                // Validate pagination
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var lawyers = await _lawyerRepository.GetPagedAsync(page, limit);
                var pendingLawyers = lawyers
                    .Where(l => !l.IsVerified)
                    .Select(l => l.ToLawyerResponseDto())
                    .ToList();

                _logger.LogInformation($"Retrieved {pendingLawyers.Count} pending lawyers");

                return pendingLawyers;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve pending lawyers");
                throw;
            }
        }

        public async Task VerifyLawyerAsync(int lawyerId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Admin verifying lawyer {lawyerId}");

                var lawyer = await _lawyerRepository.GetByIdAsync(lawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} not found");
                    throw new ArgumentException("Lawyer not found");
                }

                if (lawyer.IsVerified)
                {
                    _logger.LogInformation($"Lawyer {lawyerId} is already verified");
                    return;
                }

                lawyer.IsVerified = true;
                await _lawyerRepository.UpdateAsync(lawyer);

                // Notify lawyer
                var notification = new Notification
                {
                    UserId = lawyer.UserId,
                    Title = "Profile Verified",
                    Message = "Your lawyer profile has been verified and is now visible to clients",
                    Type = "System",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Lawyer {lawyerId} verified successfully by admin");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to verify lawyer {lawyerId}");
                throw;
            }
        }

        public async Task RejectLawyerAsync(int lawyerId, string reason)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Admin rejecting lawyer {lawyerId}");

                var lawyer = await _lawyerRepository.GetByIdAsync(lawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} not found");
                    throw new ArgumentException("Lawyer not found");
                }

                // Validate reason
                if (string.IsNullOrWhiteSpace(reason))
                {
                    _logger.LogWarning("Rejection reason is empty");
                    throw new ArgumentException("Rejection reason cannot be empty");
                }

                // Notify lawyer of rejection
                var notification = new Notification
                {
                    UserId = lawyer.UserId,
                    Title = "Profile Rejected",
                    Message = $"Your lawyer profile was rejected. Reason: {reason}",
                    Type = "System",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Lawyer {lawyerId} rejected by admin. Reason: {reason}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to reject lawyer {lawyerId}");
                throw;
            }
        }

        public async Task SuspendUserAsync(int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Admin suspending user {userId}");

                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                // Check if user is admin
                if (user.Role == "Admin")
                {
                    _logger.LogWarning($"Cannot suspend admin user {userId}");
                    throw new InvalidOperationException("Cannot suspend admin users");
                }

                // TODO: Add IsSuspended field to User model in future
                // For now, we'll just log and notify

                // Notify user
                var notification = new Notification
                {
                    UserId = userId,
                    Title = "Account Suspended",
                    Message = "Your account has been suspended. Please contact support for more information.",
                    Type = "System",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"User {userId} suspended by admin");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to suspend user {userId}");
                throw;
            }
        }

        public async Task UnsuspendUserAsync(int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Admin unsuspending user {userId}");

                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                // TODO: Remove IsSuspended field from User model in future
                // For now, we'll just log and notify

                // Notify user
                var notification = new Notification
                {
                    UserId = userId,
                    Title = "Account Restored",
                    Message = "Your account has been restored. You can now access all features.",
                    Type = "System",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"User {userId} unsuspended by admin");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to unsuspend user {userId}");
                throw;
            }
        }

        public async Task<List<BookingResponseDto>> GetAllBookingsAsync(int page = 1, int limit = 20)
        {
            try
            {
                _logger.LogInformation($"Admin retrieving all bookings, page {page}, limit {limit}");

                // Validate pagination
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var bookings = await _bookingRepository.GetAllAsync();
                var paginatedBookings = bookings
                    .Skip((page - 1) * limit)
                    .Take(limit)
                    .Select(b => b.ToBookingResponseDto())
                    .ToList();

                _logger.LogInformation($"Retrieved {paginatedBookings.Count} bookings");

                return paginatedBookings;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve bookings");
                throw;
            }
        }

        public async Task<List<PaymentSessionResponseDto>> GetAllPaymentsAsync(int page = 1, int limit = 20)
        {
            try
            {
                _logger.LogInformation($"Admin retrieving all payments, page {page}, limit {limit}");

                // Validate pagination
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var payments = await _paymentSessionRepository.GetAllAsync();
                var paginatedPayments = payments
                    .Skip((page - 1) * limit)
                    .Take(limit)
                    .Select(p => p.ToPaymentSessionResponseDto())
                    .ToList();

                _logger.LogInformation($"Retrieved {paginatedPayments.Count} payments");

                return paginatedPayments;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve payments");
                throw;
            }
        }
    }
}
