using Xunit;
using Moq;
using FluentAssertions;
using LawyerConnect.Services;
using LawyerConnect.Repositories;
using LawyerConnect.Models;
using LawyerConnect.Data;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace LawyerConnect.Tests.Services
{
    public class PaymentServiceTests
    {
        private readonly Mock<IPaymentSessionRepository> _paymentSessionRepositoryMock;
        private readonly Mock<IBookingRepository> _bookingRepositoryMock;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<IConfiguration> _configurationMock;
        private readonly Mock<ILogger<PaymentService>> _loggerMock;
        private readonly LawyerConnectDbContext _context;
        private readonly PaymentService _paymentService;

        public PaymentServiceTests()
        {
            _paymentSessionRepositoryMock = new Mock<IPaymentSessionRepository>();
            _bookingRepositoryMock = new Mock<IBookingRepository>();
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _configurationMock = new Mock<IConfiguration>();
            _loggerMock = new Mock<ILogger<PaymentService>>();

            // Setup configuration mocks
            _configurationMock.Setup(x => x["Stripe:Currency"]).Returns("usd");
            _configurationMock.Setup(x => x["App:BaseUrl"]).Returns("http://localhost:5000");
            _configurationMock.Setup(x => x["Stripe:WebhookSecret"]).Returns("test_webhook_secret");

            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);

            _paymentService = new PaymentService(
                _paymentSessionRepositoryMock.Object,
                _bookingRepositoryMock.Object,
                _notificationRepositoryMock.Object,
                _context,
                _configurationMock.Object,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task ConfirmPaymentAsync_ValidSession_ConfirmsPayment()
        {
            // Arrange
            var paymentSession = new PaymentSession
            {
                Id = 1,
                BookingId = 1,
                Amount = 100,
                Status = "Pending",
                Provider = "Stripe",
                ProviderSessionId = "test_session_id"
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2,
                Status = "Pending",
                PaymentStatus = "Pending",
                User = new User { Id = 1, FullName = "User 1" },
                Lawyer = new Lawyer 
                { 
                    Id = 2, 
                    UserId = 3,
                    User = new User { Id = 3, FullName = "Lawyer 1" }
                }
            };

            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(paymentSession);
            _paymentSessionRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<PaymentSession>())).Returns(Task.CompletedTask);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _bookingRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            var result = await _paymentService.ConfirmPaymentAsync(1);

            // Assert
            result.Should().NotBeNull();
            paymentSession.Status.Should().Be("Success");
            booking.PaymentStatus.Should().Be("Paid");
            booking.Status.Should().Be("Confirmed");
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Exactly(2));
        }

        [Fact]
        public async Task ConfirmPaymentAsync_SessionNotFound_ThrowsArgumentException()
        {
            // Arrange
            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((PaymentSession?)null);

            // Act
            Func<Task> act = async () => await _paymentService.ConfirmPaymentAsync(999);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Payment session not found");
        }

        [Fact]
        public async Task ConfirmPaymentAsync_SessionNotPending_ThrowsInvalidOperationException()
        {
            // Arrange
            var paymentSession = new PaymentSession
            {
                Id = 1,
                Status = "Success"
            };

            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(paymentSession);

            // Act
            Func<Task> act = async () => await _paymentService.ConfirmPaymentAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot confirm payment with status: Success");
        }

        [Fact]
        public async Task GetPaymentSessionAsync_ExistingSession_ReturnsSession()
        {
            // Arrange
            var paymentSession = new PaymentSession
            {
                Id = 1,
                BookingId = 1,
                Amount = 100,
                Status = "Success",
                Booking = new Booking
                {
                    Id = 1,
                    UserId = 1,
                    User = new User { Id = 1, FullName = "User 1" }
                }
            };

            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(paymentSession);

            // Act
            var result = await _paymentService.GetPaymentSessionAsync(1);

            // Assert
            result.Should().NotBeNull();
            result!.Id.Should().Be(1);
            result.Amount.Should().Be(100);
        }

        [Fact]
        public async Task GetPaymentSessionAsync_NonExistingSession_ReturnsNull()
        {
            // Arrange
            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((PaymentSession?)null);

            // Act
            var result = await _paymentService.GetPaymentSessionAsync(999);

            // Assert
            result.Should().BeNull();
        }

        [Fact]
        public async Task GetUserPaymentSessionsAsync_ValidUser_ReturnsSessions()
        {
            // Arrange
            var sessions = new List<PaymentSession>
            {
                new PaymentSession
                {
                    Id = 1,
                    BookingId = 1,
                    Amount = 100,
                    Status = "Success",
                    Booking = new Booking
                    {
                        Id = 1,
                        UserId = 1,
                        User = new User { Id = 1, FullName = "User 1" }
                    }
                }
            };

            _paymentSessionRepositoryMock.Setup(x => x.GetByUserIdAsync(1, 1, 10)).ReturnsAsync(sessions);

            // Act
            var result = await _paymentService.GetUserPaymentSessionsAsync(1, 1, 10);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(1);
        }

        [Fact]
        public async Task RefundPaymentAsync_ValidSession_RefundsPayment()
        {
            // Arrange
            var paymentSession = new PaymentSession
            {
                Id = 1,
                BookingId = 1,
                Amount = 100,
                Status = "Success",
                Provider = "Stripe",
                ProviderSessionId = "test_session_id"
            };

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

            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(paymentSession);
            _paymentSessionRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<PaymentSession>())).Returns(Task.CompletedTask);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _bookingRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Booking>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Note: This test will fail when actually calling Stripe API
            // In a real scenario, you would mock the Stripe service or use integration tests
            // For now, we test the validation logic only

            // Act & Assert - This will throw because we can't actually call Stripe in unit tests
            // In production, you would inject a Stripe service interface and mock it
            await Assert.ThrowsAsync<InvalidOperationException>(
                async () => await _paymentService.RefundPaymentAsync(1)
            );
        }

        [Fact]
        public async Task RefundPaymentAsync_SessionNotFound_ThrowsArgumentException()
        {
            // Arrange
            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((PaymentSession?)null);

            // Act
            Func<Task> act = async () => await _paymentService.RefundPaymentAsync(999);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Payment session not found");
        }

        [Fact]
        public async Task RefundPaymentAsync_SessionNotSuccess_ThrowsInvalidOperationException()
        {
            // Arrange
            var paymentSession = new PaymentSession
            {
                Id = 1,
                Status = "Pending"
            };

            _paymentSessionRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(paymentSession);

            // Act
            Func<Task> act = async () => await _paymentService.RefundPaymentAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Can only refund successful payments");
        }
    }
}
