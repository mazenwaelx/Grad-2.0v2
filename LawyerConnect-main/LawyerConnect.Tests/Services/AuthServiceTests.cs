using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;

namespace LawyerConnect.Tests.Services
{
    public class AuthServiceTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly AuthService _service;

        public AuthServiceTests()
        {
            _context = TestDbContextFactory.Create();
            var userRepository = new UserRepository(_context);
            var refreshTokenRepository = new RefreshTokenRepository(_context);
            _service = new AuthService(
                userRepository,
                refreshTokenRepository,
                TestConfigurationFactory.Create(),
                NullLogger<AuthService>.Instance,
                _context);
        }

        [Fact]
        public async Task RegisterAsync_UserRole_CreatesUserAndReturnsToken()
        {
            var dto = new RegisterRequestDto
            {
                User = new UserRegisterDto
                {
                    Email = "user@test.com",
                    FullName = "Test User",
                    Phone = "123",
                    City = "Cairo"
                }
            };

            var result = await _service.RegisterAsync(dto, PasswordHasher.Hash("password123"), "User");

            result.Token.Should().NotBeNullOrWhiteSpace();
            result.User.Email.Should().Be("user@test.com");
            (await _context.Users.CountAsync()).Should().Be(1);
        }

        [Fact]
        public async Task RegisterAsync_LawyerRole_CreatesLawyerProfilePricingAndSpecializations()
        {
            var dto = new RegisterRequestDto
            {
                User = new UserRegisterDto
                {
                    Email = "lawyer@test.com",
                    FullName = "Test Lawyer",
                    Phone = "123",
                    City = "Cairo"
                },
                Lawyer = new LawyerRegisterDto
                {
                    ExperienceYears = 5,
                    Address = "123 Main St",
                    Latitude = 30.0m,
                    Longitude = 31.0m,
                    SpecializationIds = new List<int> { 1, 2 },
                    BaseHourlyRate = 750m
                }
            };

            var result = await _service.RegisterAsync(dto, PasswordHasher.Hash("password123"), "Lawyer");

            result.User.Role.Should().Be("Lawyer");
            var lawyer = await _context.Lawyers.Include(l => l.Specializations).SingleAsync();
            lawyer.Specializations.Should().HaveCount(2);
            (await _context.LawyerPricings.CountAsync()).Should().Be(8); // 2 specs x 4 interaction types
        }

        [Fact]
        public async Task LoginAsync_ValidCredentials_ReturnsTokens()
        {
            var user = new User
            {
                Email = "login@test.com",
                FullName = "Login User",
                PasswordHash = PasswordHasher.Hash("secret"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var result = await _service.LoginAsync(
                new LoginDto { Email = "login@test.com", Password = "secret" },
                "127.0.0.1",
                "TestAgent");

            result.Token.Should().NotBeNullOrWhiteSpace();
            result.RefreshToken.Should().NotBeNullOrWhiteSpace();
            (await _context.RefreshTokens.CountAsync()).Should().Be(1);
        }

        [Fact]
        public async Task LoginAsync_InvalidPassword_ThrowsUnauthorized()
        {
            var user = new User
            {
                Email = "bad@test.com",
                FullName = "Bad Login",
                PasswordHash = PasswordHasher.Hash("correct"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var act = () => _service.LoginAsync(
                new LoginDto { Email = "bad@test.com", Password = "wrong" },
                "127.0.0.1",
                "TestAgent");

            await act.Should().ThrowAsync<UnauthorizedAccessException>();
        }

        [Fact]
        public async Task RefreshTokenAsync_ValidToken_RotatesToken()
        {
            var user = new User
            {
                Email = "refresh@test.com",
                FullName = "Refresh User",
                PasswordHash = PasswordHasher.Hash("secret"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var login = await _service.LoginAsync(
                new LoginDto { Email = "refresh@test.com", Password = "secret" },
                "127.0.0.1",
                "TestAgent");

            var refreshed = await _service.RefreshTokenAsync(
                login.RefreshToken!,
                "127.0.0.1",
                "TestAgent");

            refreshed.Token.Should().NotBeNullOrWhiteSpace();
            refreshed.RefreshToken.Should().NotBe(login.RefreshToken);
            (await _context.RefreshTokens.CountAsync(t => t.Revoked)).Should().Be(1);
        }

        [Fact]
        public async Task RefreshTokenAsync_RevokedToken_ThrowsAndRevokesAllSessions()
        {
            var user = new User
            {
                Email = "replay@test.com",
                FullName = "Replay User",
                PasswordHash = PasswordHasher.Hash("secret"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var login = await _service.LoginAsync(
                new LoginDto { Email = "replay@test.com", Password = "secret" },
                "127.0.0.1",
                "TestAgent");

            var refreshToken = login.RefreshToken!;
            await _service.RefreshTokenAsync(refreshToken, "127.0.0.1", "TestAgent");

            var act = () => _service.RefreshTokenAsync(refreshToken, "127.0.0.1", "TestAgent");
            await act.Should().ThrowAsync<UnauthorizedAccessException>();
        }

        [Fact]
        public async Task LogoutAsync_SingleDevice_RevokesCurrentToken()
        {
            var user = new User
            {
                Email = "logout@test.com",
                FullName = "Logout User",
                PasswordHash = PasswordHasher.Hash("secret"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var login = await _service.LoginAsync(
                new LoginDto { Email = "logout@test.com", Password = "secret" },
                "127.0.0.1",
                "TestAgent");

            await _service.LogoutAsync(user.Id, login.RefreshToken!, logoutAllDevices: false);

            var stored = await _context.RefreshTokens.SingleAsync();
            stored.Revoked.Should().BeTrue();
        }

        [Fact]
        public async Task GetUserByIdAsync_ExistingUser_ReturnsDto()
        {
            var user = new User
            {
                Email = "lookup@test.com",
                FullName = "Lookup User",
                PasswordHash = PasswordHasher.Hash("secret"),
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var result = await _service.GetUserByIdAsync(user.Id);

            result.Email.Should().Be("lookup@test.com");
        }

        [Fact]
        public async Task GetUserByIdAsync_MissingUser_ThrowsKeyNotFound()
        {
            var act = () => _service.GetUserByIdAsync(999);
            await act.Should().ThrowAsync<KeyNotFoundException>();
        }

        public void Dispose() => _context.Dispose();
    }
}
