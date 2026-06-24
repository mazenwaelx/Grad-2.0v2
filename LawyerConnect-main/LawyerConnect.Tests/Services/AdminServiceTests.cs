using Xunit;
using Moq;
using FluentAssertions;
using LawyerConnect.Services;
using LawyerConnect.Repositories;
using LawyerConnect.Models;
using LawyerConnect.Data;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace LawyerConnect.Tests.Services
{
    public class AdminServiceTests
    {
        private readonly Mock<IUserRepository> _userRepositoryMock;
        private readonly Mock<ILawyerRepository> _lawyerRepositoryMock;
        private readonly Mock<IBookingRepository> _bookingRepositoryMock;
        private readonly Mock<IPaymentSessionRepository> _paymentSessionRepositoryMock;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<ILogger<AdminService>> _loggerMock;
        private readonly LawyerConnectDbContext _context;
        private readonly AdminService _adminService;

        public AdminServiceTests()
        {
            _userRepositoryMock = new Mock<IUserRepository>();
            _lawyerRepositoryMock = new Mock<ILawyerRepository>();
            _bookingRepositoryMock = new Mock<IBookingRepository>();
            _paymentSessionRepositoryMock = new Mock<IPaymentSessionRepository>();
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _loggerMock = new Mock<ILogger<AdminService>>();

            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);

            _adminService = new AdminService(
                _userRepositoryMock.Object,
                _lawyerRepositoryMock.Object,
                _bookingRepositoryMock.Object,
                _paymentSessionRepositoryMock.Object,
                _notificationRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task GetAllUsersAsync_ValidPagination_ReturnsUsers()
        {
            // Arrange
            var users = new List<User>
            {
                new User { Id = 1, FullName = "User 1", Email = "user1@test.com", Role = "User" },
                new User { Id = 2, FullName = "User 2", Email = "user2@test.com", Role = "User" }
            };

            _userRepositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(users);

            // Act
            var result = await _adminService.GetAllUsersAsync(1, 10);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(2);
            result[0].FullName.Should().Be("User 1");
        }

        [Fact]
        public async Task GetAllUsersAsync_InvalidPage_ThrowsArgumentException()
        {
            // Arrange & Act
            Func<Task> act = async () => await _adminService.GetAllUsersAsync(0, 10);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Page number must be greater than 0");
        }

        [Fact]
        public async Task GetAllUsersAsync_InvalidLimit_ThrowsArgumentException()
        {
            // Arrange & Act
            Func<Task> act = async () => await _adminService.GetAllUsersAsync(1, 101);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Limit must be between 1 and 100");
        }

        [Fact]
        public async Task GetPendingLawyersAsync_ValidPagination_ReturnsPendingLawyers()
        {
            // Arrange
            var lawyers = new List<Lawyer>
            {
                new Lawyer 
                { 
                    Id = 1, 
                    UserId = 1, 
                    IsVerified = false,
                    User = new User { Id = 1, FullName = "Lawyer 1", Email = "lawyer1@test.com" }
                },
                new Lawyer 
                { 
                    Id = 2, 
                    UserId = 2, 
                    IsVerified = false,
                    User = new User { Id = 2, FullName = "Lawyer 2", Email = "lawyer2@test.com" }
                }
            };

            _lawyerRepositoryMock.Setup(x => x.GetPagedAsync(1, 20)).ReturnsAsync(lawyers);

            // Act
            var result = await _adminService.GetPendingLawyersAsync(1, 20);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(2);
            result.All(l => !l.IsVerified).Should().BeTrue();
        }

        [Fact]
        public async Task VerifyLawyerAsync_ValidLawyer_VerifiesLawyer()
        {
            // Arrange
            var lawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = 1, 
                IsVerified = false,
                User = new User { Id = 1, FullName = "Lawyer 1" }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(lawyer);
            _lawyerRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<Lawyer>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _adminService.VerifyLawyerAsync(1);

            // Assert
            lawyer.IsVerified.Should().BeTrue();
            _lawyerRepositoryMock.Verify(x => x.UpdateAsync(It.Is<Lawyer>(l => l.IsVerified)), Times.Once);
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.Is<Notification>(n => 
                n.UserId == 1 && n.Title == "Profile Verified")), Times.Once);
        }

        [Fact]
        public async Task VerifyLawyerAsync_LawyerNotFound_ThrowsArgumentException()
        {
            // Arrange
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act
            Func<Task> act = async () => await _adminService.VerifyLawyerAsync(999);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Lawyer not found");
        }

        [Fact]
        public async Task VerifyLawyerAsync_AlreadyVerified_DoesNothing()
        {
            // Arrange
            var lawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = 1, 
                IsVerified = true,
                User = new User { Id = 1, FullName = "Lawyer 1" }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(lawyer);

            // Act
            await _adminService.VerifyLawyerAsync(1);

            // Assert
            _lawyerRepositoryMock.Verify(x => x.UpdateAsync(It.IsAny<Lawyer>()), Times.Never);
        }

        [Fact]
        public async Task RejectLawyerAsync_ValidInput_SendsNotification()
        {
            // Arrange
            var lawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = 1, 
                IsVerified = false,
                User = new User { Id = 1, FullName = "Lawyer 1" }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(lawyer);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _adminService.RejectLawyerAsync(1, "Incomplete documentation");

            // Assert
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.Is<Notification>(n => 
                n.UserId == 1 && 
                n.Title == "Profile Rejected" && 
                n.Message.Contains("Incomplete documentation"))), Times.Once);
        }

        [Fact]
        public async Task RejectLawyerAsync_EmptyReason_ThrowsArgumentException()
        {
            // Arrange
            var lawyer = new Lawyer { Id = 1, UserId = 1, IsVerified = false };
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(lawyer);

            // Act
            Func<Task> act = async () => await _adminService.RejectLawyerAsync(1, "");

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Rejection reason cannot be empty");
        }

        [Fact]
        public async Task SuspendUserAsync_ValidUser_SendsNotification()
        {
            // Arrange
            var user = new User { Id = 1, FullName = "User 1", Email = "user1@test.com", Role = "User" };
            
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            _userRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(user);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);

            // Act
            await _adminService.SuspendUserAsync(1);

            // Assert
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.Is<Notification>(n => 
                n.UserId == 1 && n.Title == "Account Suspended")), Times.Once);
        }

        [Fact]
        public async Task SuspendUserAsync_AdminUser_ThrowsInvalidOperationException()
        {
            // Arrange
            var adminUser = new User { Id = 1, FullName = "Admin", Email = "admin@test.com", Role = "Admin" };
            
            _context.Users.Add(adminUser);
            await _context.SaveChangesAsync();

            _userRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(adminUser);

            // Act
            Func<Task> act = async () => await _adminService.SuspendUserAsync(1);

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot suspend admin users");
        }

        [Fact]
        public async Task GetAllBookingsAsync_ValidPagination_ReturnsBookings()
        {
            // Arrange
            var bookings = new List<Booking>
            {
                new Booking 
                { 
                    Id = 1, 
                    UserId = 1, 
                    LawyerId = 1, 
                    Status = "Confirmed",
                    User = new User { Id = 1, FullName = "User 1" },
                    Lawyer = new Lawyer { Id = 1, UserId = 2, User = new User { Id = 2, FullName = "Lawyer 1" } }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(bookings);

            // Act
            var result = await _adminService.GetAllBookingsAsync(1, 20);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetAllPaymentsAsync_ValidPagination_ReturnsPayments()
        {
            // Arrange
            var payments = new List<PaymentSession>
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

            _paymentSessionRepositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(payments);

            // Act
            var result = await _adminService.GetAllPaymentsAsync(1, 20);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(1);
        }
    }
}
