using FluentAssertions;
using LawyerConnect.Controllers;
using LawyerConnect.Data;
using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging.Abstractions;
using Moq;

namespace LawyerConnect.Tests.Controllers
{
    public class AuthControllerTests
    {
        [Fact]
        public async Task Register_DuplicateEmail_ReturnsConflict()
        {
            var authService = new Mock<IAuthService>();
            var userRepository = new Mock<IUserRepository>();
            userRepository.Setup(x => x.GetByEmailAsync("exists@test.com"))
                .ReturnsAsync(new User { Email = "exists@test.com" });

            var controller = new AuthController(
                authService.Object,
                userRepository.Object,
                TestConfigurationFactory.Create(),
                NullLogger<AuthController>.Instance);

            var result = await controller.Register(new RegisterRequestDto
            {
                User = new UserRegisterDto
                {
                    Email = "exists@test.com",
                    Password = "password",
                    FullName = "Exists"
                }
            });

            result.Result.Should().BeOfType<ConflictObjectResult>();
        }

        [Fact]
        public async Task Register_ValidUser_ReturnsOk()
        {
            var authService = new Mock<IAuthService>();
            authService.Setup(x => x.RegisterAsync(It.IsAny<RegisterRequestDto>(), It.IsAny<string>(), "User"))
                .ReturnsAsync(new AuthResponseDto
                {
                    Token = "token",
                    ExpiresAt = DateTime.UtcNow.AddMinutes(30),
                    User = new UserResponseDto { Email = "new@test.com" }
                });

            var userRepository = new Mock<IUserRepository>();
            userRepository.Setup(x => x.GetByEmailAsync("new@test.com")).ReturnsAsync((User?)null);

            var controller = new AuthController(
                authService.Object,
                userRepository.Object,
                TestConfigurationFactory.Create(),
                NullLogger<AuthController>.Instance);

            var result = await controller.Register(new RegisterRequestDto
            {
                User = new UserRegisterDto
                {
                    Email = "new@test.com",
                    Password = "password",
                    FullName = "New User",
                    Phone = "1234567890",
                    City = "Cairo"
                }
            });

            result.Result.Should().BeOfType<CreatedAtActionResult>();
        }
    }

    public class InteractionTypesControllerTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;

        public InteractionTypesControllerTests()
        {
            _context = TestDbContextFactory.Create();
        }

        [Fact]
        public async Task GetAll_ReturnsSeededInteractionTypes()
        {
            var controller = new InteractionTypesController(_context, NullLogger<InteractionTypesController>.Instance);

            var result = await controller.GetAll();

            var ok = result.Result.Should().BeOfType<OkObjectResult>().Subject;
            var types = ok.Value.Should().BeAssignableTo<IEnumerable<InteractionTypeDto>>().Subject;
            types.Should().HaveCount(4);
        }

        public void Dispose() => _context.Dispose();
    }

    public class LawyersControllerTests
    {
        [Fact]
        public async Task GetFeatured_ReturnsLawyersFromService()
        {
            var lawyerService = new Mock<ILawyerService>();
            lawyerService.Setup(x => x.GetFeaturedLawyersAsync(3))
                .ReturnsAsync(new List<LawyerResponseDto>
                {
                    new() { Id = 1, FullName = "Featured Lawyer", IsVerified = true }
                });

            var controller = new LawyersController(
                lawyerService.Object,
                new Mock<IPricingService>().Object,
                NullLogger<LawyersController>.Instance);

            var result = await controller.GetFeatured(3);

            var ok = result.Result.Should().BeOfType<OkObjectResult>().Subject;
            var lawyers = ok.Value.Should().BeAssignableTo<List<LawyerResponseDto>>().Subject;
            lawyers.Should().HaveCount(1);
        }
    }

    public class SpecializationsControllerTests
    {
        [Fact]
        public async Task GetAll_ReturnsSpecializations()
        {
            var service = new Mock<ISpecializationService>();
            service.Setup(x => x.GetAllAsync())
                .ReturnsAsync(new List<SpecializationDto>
                {
                    new() { Id = 1, Name = "Criminal Law" }
                });

            var controller = new SpecializationsController(
                service.Object,
                NullLogger<SpecializationsController>.Instance);

            var result = await controller.GetAll();
            result.Result.Should().BeOfType<OkObjectResult>();
        }
    }
}
