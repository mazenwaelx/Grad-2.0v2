using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Tests.TestHelpers;

namespace LawyerConnect.Tests.Repositories
{
    public class BookingRepositoryTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly BookingRepository _repository;

        public BookingRepositoryTests()
        {
            _context = TestDbContextFactory.Create();
            _repository = new BookingRepository(_context);
            SeedBooking();
        }

        private void SeedBooking()
        {
            var client = new User { Email = "client@test.com", FullName = "Client", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            var lawyerUser = new User { Email = "lawyer2@test.com", FullName = "Lawyer", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.AddRange(client, lawyerUser);
            _context.SaveChanges();

            var lawyer = new Lawyer { UserId = lawyerUser.Id, ExperienceYears = 3, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            _context.SaveChanges();

            _context.Bookings.Add(new Booking
            {
                UserId = client.Id,
                LawyerId = lawyer.Id,
                SpecializationId = 1,
                InteractionTypeId = 1,
                PriceSnapshot = 500,
                DurationSnapshot = 60,
                Date = DateTime.UtcNow.AddDays(1),
                Status = "Pending",
                PaymentStatus = "Pending",
                CreatedAt = DateTime.UtcNow
            });
            _context.SaveChanges();
        }

        [Fact]
        public async Task GetByIdAsync_IncludesRelatedEntities()
        {
            var booking = await _repository.GetByIdAsync(1);
            booking.Should().NotBeNull();
            booking!.User.FullName.Should().Be("Client");
            booking.Lawyer.User.FullName.Should().Be("Lawyer");
        }

        [Fact]
        public async Task GetUserBookingsAsync_ReturnsUserBookings()
        {
            var bookings = await _repository.GetUserBookingsAsync(1);
            bookings.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetLawyerBookingsAsync_ReturnsLawyerBookings()
        {
            var bookings = await _repository.GetLawyerBookingsAsync(1);
            bookings.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetLawyerBookingsForDateAsync_DetectsOverlap()
        {
            var date = DateTime.UtcNow.AddDays(1);
            var overlaps = await _repository.GetLawyerBookingsForDateAsync(1, date, 60);
            overlaps.Should().HaveCount(1);
        }

        public void Dispose() => _context.Dispose();
    }
}
