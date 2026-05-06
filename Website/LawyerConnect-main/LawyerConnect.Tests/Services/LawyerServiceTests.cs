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
    public class LawyerServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly Mock<ILawyerRepository> _lawyerRepositoryMock;
        private readonly Mock<IUserRepository> _userRepositoryMock;
        private readonly Mock<ISpecializationRepository> _specializationRepositoryMock;
        private readonly Mock<ILogger<LawyerService>> _loggerMock;
        private readonly LawyerService _service;

        public LawyerServiceTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
            _lawyerRepositoryMock = new Mock<ILawyerRepository>();
            _userRepositoryMock = new Mock<IUserRepository>();
            _specializationRepositoryMock = new Mock<ISpecializationRepository>();
            _loggerMock = new Mock<ILogger<LawyerService>>();

            _service = new LawyerService(
                _lawyerRepositoryMock.Object,
                _userRepositoryMock.Object,
                _specializationRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task RegisterLawyerAsync_ValidInput_CreatesLawyer()
        {
            // Arrange
            var userId = 1;
            var dto = new LawyerRegisterDto
            {
                ExperienceYears = 5,
                Address = "123 Main St",
                Latitude = 40.7128m,
                Longitude = -74.0060m,
                SpecializationIds = new List<int> { 1 }
            };

            var user = new User 
            { 
                Id = userId, 
                Email = "lawyer@example.com", 
                FullName = "Test Lawyer",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            var specialization = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };
            var createdLawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = userId, 
                ExperienceYears = dto.ExperienceYears,
                Address = dto.Address,
                Latitude = dto.Latitude,
                Longitude = dto.Longitude,
                IsVerified = false,
                CreatedAt = DateTime.UtcNow,
                User = user
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);
            _lawyerRepositoryMock.Setup(x => x.GetByUserIdAsync(userId)).ReturnsAsync((Lawyer?)null);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(It.IsAny<int>())).ReturnsAsync(createdLawyer);

            // Act
            var result = await _service.RegisterLawyerAsync(dto, userId);

            // Assert
            result.Should().NotBeNull();
            result.ExperienceYears.Should().Be(dto.ExperienceYears);
            result.Address.Should().Be(dto.Address);

            _lawyerRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Lawyer>()), Times.Once);
            _userRepositoryMock.Verify(x => x.UpdateAsync(It.Is<User>(u => u.Role == "Lawyer")), Times.Once);
        }

        [Fact]
        public async Task RegisterLawyerAsync_NonExistingUser_ThrowsArgumentException()
        {
            // Arrange
            var dto = new LawyerRegisterDto
            {
                ExperienceYears = 5,
                Address = "123 Main St",
                Latitude = 40.7128m,
                Longitude = -74.0060m,
                SpecializationIds = new List<int>()
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((User?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterLawyerAsync(dto, 999));
        }

        [Fact]
        public async Task RegisterLawyerAsync_ExistingLawyerProfile_ThrowsInvalidOperationException()
        {
            // Arrange
            var userId = 1;
            var dto = new LawyerRegisterDto
            {
                ExperienceYears = 5,
                Address = "123 Main St",
                Latitude = 40.7128m,
                Longitude = -74.0060m,
                SpecializationIds = new List<int>()
            };

            var user = new User 
            { 
                Id = userId, 
                Email = "lawyer@example.com", 
                FullName = "Test Lawyer",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            var existingLawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = userId, 
                ExperienceYears = 3,
                Address = "Old Address",
                IsVerified = false,
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);
            _lawyerRepositoryMock.Setup(x => x.GetByUserIdAsync(userId)).ReturnsAsync(existingLawyer);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => 
                _service.RegisterLawyerAsync(dto, userId));
        }

        [Fact]
        public async Task RegisterLawyerAsync_InvalidSpecialization_ThrowsArgumentException()
        {
            // Arrange
            var userId = 1;
            var dto = new LawyerRegisterDto
            {
                ExperienceYears = 5,
                Address = "123 Main St",
                Latitude = 40.7128m,
                Longitude = -74.0060m,
                SpecializationIds = new List<int> { 999 }
            };

            var user = new User 
            { 
                Id = userId, 
                Email = "lawyer@example.com", 
                FullName = "Test Lawyer",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            _userRepositoryMock.Setup(x => x.GetByIdAsync(userId)).ReturnsAsync(user);
            _lawyerRepositoryMock.Setup(x => x.GetByUserIdAsync(userId)).ReturnsAsync((Lawyer?)null);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Specialization?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.RegisterLawyerAsync(dto, userId));
        }

        [Fact]
        public async Task GetByIdAsync_ExistingLawyer_ReturnsLawyer()
        {
            // Arrange
            var lawyerId = 1;
            var lawyer = new Lawyer 
            { 
                Id = lawyerId, 
                UserId = 1, 
                ExperienceYears = 5,
                Address = "123 Main St",
                IsVerified = true,
                CreatedAt = DateTime.UtcNow,
                User = new User 
                { 
                    Id = 1, 
                    Email = "lawyer@example.com", 
                    FullName = "Test Lawyer",
                    PasswordHash = "hash",
                    Role = "Lawyer",
                    CreatedAt = DateTime.UtcNow
                }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);

            // Act
            var result = await _service.GetByIdAsync(lawyerId);

            // Assert
            result.Should().NotBeNull();
            result!.Id.Should().Be(lawyerId);
            result.ExperienceYears.Should().Be(5);
        }

        [Fact]
        public async Task GetByIdAsync_NonExistingLawyer_ReturnsNull()
        {
            // Arrange
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act
            var result = await _service.GetByIdAsync(999);

            // Assert
            result.Should().BeNull();
        }

        [Fact]
        public async Task GetByUserIdAsync_ExistingLawyer_ReturnsLawyer()
        {
            // Arrange
            var userId = 1;
            var lawyer = new Lawyer 
            { 
                Id = 1, 
                UserId = userId, 
                ExperienceYears = 5,
                Address = "123 Main St",
                IsVerified = true,
                CreatedAt = DateTime.UtcNow,
                User = new User 
                { 
                    Id = userId, 
                    Email = "lawyer@example.com", 
                    FullName = "Test Lawyer",
                    PasswordHash = "hash",
                    Role = "Lawyer",
                    CreatedAt = DateTime.UtcNow
                }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByUserIdAsync(userId)).ReturnsAsync(lawyer);

            // Act
            var result = await _service.GetByUserIdAsync(userId);

            // Assert
            result.Should().NotBeNull();
            result!.UserId.Should().Be(userId);
        }

        [Fact]
        public async Task GetPagedAsync_ValidPagination_ReturnsLawyers()
        {
            // Arrange
            var lawyers = new List<Lawyer>
            {
                new Lawyer 
                { 
                    Id = 1, 
                    UserId = 1, 
                    ExperienceYears = 5,
                    Address = "Address 1",
                    IsVerified = true,
                    CreatedAt = DateTime.UtcNow,
                    User = new User { Id = 1, Email = "lawyer1@example.com", FullName = "Lawyer 1", PasswordHash = "hash", Role = "Lawyer", CreatedAt = DateTime.UtcNow }
                },
                new Lawyer 
                { 
                    Id = 2, 
                    UserId = 2, 
                    ExperienceYears = 10,
                    Address = "Address 2",
                    IsVerified = true,
                    CreatedAt = DateTime.UtcNow,
                    User = new User { Id = 2, Email = "lawyer2@example.com", FullName = "Lawyer 2", PasswordHash = "hash", Role = "Lawyer", CreatedAt = DateTime.UtcNow }
                }
            };

            _lawyerRepositoryMock.Setup(x => x.GetPagedAsync(1, 20)).ReturnsAsync(lawyers);

            // Act
            var result = await _service.GetPagedAsync(1, 20);

            // Assert
            result.Should().HaveCount(2);
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

        [Fact]
        public async Task VerifyLawyerAsync_ValidLawyer_VerifiesLawyer()
        {
            // Arrange
            var lawyerId = 1;
            var lawyer = new Lawyer 
            { 
                Id = lawyerId, 
                UserId = 1, 
                ExperienceYears = 5,
                Address = "123 Main St",
                IsVerified = false,
                CreatedAt = DateTime.UtcNow
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);

            // Act
            await _service.VerifyLawyerAsync(lawyerId);

            // Assert
            _lawyerRepositoryMock.Verify(x => x.UpdateAsync(It.Is<Lawyer>(l => l.IsVerified == true)), Times.Once);
        }

        [Fact]
        public async Task VerifyLawyerAsync_NonExistingLawyer_ThrowsArgumentException()
        {
            // Arrange
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.VerifyLawyerAsync(999));
        }

        [Fact]
        public async Task SearchLawyersAsync_ValidFilters_ReturnsFilteredLawyers()
        {
            // Arrange
            var filters = new LawyerSearchDto
            {
                Page = 1,
                Limit = 20,
                SpecializationId = 1,
                MinExperienceYears = 3
            };

            var specialization1 = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };
            var specialization2 = new Specialization { Id = 2, Name = "Family Law", Description = "Test" };

            var lawyers = new List<Lawyer>
            {
                new Lawyer 
                { 
                    Id = 1, 
                    UserId = 1, 
                    ExperienceYears = 5,
                    Address = "Address 1",
                    IsVerified = true,
                    CreatedAt = DateTime.UtcNow,
                    User = new User { Id = 1, Email = "lawyer1@example.com", FullName = "Lawyer 1", PasswordHash = "hash", Role = "Lawyer", CreatedAt = DateTime.UtcNow },
                    Specializations = new List<LawyerSpecialization>
                    {
                        new LawyerSpecialization { LawyerId = 1, SpecializationId = 1, Specialization = specialization1 }
                    }
                },
                new Lawyer 
                { 
                    Id = 2, 
                    UserId = 2, 
                    ExperienceYears = 2,
                    Address = "Address 2",
                    IsVerified = true,
                    CreatedAt = DateTime.UtcNow,
                    User = new User { Id = 2, Email = "lawyer2@example.com", FullName = "Lawyer 2", PasswordHash = "hash", Role = "Lawyer", CreatedAt = DateTime.UtcNow },
                    Specializations = new List<LawyerSpecialization>
                    {
                        new LawyerSpecialization { LawyerId = 2, SpecializationId = 2, Specialization = specialization2 }
                    }
                }
            };

            _lawyerRepositoryMock.Setup(x => x.GetPagedAsync(1, 20)).ReturnsAsync(lawyers);

            // Act
            var result = await _service.SearchLawyersAsync(filters);

            // Assert
            result.Should().HaveCount(1); // Only lawyer 1 matches (verified, specialization 1, experience >= 3)
            result[0].ExperienceYears.Should().Be(5);
        }

        [Fact]
        public async Task SearchLawyersAsync_InvalidPage_ThrowsArgumentException()
        {
            // Arrange
            var filters = new LawyerSearchDto
            {
                Page = 0,
                Limit = 20
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.SearchLawyersAsync(filters));
        }

        [Fact]
        public async Task SearchLawyersAsync_InvalidLimit_ThrowsArgumentException()
        {
            // Arrange
            var filters = new LawyerSearchDto
            {
                Page = 1,
                Limit = 200
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => 
                _service.SearchLawyersAsync(filters));
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}
