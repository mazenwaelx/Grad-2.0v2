using Xunit;
using Moq;
using FluentAssertions;
using LawyerConnect.Services;
using LawyerConnect.Repositories;
using LawyerConnect.Models;
using LawyerConnect.DTOs;
using LawyerConnect.Data;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace LawyerConnect.Tests.Services
{
    public class ReviewServiceTests
    {
        private readonly Mock<IBookingRepository> _bookingRepositoryMock;
        private readonly Mock<ILawyerRepository> _lawyerRepositoryMock;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<IReviewRepository> _reviewRepositoryMock;
        private readonly Mock<ILogger<ReviewService>> _loggerMock;
        private readonly LawyerConnectDbContext _context;
        private readonly ReviewService _reviewService;

        public ReviewServiceTests()
        {
            _bookingRepositoryMock = new Mock<IBookingRepository>();
            _lawyerRepositoryMock = new Mock<ILawyerRepository>();
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _reviewRepositoryMock = new Mock<IReviewRepository>();
            _loggerMock = new Mock<ILogger<ReviewService>>();

            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);

            _reviewService = new ReviewService(
                _bookingRepositoryMock.Object,
                _lawyerRepositoryMock.Object,
                _notificationRepositoryMock.Object,
                _reviewRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task CreateReviewAsync_ValidInput_CreatesReview()
        {
            // Arrange
            var userId = 1;
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 2,
                Rating = 5,
                Comment = "Excellent service"
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Completed"
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3,
                AverageRating = 4.0m,
                ReviewsCount = 1
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);
            _reviewRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync((Review?)null);
            _reviewRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Review>())).Returns(Task.CompletedTask);
            _lawyerRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Lawyer>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            var result = await _reviewService.CreateReviewAsync(userId, dto);

            // Assert
            result.Should().NotBeNull();
            result.Rating.Should().Be(5);
            lawyer.AverageRating.Should().Be(4.5m); // (4.0 * 1 + 5) / 2 = 4.5
            lawyer.ReviewsCount.Should().Be(2);
            _reviewRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Review>()), Times.Once);
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Once);
        }

        [Fact]
        public async Task CreateReviewAsync_BookingNotCompleted_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 2,
                Rating = 5
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Pending"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _reviewService.CreateReviewAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Can only review completed bookings");
        }

        [Fact]
        public async Task CreateReviewAsync_WrongUser_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 2,
                Rating = 5
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 2, // Different user
                LawyerId = 2,
                Status = "Completed"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _reviewService.CreateReviewAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<UnauthorizedAccessException>()
                .WithMessage("Can only review your own bookings");
        }

        [Fact]
        public async Task CreateReviewAsync_LawyerMismatch_ThrowsArgumentException()
        {
            // Arrange
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 3, // Different lawyer
                Rating = 5
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Completed"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _reviewService.CreateReviewAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Lawyer ID does not match the booking");
        }

        [Fact]
        public async Task CreateReviewAsync_DuplicateReview_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 2,
                Rating = 5
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Completed"
            };

            var existingReview = new Review
            {
                Id = 1,
                BookingId = 1,
                UserId = 1,
                LawyerId = 2,
                Rating = 4
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _reviewRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(existingReview);

            // Act
            Func<Task> act = async () => await _reviewService.CreateReviewAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Review already exists for this booking");
        }

        [Fact]
        public async Task CreateReviewAsync_InvalidRating_ThrowsArgumentException()
        {
            // Arrange
            var dto = new ReviewCreateDto
            {
                BookingId = 1,
                LawyerId = 2,
                Rating = 6 // Invalid rating
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Completed"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _reviewRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync((Review?)null);

            // Act
            Func<Task> act = async () => await _reviewService.CreateReviewAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Rating must be between 1 and 5");
        }

        [Fact]
        public async Task GetLawyerReviewsAsync_ValidLawyer_ReturnsReviews()
        {
            // Arrange
            var reviews = new List<Review>
            {
                new Review 
                { 
                    Id = 1, 
                    LawyerId = 2, 
                    UserId = 1, 
                    Rating = 5,
                    User = new User { Id = 1, FullName = "User 1" }
                }
            };

            _reviewRepositoryMock.Setup(x => x.GetLawyerReviewsAsync(2, 1, 10)).ReturnsAsync(reviews);

            // Act
            var result = await _reviewService.GetLawyerReviewsAsync(2, 1, 10);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetLawyerAverageRatingAsync_ValidLawyer_ReturnsRating()
        {
            // Arrange
            var lawyer = new Lawyer
            {
                Id = 2,
                AverageRating = 4.5m
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);

            // Act
            var result = await _reviewService.GetLawyerAverageRatingAsync(2);

            // Assert
            result.Should().Be(4.5m);
        }

        [Fact]
        public async Task GetLawyerAverageRatingAsync_LawyerNotFound_ReturnsZero()
        {
            // Arrange
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act
            var result = await _reviewService.GetLawyerAverageRatingAsync(999);

            // Assert
            result.Should().Be(0);
        }

        [Fact]
        public async Task DeleteReviewAsync_ValidAdmin_DeletesReview()
        {
            // Arrange
            var adminUser = new User { Id = 1, FullName = "Admin", Role = "Admin" };
            _context.Users.Add(adminUser);
            await _context.SaveChangesAsync();

            var review = new Review
            {
                Id = 1,
                UserId = 2,
                LawyerId = 3,
                Rating = 5
            };

            var lawyer = new Lawyer
            {
                Id = 3,
                UserId = 4,
                AverageRating = 4.5m,
                ReviewsCount = 2
            };

            _reviewRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(review);
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(3)).ReturnsAsync(lawyer);
            _lawyerRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Lawyer>())).Returns(Task.CompletedTask);
            _reviewRepositoryMock.Setup(x => x.DeleteAsync(It.IsAny<Review>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _reviewService.DeleteReviewAsync(1, 1);

            // Assert
            _reviewRepositoryMock.Verify(x => x.DeleteAsync(It.IsAny<Review>()), Times.Once);
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Exactly(2));
        }

        [Fact]
        public async Task DeleteReviewAsync_NonAdmin_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var regularUser = new User { Id = 1, FullName = "User", Role = "User" };
            _context.Users.Add(regularUser);
            await _context.SaveChangesAsync();

            // Act
            Func<Task> act = async () => await _reviewService.DeleteReviewAsync(1, 1);

            // Assert
            await act.Should().ThrowAsync<UnauthorizedAccessException>()
                .WithMessage("Only administrators can delete reviews");
        }

        [Fact]
        public async Task DeleteReviewAsync_ReviewNotFound_ThrowsArgumentException()
        {
            // Arrange
            var adminUser = new User { Id = 1, FullName = "Admin", Role = "Admin" };
            _context.Users.Add(adminUser);
            await _context.SaveChangesAsync();

            _reviewRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Review?)null);

            // Act
            Func<Task> act = async () => await _reviewService.DeleteReviewAsync(999, 1);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Review not found");
        }
    }
}
