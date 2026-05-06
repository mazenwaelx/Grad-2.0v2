using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace LawyerConnect.Tests.Services
{
    public class NotificationServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<IUserRepository> _userRepositoryMock;
        private readonly Mock<ILogger<NotificationService>> _loggerMock;
        private readonly NotificationService _service;

        public NotificationServiceTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _userRepositoryMock = new Mock<IUserRepository>();
            _loggerMock = new Mock<ILogger<NotificationService>>();

            _service = new NotificationService(
                _notificationRepositoryMock.Object,
                _userRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task CreateNotificationAsync_ValidInput_CreatesNotification()
        {
            // Arrange
            var userId = 1;
            var dto = new NotificationCreateDto
            {
                Title = "Test Notification",
                Message = "Test Message",
                Type = "System"
            };

            var user = new User { Id = userId, FullName = "Test User", Email = "test@example.com" };
            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);

            // Act
            var result = await _service.CreateNotificationAsync(userId, dto);

            // Assert
            result.Should().NotBeNull();
            result.Title.Should().Be(dto.Title);
            result.Message.Should().Be(dto.Message);
            result.Type.Should().Be(dto.Type);
            result.UserId.Should().Be(userId);
            result.IsRead.Should().BeFalse();

            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Once);
        }

        [Fact]
        public async Task CreateNotificationAsync_InvalidType_ThrowsArgumentException()
        {
            // Arrange
            var userId = 1;
            var dto = new NotificationCreateDto
            {
                Title = "Test",
                Message = "Test",
                Type = "InvalidType"
            };

            var user = new User { Id = userId, FullName = "Test User", Email = "test@example.com" };
            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.CreateNotificationAsync(userId, dto));
        }

        [Fact]
        public async Task CreateNotificationAsync_UserNotFound_ThrowsArgumentException()
        {
            // Arrange
            var userId = 999;
            var dto = new NotificationCreateDto
            {
                Title = "Test",
                Message = "Test",
                Type = "System"
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync((User?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.CreateNotificationAsync(userId, dto));
        }

        [Fact]
        public async Task GetUserNotificationsAsync_ValidPagination_ReturnsNotifications()
        {
            // Arrange
            var userId = 1;
            var user = new User { Id = userId, FullName = "Test User", Email = "test@example.com" };
            var notifications = new List<Notification>
            {
                new Notification { Id = 1, UserId = userId, Title = "Test 1", Message = "Message 1", Type = "System", IsRead = false, CreatedAt = DateTime.UtcNow },
                new Notification { Id = 2, UserId = userId, Title = "Test 2", Message = "Message 2", Type = "Booking", IsRead = true, CreatedAt = DateTime.UtcNow }
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);
            _notificationRepositoryMock.Setup(x => x.GetUserNotificationsAsync(userId, 1, 20))
                .ReturnsAsync(notifications);

            // Act
            var result = await _service.GetUserNotificationsAsync(userId, 1, 20);

            // Assert
            result.Should().HaveCount(2);
            result[0].Title.Should().Be("Test 1");
            result[1].Title.Should().Be("Test 2");
        }

        [Fact]
        public async Task GetUserNotificationsAsync_InvalidPage_ThrowsArgumentException()
        {
            // Arrange
            var userId = 1;

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.GetUserNotificationsAsync(userId, 0, 20));
        }

        [Fact]
        public async Task GetUserNotificationsAsync_InvalidLimit_ThrowsArgumentException()
        {
            // Arrange
            var userId = 1;

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.GetUserNotificationsAsync(userId, 1, 200));
        }

        [Fact]
        public async Task MarkAsReadAsync_ValidNotification_MarksAsRead()
        {
            // Arrange
            var notificationId = 1;
            var userId = 1;
            var notification = new Notification 
            { 
                Id = notificationId, 
                UserId = userId, 
                Title = "Test", 
                Message = "Test", 
                Type = "System", 
                IsRead = false,
                CreatedAt = DateTime.UtcNow
            };

            _notificationRepositoryMock.Setup(x => x.GetByIdAsync(notificationId))
                .ReturnsAsync(notification);

            // Act
            await _service.MarkAsReadAsync(notificationId, userId);

            // Assert
            _notificationRepositoryMock.Verify(x => x.UpdateAsync(It.Is<Notification>(n => n.IsRead == true)), Times.Once);
        }

        [Fact]
        public async Task MarkAsReadAsync_WrongUser_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var notificationId = 1;
            var userId = 1;
            var wrongUserId = 2;
            var notification = new Notification 
            { 
                Id = notificationId, 
                UserId = userId, 
                Title = "Test", 
                Message = "Test", 
                Type = "System", 
                IsRead = false,
                CreatedAt = DateTime.UtcNow
            };

            _notificationRepositoryMock.Setup(x => x.GetByIdAsync(notificationId))
                .ReturnsAsync(notification);

            // Act & Assert
            await Assert.ThrowsAsync<UnauthorizedAccessException>(() => 
                _service.MarkAsReadAsync(notificationId, wrongUserId));
        }

        [Fact]
        public async Task GetUnreadCountAsync_ReturnsCorrectCount()
        {
            // Arrange
            var userId = 1;
            var user = new User { Id = userId, FullName = "Test User", Email = "test@example.com" };
            var notifications = new List<Notification>
            {
                new Notification { Id = 1, UserId = userId, IsRead = false, Title = "Test", Message = "Test", Type = "System", CreatedAt = DateTime.UtcNow },
                new Notification { Id = 2, UserId = userId, IsRead = false, Title = "Test", Message = "Test", Type = "System", CreatedAt = DateTime.UtcNow },
                new Notification { Id = 3, UserId = userId, IsRead = true, Title = "Test", Message = "Test", Type = "System", CreatedAt = DateTime.UtcNow }
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);
            _notificationRepositoryMock.Setup(x => x.GetUserNotificationsAsync(userId, 1, 1000))
                .ReturnsAsync(notifications);

            // Act
            var result = await _service.GetUnreadCountAsync(userId);

            // Assert
            result.Should().Be(2);
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}
