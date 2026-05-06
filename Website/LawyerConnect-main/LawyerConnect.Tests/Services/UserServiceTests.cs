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
    public class UserServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly Mock<IUserRepository> _userRepositoryMock;
        private readonly Mock<ILogger<UserService>> _loggerMock;
        private readonly UserService _service;

        public UserServiceTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
            _userRepositoryMock = new Mock<IUserRepository>();
            _loggerMock = new Mock<ILogger<UserService>>();

            _service = new UserService(
                _userRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task RegisterUserAsync_ValidInput_CreatesUser()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "test@example.com",
                FullName = "Test User",
                Phone = "1234567890"
            };
            var passwordHash = "hashedPassword123";
            var role = "User";

            _userRepositoryMock.Setup(x => x.GetByEmailAsync(dto.Email)).ReturnsAsync((User?)null);

            // Act
            var result = await _service.RegisterUserAsync(dto, passwordHash, role);

            // Assert
            result.Should().NotBeNull();
            result.Email.Should().Be(dto.Email);
            result.FullName.Should().Be(dto.FullName);
            result.Role.Should().Be(role);

            _userRepositoryMock.Verify(x => x.AddAsync(It.IsAny<User>()), Times.Once);
        }

        [Fact]
        public async Task RegisterUserAsync_EmptyEmail_ThrowsArgumentException()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "",
                FullName = "Test User",
                Phone = "1234567890"
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterUserAsync(dto, "hash", "User"));
        }

        [Fact]
        public async Task RegisterUserAsync_EmptyFullName_ThrowsArgumentException()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "test@example.com",
                FullName = "",
                Phone = "1234567890"
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterUserAsync(dto, "hash", "User"));
        }

        [Fact]
        public async Task RegisterUserAsync_EmptyPasswordHash_ThrowsArgumentException()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "test@example.com",
                FullName = "Test User",
                Phone = "1234567890"
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterUserAsync(dto, "", "User"));
        }

        [Fact]
        public async Task RegisterUserAsync_InvalidRole_ThrowsArgumentException()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "test@example.com",
                FullName = "Test User",
                Phone = "1234567890"
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterUserAsync(dto, "hash", "InvalidRole"));
        }

        [Fact]
        public async Task RegisterUserAsync_DuplicateEmail_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new UserRegisterDto
            {
                Email = "test@example.com",
                FullName = "Test User",
                Phone = "1234567890"
            };

            var existingUser = new User 
            { 
                Id = 1, 
                Email = dto.Email, 
                FullName = "Existing User", 
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByEmailAsync(dto.Email)).ReturnsAsync(existingUser);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => 
                _service.RegisterUserAsync(dto, "hash", "User"));
        }

        [Fact]
        public async Task UpdateUserRoleAsync_ValidInput_UpdatesRole()
        {
            // Arrange
            var userId = 1;
            var newRole = "Lawyer";
            var user = new User 
            { 
                Id = userId, 
                Email = "test@example.com", 
                FullName = "Test User",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);

            // Act
            await _service.UpdateUserRoleAsync(userId, newRole);

            // Assert
            _userRepositoryMock.Verify(x => x.UpdateAsync(It.Is<User>(u => u.Role == newRole)), Times.Once);
        }

        [Fact]
        public async Task UpdateUserRoleAsync_NonExistingUser_ThrowsArgumentException()
        {
            // Arrange
            _userRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((User?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.UpdateUserRoleAsync(999, "Lawyer"));
        }

        [Fact]
        public async Task UpdateUserRoleAsync_InvalidRole_ThrowsArgumentException()
        {
            // Arrange
            var userId = 1;
            var user = new User 
            { 
                Id = userId, 
                Email = "test@example.com", 
                FullName = "Test User",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.UpdateUserRoleAsync(userId, "InvalidRole"));
        }

        [Fact]
        public async Task GetByIdAsync_ExistingUser_ReturnsUser()
        {
            // Arrange
            var userId = 1;
            var user = new User 
            { 
                Id = userId, 
                Email = "test@example.com", 
                FullName = "Test User",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);

            // Act
            var result = await _service.GetByIdAsync(userId);

            // Assert
            result.Should().NotBeNull();
            result!.Id.Should().Be(userId);
            result.Email.Should().Be(user.Email);
        }

        [Fact]
        public async Task GetByIdAsync_NonExistingUser_ReturnsNull()
        {
            // Arrange
            _userRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((User?)null);

            // Act
            var result = await _service.GetByIdAsync(999);

            // Assert
            result.Should().BeNull();
        }

        [Fact]
        public async Task GetPagedAsync_ValidPagination_ReturnsUsers()
        {
            // Arrange
            var users = new List<User>
            {
                new User { Id = 1, Email = "user1@example.com", FullName = "User 1", PasswordHash = "hash", Role = "User", CreatedAt = DateTime.UtcNow },
                new User { Id = 2, Email = "user2@example.com", FullName = "User 2", PasswordHash = "hash", Role = "User", CreatedAt = DateTime.UtcNow }
            };

            _userRepositoryMock.Setup(x => x.GetPagedAsync(1, 20)).ReturnsAsync(users);

            // Act
            var result = await _service.GetPagedAsync(1, 20);

            // Assert
            result.Should().HaveCount(2);
            result.First().Email.Should().Be("user1@example.com");
        }

        [Fact]
        public async Task GetPagedAsync_InvalidPage_ThrowsArgumentException()
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.GetPagedAsync(0, 20));
        }

        [Fact]
        public async Task GetPagedAsync_InvalidLimit_ThrowsArgumentException()
        {
            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.GetPagedAsync(1, 200));
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}

