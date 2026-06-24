using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Tests.Repositories
{
    public class RefreshTokenRepositoryTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly RefreshTokenRepository _repository;

        public RefreshTokenRepositoryTests()
        {
            _context = TestDbContextFactory.Create(seed: false);
            _repository = new RefreshTokenRepository(_context);
            _context.Users.Add(new User
            {
                Email = "token@test.com",
                FullName = "Token User",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            });
            _context.SaveChanges();
        }

        [Fact]
        public async Task AddAsync_GetByTokenHashAsync_RevokeAsync_Work()
        {
            var token = new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = 1,
                TokenHash = "abc123",
                ExpiresAt = DateTime.UtcNow.AddDays(7),
                CreatedAt = DateTime.UtcNow
            };

            await _repository.AddAsync(token);

            var found = await _repository.GetByTokenHashAsync("abc123");
            found.Should().NotBeNull();

            await _repository.RevokeAsync(found!, RefreshTokenRevokeReason.Logout);
            found!.Revoked.Should().BeTrue();
        }

        [Fact]
        public async Task RevokeAllAsync_RevokesActiveTokens()
        {
            await _repository.AddAsync(new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = 1,
                TokenHash = "one",
                ExpiresAt = DateTime.UtcNow.AddDays(7),
                CreatedAt = DateTime.UtcNow
            });
            await _repository.AddAsync(new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = 1,
                TokenHash = "two",
                ExpiresAt = DateTime.UtcNow.AddDays(7),
                CreatedAt = DateTime.UtcNow
            });

            await _repository.RevokeAllAsync(1, RefreshTokenRevokeReason.LogoutAll);

            (await _context.RefreshTokens.CountAsync(t => !t.Revoked)).Should().Be(0);
        }

        [Fact]
        public async Task DeleteOldTokensAsync_RemovesExpiredRevokedTokens()
        {
            await _repository.AddAsync(new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = 1,
                TokenHash = "old",
                ExpiresAt = DateTime.UtcNow.AddDays(-1),
                CreatedAt = DateTime.UtcNow.AddDays(-30),
                Revoked = true,
                RevokedDate = DateTime.UtcNow.AddDays(-20)
            });

            await _repository.DeleteOldTokensAsync(14);

            (await _context.RefreshTokens.CountAsync()).Should().Be(0);
        }

        public void Dispose() => _context.Dispose();
    }
}
