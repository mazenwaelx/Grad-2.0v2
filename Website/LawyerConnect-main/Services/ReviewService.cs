using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Services
{
    public class ReviewService : IReviewService
    {
        private readonly IBookingRepository _bookingRepository;
        private readonly ILawyerRepository _lawyerRepository;
        private readonly INotificationRepository _notificationRepository;
        private readonly IReviewRepository _reviewRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<ReviewService> _logger;

        public ReviewService(
            IBookingRepository bookingRepository,
            ILawyerRepository lawyerRepository,
            INotificationRepository notificationRepository,
            IReviewRepository reviewRepository,
            LawyerConnectDbContext context,
            ILogger<ReviewService> logger)
        {
            _bookingRepository = bookingRepository;
            _lawyerRepository = lawyerRepository;
            _notificationRepository = notificationRepository;
            _reviewRepository = reviewRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<ReviewResponseDto> CreateReviewAsync(int userId, ReviewCreateDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Creating review for booking {dto.BookingId} by user {userId}");

                // Validate booking exists and is completed
                var booking = await _bookingRepository.GetByIdAsync(dto.BookingId);
                if (booking == null)
                {
                    _logger.LogWarning($"Review creation failed: Booking {dto.BookingId} not found");
                    throw new ArgumentException("Booking not found");
                }

                if (booking.Status != "Completed")
                {
                    _logger.LogWarning($"Review creation failed: Booking {dto.BookingId} status is {booking.Status}, expected Completed");
                    throw new InvalidOperationException("Can only review completed bookings");
                }

                if (booking.UserId != userId)
                {
                    _logger.LogWarning($"Review creation failed: User {userId} attempted to review booking {dto.BookingId} owned by user {booking.UserId}");
                    throw new UnauthorizedAccessException("Can only review your own bookings");
                }

                // Validate lawyer ID matches booking
                if (booking.LawyerId != dto.LawyerId)
                {
                    _logger.LogWarning($"Review creation failed: LawyerId {dto.LawyerId} does not match booking lawyer {booking.LawyerId}");
                    throw new ArgumentException("Lawyer ID does not match the booking");
                }

                // Check if review already exists for this booking
                var existingReview = await _reviewRepository.GetByBookingIdAsync(dto.BookingId);
                if (existingReview != null)
                {
                    _logger.LogWarning($"Review creation failed: Review already exists for booking {dto.BookingId}");
                    throw new InvalidOperationException("Review already exists for this booking");
                }

                // Validate rating range
                if (dto.Rating < 1 || dto.Rating > 5)
                {
                    _logger.LogWarning($"Review creation failed: Invalid rating {dto.Rating}, must be between 1 and 5");
                    throw new ArgumentException("Rating must be between 1 and 5");
                }

                // Create review using mapper
                var review = dto.ToReview(userId);
                await _reviewRepository.AddAsync(review);

                // Update lawyer's average rating and review count
                var lawyer = await _lawyerRepository.GetByIdAsync(dto.LawyerId);
                if (lawyer != null)
                {
                    // Calculate new average rating
                    var newAverageRating = (lawyer.AverageRating * lawyer.ReviewsCount + dto.Rating) / (lawyer.ReviewsCount + 1);
                    lawyer.AverageRating = Math.Round(newAverageRating, 2);
                    lawyer.ReviewsCount++;

                    await _lawyerRepository.UpdateAsync(lawyer);

                    // Create notification for lawyer
                    var notification = new Notification
                    {
                        UserId = lawyer.UserId,
                        Title = "New Review Received",
                        Message = $"You received a {dto.Rating}-star review from a client. Your average rating is now {lawyer.AverageRating:F1} stars.",
                        Type = "Review",
                        IsRead = false,
                        CreatedAt = DateTime.UtcNow
                    };
                    await _notificationRepository.AddAsync(notification);

                    _logger.LogInformation($"Updated lawyer {dto.LawyerId} rating: {lawyer.AverageRating:F2} ({lawyer.ReviewsCount} reviews)");
                }

                await transaction.CommitAsync();

                _logger.LogInformation($"Review {review.Id} created successfully for booking {dto.BookingId}");

                return review.ToReviewResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to create review for booking {dto.BookingId} by user {userId}");
                throw;
            }
        }

        public async Task<List<ReviewResponseDto>> GetLawyerReviewsAsync(int lawyerId, int page = 1, int limit = 10)
        {
            try
            {
                var reviews = await _reviewRepository.GetLawyerReviewsAsync(lawyerId, page, limit);
                return reviews.ToReviewResponseDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get reviews for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task<List<ReviewResponseDto>> GetFeaturedReviewsAsync(int limit = 3)
        {
            try
            {
                _logger.LogInformation($"Retrieving top {limit} featured reviews");

                // Get all reviews with high ratings (4-5 stars) that have comments
                var allReviews = await _context.Reviews
                    .Include(r => r.User)
                    .Include(r => r.Lawyer)
                        .ThenInclude(l => l.User)
                    .Where(r => r.Rating >= 4 && !string.IsNullOrEmpty(r.Comment))
                    .OrderByDescending(r => r.Rating)
                    .ThenByDescending(r => r.CreatedAt)
                    .Take(limit * 3) // Get more to have variety
                    .ToListAsync();

                if (!allReviews.Any())
                {
                    _logger.LogInformation("No featured reviews found");
                    return new List<ReviewResponseDto>();
                }

                // Select diverse reviews (different lawyers if possible)
                var featured = new List<Review>();
                var usedLawyerIds = new HashSet<int>();

                // First pass: Get one review per lawyer
                foreach (var review in allReviews)
                {
                    if (featured.Count >= limit) break;
                    if (!usedLawyerIds.Contains(review.LawyerId))
                    {
                        featured.Add(review);
                        usedLawyerIds.Add(review.LawyerId);
                    }
                }

                // Second pass: Fill remaining slots if needed
                if (featured.Count < limit)
                {
                    foreach (var review in allReviews)
                    {
                        if (featured.Count >= limit) break;
                        if (!featured.Contains(review))
                        {
                            featured.Add(review);
                        }
                    }
                }

                _logger.LogInformation($"Retrieved {featured.Count} featured reviews");
                return featured.Select(r => r.ToReviewResponseDto()).ToList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve featured reviews");
                throw;
            }
        }

        public async Task<decimal> GetLawyerAverageRatingAsync(int lawyerId)
        {
            try
            {
                var lawyer = await _lawyerRepository.GetByIdAsync(lawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} not found when getting average rating");
                    return 0;
                }

                return lawyer.AverageRating;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get average rating for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task DeleteReviewAsync(int id, int adminUserId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                // Validate admin user exists and has admin role
                var adminUser = await _context.Users.FindAsync(adminUserId);
                if (adminUser == null || adminUser.Role != "Admin")
                {
                    _logger.LogWarning($"Review deletion failed: User {adminUserId} is not an admin");
                    throw new UnauthorizedAccessException("Only administrators can delete reviews");
                }

                var review = await _reviewRepository.GetByIdAsync(id);
                if (review == null)
                {
                    _logger.LogWarning($"Review deletion failed: Review {id} not found");
                    throw new ArgumentException("Review not found");
                }

                // Get lawyer before deleting review to update rating
                var lawyer = await _lawyerRepository.GetByIdAsync(review.LawyerId);
                if (lawyer != null && lawyer.ReviewsCount > 0)
                {
                    // Recalculate average rating without this review
                    if (lawyer.ReviewsCount == 1)
                    {
                        // This is the only review, reset to 0
                        lawyer.AverageRating = 0;
                        lawyer.ReviewsCount = 0;
                    }
                    else
                    {
                        // Remove this review from the average
                        var totalRating = lawyer.AverageRating * lawyer.ReviewsCount;
                        var newTotalRating = totalRating - review.Rating;
                        lawyer.ReviewsCount--;
                        lawyer.AverageRating = Math.Round(newTotalRating / lawyer.ReviewsCount, 2);
                    }

                    await _lawyerRepository.UpdateAsync(lawyer);

                    // Create notification for lawyer
                    var lawyerNotification = new Notification
                    {
                        UserId = lawyer.UserId,
                        Title = "Review Removed by Admin",
                        Message = $"A review has been removed by administration. Your average rating is now {lawyer.AverageRating:F1} stars.",
                        Type = "Review",
                        IsRead = false,
                        CreatedAt = DateTime.UtcNow
                    };
                    await _notificationRepository.AddAsync(lawyerNotification);
                }

                // Create notification for the user who wrote the review
                var userNotification = new Notification
                {
                    UserId = review.UserId,
                    Title = "Review Removed",
                    Message = "One of your reviews has been removed by administration for violating community guidelines.",
                    Type = "Review",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(userNotification);

                // Delete the review
                await _reviewRepository.DeleteAsync(review);

                await transaction.CommitAsync();

                _logger.LogInformation($"Review {id} deleted by admin {adminUserId}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to delete review {id} by admin {adminUserId}");
                throw;
            }
        }
    }
}
