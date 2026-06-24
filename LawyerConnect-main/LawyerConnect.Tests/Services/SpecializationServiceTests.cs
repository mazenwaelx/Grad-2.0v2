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
    public class SpecializationServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly Mock<ISpecializationRepository> _repositoryMock;
        private readonly Mock<ILogger<SpecializationService>> _loggerMock;
        private readonly SpecializationService _service;

        public SpecializationServiceTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
            _repositoryMock = new Mock<ISpecializationRepository>();
            _loggerMock = new Mock<ILogger<SpecializationService>>();

            _service = new SpecializationService(
                _repositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task GetAllAsync_ReturnsAllSpecializations()
        {
            // Arrange
            var specializations = new List<Specialization>
            {
                new Specialization { Id = 1, Name = "Corporate Law", Description = "Business law" },
                new Specialization { Id = 2, Name = "Family Law", Description = "Family matters" }
            };

            _repositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(specializations);

            // Act
            var result = await _service.GetAllAsync();

            // Assert
            result.Should().HaveCount(2);
            result[0].Name.Should().Be("Corporate Law");
            result[1].Name.Should().Be("Family Law");
        }

        [Fact]
        public async Task GetByIdAsync_ExistingId_ReturnsSpecialization()
        {
            // Arrange
            var specialization = new Specialization 
            { 
                Id = 1, 
                Name = "Corporate Law", 
                Description = "Business law" 
            };

            _repositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);

            // Act
            var result = await _service.GetByIdAsync(1);

            // Assert
            result.Should().NotBeNull();
            result!.Name.Should().Be("Corporate Law");
        }

        [Fact]
        public async Task GetByIdAsync_NonExistingId_ReturnsNull()
        {
            // Arrange
            _repositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Specialization?)null);

            // Act
            var result = await _service.GetByIdAsync(999);

            // Assert
            result.Should().BeNull();
        }

        [Fact]
        public async Task CreateAsync_ValidInput_CreatesSpecialization()
        {
            // Arrange
            var dto = new SpecializationDto
            {
                Name = "Criminal Law",
                Description = "Criminal defense and prosecution"
            };

            _repositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(new List<Specialization>());

            // Act
            var result = await _service.CreateAsync(dto);

            // Assert
            result.Should().NotBeNull();
            result.Name.Should().Be(dto.Name);
            result.Description.Should().Be(dto.Description);

            _repositoryMock.Verify(x => x.AddAsync(It.IsAny<Specialization>()), Times.Once);
        }

        [Fact]
        public async Task CreateAsync_EmptyName_ThrowsArgumentException()
        {
            // Arrange
            var dto = new SpecializationDto
            {
                Name = "",
                Description = "Test"
            };

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.CreateAsync(dto));
        }

        [Fact]
        public async Task CreateAsync_DuplicateName_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new SpecializationDto
            {
                Name = "Corporate Law",
                Description = "Business law"
            };

            var existingSpecializations = new List<Specialization>
            {
                new Specialization { Id = 1, Name = "Corporate Law", Description = "Existing" }
            };

            _repositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(existingSpecializations);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => _service.CreateAsync(dto));
        }

        [Fact]
        public async Task CreateAsync_DuplicateNameCaseInsensitive_ThrowsInvalidOperationException()
        {
            // Arrange
            var dto = new SpecializationDto
            {
                Name = "CORPORATE LAW",
                Description = "Business law"
            };

            var existingSpecializations = new List<Specialization>
            {
                new Specialization { Id = 1, Name = "corporate law", Description = "Existing" }
            };

            _repositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(existingSpecializations);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => _service.CreateAsync(dto));
        }

        [Fact]
        public async Task UpdateAsync_ValidInput_UpdatesSpecialization()
        {
            // Arrange
            var specializationId = 1;
            var dto = new SpecializationDto
            {
                Name = "Updated Name",
                Description = "Updated Description"
            };

            var existingSpecialization = new Specialization 
            { 
                Id = specializationId, 
                Name = "Old Name", 
                Description = "Old Description" 
            };

            _repositoryMock.Setup(x => x.GetByIdAsync(specializationId)).ReturnsAsync(existingSpecialization);
            _repositoryMock.Setup(x => x.GetAllAsync()).ReturnsAsync(new List<Specialization> { existingSpecialization });

            // Act
            await _service.UpdateAsync(specializationId, dto);

            // Assert
            _repositoryMock.Verify(x => x.UpdateAsync(It.Is<Specialization>(s => 
                s.Name == dto.Name && s.Description == dto.Description)), Times.Once);
        }

        [Fact]
        public async Task UpdateAsync_NonExistingId_ThrowsArgumentException()
        {
            // Arrange
            var dto = new SpecializationDto
            {
                Name = "Test",
                Description = "Test"
            };

            _repositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Specialization?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.UpdateAsync(999, dto));
        }

        [Fact]
        public async Task DeleteAsync_NoAssignedLawyers_DeletesSpecialization()
        {
            // Arrange
            var specializationId = 1;
            var specialization = new Specialization 
            { 
                Id = specializationId, 
                Name = "Test", 
                Description = "Test",
                Lawyers = new List<LawyerSpecialization>() // Empty list
            };

            _repositoryMock.Setup(x => x.GetByIdAsync(specializationId)).ReturnsAsync(specialization);

            // Act
            await _service.DeleteAsync(specializationId);

            // Assert
            _repositoryMock.Verify(x => x.DeleteAsync(specializationId), Times.Once);
        }

        [Fact]
        public async Task DeleteAsync_WithAssignedLawyers_ThrowsInvalidOperationException()
        {
            // Arrange
            var specializationId = 1;
            var specialization = new Specialization 
            { 
                Id = specializationId, 
                Name = "Test", 
                Description = "Test",
                Lawyers = new List<LawyerSpecialization>
                {
                    new LawyerSpecialization { LawyerId = 1, SpecializationId = specializationId }
                }
            };

            _repositoryMock.Setup(x => x.GetByIdAsync(specializationId)).ReturnsAsync(specialization);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => _service.DeleteAsync(specializationId));
        }

        [Fact]
        public async Task DeleteAsync_NonExistingId_ThrowsArgumentException()
        {
            // Arrange
            _repositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Specialization?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.DeleteAsync(999));
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}
