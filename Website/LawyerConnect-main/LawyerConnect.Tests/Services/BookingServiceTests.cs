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
    public class BookingServiceTests
    {
        private readonly Mock<IBookingRepository> _bookingRepositoryMock;
        private readonly Mock<ILawyerRepository> _lawyerRepositoryMock;
        private readonly Mock<IPricingRepository> _pricingRepositoryMock;
        private readonly Mock<IChatRoomRepository> _chatRoomRepositoryMock;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<ILogger<BookingService>> _loggerMock;
        private readonly LawyerConnectDbContext _context;
        private readonly BookingService _bookingService;

        public BookingServiceTests()
        {
            _bookingRepositoryMock = new Mock<IBookingRepository>();
            _lawyerRepositoryMock = new Mock<ILawyerRepository>();
            _pricingRepositoryMock = new Mock<IPricingRepository>();
            _chatRoomRepositoryMock = new Mock<IChatRoomRepository>();
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _loggerMock = new Mock<ILogger<BookingService>>();

            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);

            _bookingService = new BookingService(
                _bookingRepositoryMock.Object,
                _lawyerRepositoryMock.Object,
                _pricingRepositoryMock.Object,
                _chatRoomRepositoryMock.Object,
                _notificationRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task CreateBookingAsync_ValidInput_CreatesBooking()
        {
            // Arrange
            var userId = 1;
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddDays(2)
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3,
                IsVerified = true,
                User = new User { Id = 3, FullName = "Lawyer 1" }
            };

            var pricing = new LawyerPricing
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 100,
                DurationMinutes = 60
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(2, 1, 1)).ReturnsAsync(pricing);
            _bookingRepositoryMock.Setup(x => x.GetLawyerBookingsForDateAsync(2, dto.Date, 60))
                .ReturnsAsync(new List<Booking>());
            _bookingRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _chatRoomRepositoryMock.Setup(x => x.AddAsync(It.IsAny<ChatRoom>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            var result = await _bookingService.CreateBookingAsync(userId, dto);

            // Assert
            result.Should().NotBeNull();
            _bookingRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Booking>()), Times.Once);
            _chatRoomRepositoryMock.Verify(x => x.AddAsync(It.IsAny<ChatRoom>()), Times.Once);
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Exactly(2));
        }

        [Fact]
        public async Task CreateBookingAsync_PastDate_ThrowsArgumentException()
        {
            // Arrange
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddMinutes(-30)
            };

            // Act
            Func<Task> act = async () => await _bookingService.CreateBookingAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Booking date must be at least 1 hour in the future");
        }

        [Fact]
        public async Task CreateBookingAsync_UnverifiedLawyer_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddDays(2)
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3,
                IsVerified = false
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);

            // Act
            Func<Task> act = async () => await _bookingService.CreateBookingAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot book with unverified lawyer");
        }

        [Fact]
        public async Task CreateBookingAsync_UserBooksSelf_ThrowsInvalidOperationException()
        {
            // Arrange
            var userId = 1;
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddDays(2)
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 1, // Same as booking user
                IsVerified = true
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);

            // Act
            Func<Task> act = async () => await _bookingService.CreateBookingAsync(userId, dto);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot book a consultation with yourself");
        }

        [Fact]
        public async Task CreateBookingAsync_NoPricing_ThrowsArgumentException()
        {
            // Arrange
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddDays(2)
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3,
                IsVerified = true
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(2, 1, 1)).ReturnsAsync((LawyerPricing?)null);

            // Act
            Func<Task> act = async () => await _bookingService.CreateBookingAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Pricing not available for this specialization and interaction type");
        }

        [Fact]
        public async Task CreateBookingAsync_ConflictingBooking_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow.AddDays(2)
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3,
                IsVerified = true
            };

            var pricing = new LawyerPricing
            {
                LawyerId = 2,
                Price = 100,
                DurationMinutes = 60
            };

            var conflictingBooking = new Booking
            {
                Id = 1,
                LawyerId = 2,
                Status = "Confirmed",
                Date = dto.Date
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(2)).ReturnsAsync(lawyer);
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(2, 1, 1)).ReturnsAsync(pricing);
            _bookingRepositoryMock.Setup(x => x.GetLawyerBookingsForDateAsync(2, dto.Date, 60))
                .ReturnsAsync(new List<Booking> { conflictingBooking });

            // Act
            Func<Task> act = async () => await _bookingService.CreateBookingAsync(1, dto);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("This time slot is not available");
        }

        [Fact]
        public async Task GetBookingByIdAsync_ExistingBooking_ReturnsBooking()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Pending",
                User = new User { Id = 1, FullName = "User 1" },
                Lawyer = new Lawyer 
                { 
                    Id = 2, 
                    UserId = 3,
                    User = new User { Id = 3, FullName = "Lawyer 1" }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            var result = await _bookingService.GetBookingByIdAsync(1);

            // Assert
            result.Should().NotBeNull();
            result!.Id.Should().Be(1);
        }

        [Fact]
        public async Task UpdateBookingStatusAsync_ValidTransition_UpdatesStatus()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Pending",
                User = new User { Id = 1, FullName = "User 1" },
                Lawyer = new Lawyer 
                { 
                    Id = 2, 
                    UserId = 3,
                    User = new User { Id = 3, FullName = "Lawyer 1" }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _bookingRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _bookingService.UpdateBookingStatusAsync(1, "Confirmed");

            // Assert
            booking.Status.Should().Be("Confirmed");
            _bookingRepositoryMock.Verify(x => x.UpdateAsync(It.IsAny<Booking>()), Times.Once);
        }

        [Fact]
        public async Task UpdateBookingStatusAsync_InvalidTransition_ThrowsInvalidOperationException()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                Status = "Completed"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _bookingService.UpdateBookingStatusAsync(1, "Pending");

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>();
        }

        [Fact]
        public async Task CancelBookingAsync_ValidBooking_CancelsBooking()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Pending",
                Date = DateTime.UtcNow.AddDays(2),
                User = new User { Id = 1, FullName = "User 1" },
                Lawyer = new Lawyer 
                { 
                    Id = 2, 
                    UserId = 3,
                    User = new User { Id = 3, FullName = "Lawyer 1" }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _bookingRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _bookingService.CancelBookingAsync(1);

            // Assert
            booking.Status.Should().Be("Cancelled");
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Exactly(2));
        }

        [Fact]
        public async Task CancelBookingAsync_AlreadyCancelled_ThrowsInvalidOperationException()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                Status = "Cancelled"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _bookingService.CancelBookingAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot cancel booking that is Cancelled");
        }

        [Fact]
        public async Task CompleteBookingAsync_ValidBooking_CompletesBooking()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Confirmed",
                PaymentStatus = "Paid",
                User = new User { Id = 1, FullName = "User 1" },
                Lawyer = new Lawyer 
                { 
                    Id = 2, 
                    UserId = 3,
                    User = new User { Id = 3, FullName = "Lawyer 1" }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _bookingRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _bookingService.CompleteBookingAsync(1);

            // Assert
            booking.Status.Should().Be("Completed");
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Exactly(2));
        }

        [Fact]
        public async Task CompleteBookingAsync_NotConfirmed_ThrowsInvalidOperationException()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                Status = "Pending"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _bookingService.CompleteBookingAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Only confirmed bookings can be completed");
        }

        [Fact]
        public async Task CompleteBookingAsync_NotPaid_ThrowsInvalidOperationException()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                Status = "Confirmed",
                PaymentStatus = "Pending"
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);

            // Act
            Func<Task> act = async () => await _bookingService.CompleteBookingAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot complete booking without payment");
        }
    }
}
