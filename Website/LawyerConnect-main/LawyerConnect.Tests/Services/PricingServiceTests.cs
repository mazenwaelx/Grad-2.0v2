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
    public class PricingServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly Mock<IPricingRepository> _pricingRepositoryMock;
        private readonly Mock<ILawyerRepository> _lawyerRepositoryMock;
        private readonly Mock<ISpecializationRepository> _specializationRepositoryMock;
        private readonly Mock<ILogger<PricingService>> _loggerMock;
        private readonly PricingService _service;

        public PricingServiceTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
            _pricingRepositoryMock = new Mock<IPricingRepository>();
            _lawyerRepositoryMock = new Mock<ILawyerRepository>();
            _specializationRepositoryMock = new Mock<ISpecializationRepository>();
            _loggerMock = new Mock<ILogger<PricingService>>();

            _service = new PricingService(
                _pricingRepositoryMock.Object,
                _lawyerRepositoryMock.Object,
                _specializationRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task GetPricingAsync_ExistingPricing_ReturnsPricing()
        {
            // Arrange
            var lawyerId = 1;
            var specializationId = 1;
            var interactionTypeId = 1;
            var pricing = new LawyerPricing
            {
                LawyerId = lawyerId,
                SpecializationId = specializationId,
                InteractionTypeId = interactionTypeId,
                Price = 500.00m,
                DurationMinutes = 60
            };

            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(lawyerId, specializationId, interactionTypeId))
                .ReturnsAsync(pricing);

            // Act
            var result = await _service.GetPricingAsync(lawyerId, specializationId, interactionTypeId);

            // Assert
            result.Should().NotBeNull();
            result!.Price.Should().Be(500.00m);
            result.DurationMinutes.Should().Be(60);
        }

        [Fact]
        public async Task GetPricingAsync_NonExistingPricing_ReturnsNull()
        {
            // Arrange
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(999, 999, 999))
                .ReturnsAsync((LawyerPricing?)null);

            // Act
            var result = await _service.GetPricingAsync(999, 999, 999);

            // Assert
            result.Should().BeNull();
        }

        [Fact]
        public async Task GetLawyerPricingAsync_ValidLawyer_ReturnsPricingList()
        {
            // Arrange
            var lawyerId = 1;
            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };
            var pricings = new List<LawyerPricing>
            {
                new LawyerPricing { LawyerId = lawyerId, SpecializationId = 1, InteractionTypeId = 1, Price = 500, DurationMinutes = 60 },
                new LawyerPricing { LawyerId = lawyerId, SpecializationId = 1, InteractionTypeId = 2, Price = 5000, DurationMinutes = 0 }
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _pricingRepositoryMock.Setup(x => x.GetLawyerPricingAsync(lawyerId)).ReturnsAsync(pricings);

            // Act
            var result = await _service.GetLawyerPricingAsync(lawyerId);

            // Assert
            result.Should().HaveCount(2);
            result[0].Price.Should().Be(500);
            result[1].Price.Should().Be(5000);
        }

        [Fact]
        public async Task GetLawyerPricingAsync_NonExistingLawyer_ThrowsArgumentException()
        {
            // Arrange
            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.GetLawyerPricingAsync(999));
        }

        [Fact]
        public async Task SetPricingAsync_ValidInput_CreatesPricing()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 600.00m,
                DurationMinutes = 60
            };

            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };
            var specialization = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(lawyerId, 1, 1)).ReturnsAsync((LawyerPricing?)null);

            // Act
            await _service.SetPricingAsync(lawyerId, dto);

            // Assert
            _pricingRepositoryMock.Verify(x => x.AddAsync(It.Is<LawyerPricing>(p => 
                p.Price == 600.00m && p.DurationMinutes == 60)), Times.Once);
        }

        [Fact]
        public async Task SetPricingAsync_NegativePrice_ThrowsArgumentException()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = -100.00m,
                DurationMinutes = 60
            };

            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };
            var specialization = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.SetPricingAsync(lawyerId, dto));
        }

        [Fact]
        public async Task SetPricingAsync_ZeroDuration_ThrowsArgumentException()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 500.00m,
                DurationMinutes = 0
            };

            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };
            var specialization = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.SetPricingAsync(lawyerId, dto));
        }

        [Fact]
        public async Task SetPricingAsync_DuplicatePricing_ThrowsInvalidOperationException()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 500.00m,
                DurationMinutes = 60
            };

            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };
            var specialization = new Specialization { Id = 1, Name = "Corporate Law", Description = "Test" };
            var existingPricing = new LawyerPricing { LawyerId = lawyerId, SpecializationId = 1, InteractionTypeId = 1, Price = 400, DurationMinutes = 60 };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(specialization);
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(lawyerId, 1, 1)).ReturnsAsync(existingPricing);

            // Act & Assert
            await Assert.ThrowsAsync<InvalidOperationException>(() => _service.SetPricingAsync(lawyerId, dto));
        }

        [Fact]
        public async Task SetPricingAsync_NonExistingLawyer_ThrowsArgumentException()
        {
            // Arrange
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 500.00m,
                DurationMinutes = 60
            };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Lawyer?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.SetPricingAsync(999, dto));
        }

        [Fact]
        public async Task SetPricingAsync_NonExistingSpecialization_ThrowsArgumentException()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 999,
                InteractionTypeId = 1,
                Price = 500.00m,
                DurationMinutes = 60
            };

            var lawyer = new Lawyer { Id = lawyerId, UserId = 1, ExperienceYears = 5, IsVerified = true, Address = "Test Address" };

            _lawyerRepositoryMock.Setup(x => x.GetByIdAsync(lawyerId)).ReturnsAsync(lawyer);
            _specializationRepositoryMock.Setup(x => x.GetByIdAsync(999)).ReturnsAsync((Specialization?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.SetPricingAsync(lawyerId, dto));
        }

        [Fact]
        public async Task UpdatePricingAsync_ValidInput_UpdatesPricing()
        {
            // Arrange
            var lawyerId = 1;
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 700.00m,
                DurationMinutes = 90
            };

            var existingPricing = new LawyerPricing 
            { 
                LawyerId = lawyerId, 
                SpecializationId = 1, 
                InteractionTypeId = 1, 
                Price = 500, 
                DurationMinutes = 60 
            };

            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(lawyerId, 1, 1)).ReturnsAsync(existingPricing);

            // Act
            await _service.UpdatePricingAsync(lawyerId, dto);

            // Assert
            _pricingRepositoryMock.Verify(x => x.UpdateAsync(It.Is<LawyerPricing>(p => 
                p.Price == 700.00m && p.DurationMinutes == 90)), Times.Once);
        }

        [Fact]
        public async Task DeletePricingAsync_ExistingPricing_DeletesPricing()
        {
            // Arrange
            var lawyerId = 1;
            var specializationId = 1;
            var interactionTypeId = 1;
            var pricing = new LawyerPricing 
            { 
                LawyerId = lawyerId, 
                SpecializationId = specializationId, 
                InteractionTypeId = interactionTypeId, 
                Price = 500, 
                DurationMinutes = 60 
            };

            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(lawyerId, specializationId, interactionTypeId))
                .ReturnsAsync(pricing);

            // Act
            await _service.DeletePricingAsync(lawyerId, specializationId, interactionTypeId);

            // Assert
            _pricingRepositoryMock.Verify(x => x.DeleteAsync(lawyerId, specializationId, interactionTypeId), Times.Once);
        }

        [Fact]
        public async Task DeletePricingAsync_NonExistingPricing_ThrowsArgumentException()
        {
            // Arrange
            _pricingRepositoryMock.Setup(x => x.GetPricingAsync(999, 999, 999))
                .ReturnsAsync((LawyerPricing?)null);

            // Act & Assert
            await Assert.ThrowsAsync<ArgumentException>(() => _service.DeletePricingAsync(999, 999, 999));
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}

