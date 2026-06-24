using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Tests.Repositories
{
    public class LawyerRepositoryTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly LawyerRepository _repository;

        public LawyerRepositoryTests()
        {
            _context = TestDbContextFactory.Create();
            _repository = new LawyerRepository(_context);
            SeedLawyer();
        }

        private void SeedLawyer()
        {
            var user = new User
            {
                Email = "lawyer@test.com",
                FullName = "Lawyer One",
                PasswordHash = "hash",
                Role = "Lawyer",
                CreatedAt = DateTime.UtcNow
            };
            _context.Users.Add(user);
            _context.SaveChanges();

            var lawyer = new Lawyer
            {
                UserId = user.Id,
                ExperienceYears = 6,
                Address = "Addr",
                IsVerified = true,
                CreatedAt = DateTime.UtcNow
            };
            _context.Lawyers.Add(lawyer);
            _context.LawyerSpecializations.Add(new LawyerSpecialization
            {
                Lawyer = lawyer,
                SpecializationId = 1
            });
            _context.SaveChanges();
        }

        [Fact]
        public async Task GetByIdAsync_IncludesUserAndSpecializations()
        {
            var lawyer = await _repository.GetByIdAsync(1);
            lawyer.Should().NotBeNull();
            lawyer!.User.FullName.Should().Be("Lawyer One");
            lawyer.Specializations.Should().NotBeEmpty();
        }

        [Fact]
        public async Task GetByUserIdAsync_ReturnsLawyer()
        {
            var lawyer = await _repository.GetByUserIdAsync(1);
            lawyer.Should().NotBeNull();
        }

        [Fact]
        public async Task GetPagedAsync_ReturnsLawyers()
        {
            var lawyers = await _repository.GetPagedAsync(1, 10);
            lawyers.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetAllAsync_ReturnsAllLawyers()
        {
            var lawyers = await _repository.GetAllAsync();
            lawyers.Should().HaveCount(1);
        }

        public void Dispose() => _context.Dispose();
    }
}
