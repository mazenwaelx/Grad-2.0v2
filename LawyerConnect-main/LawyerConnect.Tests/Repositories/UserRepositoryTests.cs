using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Tests.Repositories
{
    public class UserRepositoryTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly UserRepository _repository;

        public UserRepositoryTests()
        {
            _context = TestDbContextFactory.Create();
            _repository = new UserRepository(_context);
        }

        [Fact]
        public async Task AddAsync_AndGetByEmailAsync_Works()
        {
            var user = new User
            {
                Email = "repo@test.com",
                FullName = "Repo User",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };

            await _repository.AddAsync(user);

            var found = await _repository.GetByEmailAsync("repo@test.com");
            found.Should().NotBeNull();
            found!.FullName.Should().Be("Repo User");
        }

        [Fact]
        public async Task GetPagedAsync_ReturnsRequestedPage()
        {
            for (var i = 1; i <= 5; i++)
            {
                _context.Users.Add(new User
                {
                    Email = $"user{i}@test.com",
                    FullName = $"User {i}",
                    PasswordHash = "hash",
                    Role = "User",
                    CreatedAt = DateTime.UtcNow
                });
            }
            await _context.SaveChangesAsync();

            var page = await _repository.GetPagedAsync(2, 2);
            page.Should().HaveCount(2);
        }

        [Fact]
        public async Task UpdateAsync_AndDeleteAsync_Work()
        {
            var user = new User
            {
                Email = "mutate@test.com",
                FullName = "Before",
                PasswordHash = "hash",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            await _repository.AddAsync(user);

            user.FullName = "After";
            await _repository.UpdateAsync(user);

            var updated = await _repository.GetByIdAsync(user.Id);
            updated!.FullName.Should().Be("After");

            await _repository.DeleteAsync(updated);
            (await _repository.GetByIdAsync(user.Id)).Should().BeNull();
        }

        public void Dispose() => _context.Dispose();
    }
}
