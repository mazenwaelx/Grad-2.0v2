using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Tests.TestHelpers;

namespace LawyerConnect.Tests.Repositories
{
    public class RemainingRepositoryTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;

        public RemainingRepositoryTests()
        {
            _context = TestDbContextFactory.Create();
        }

        [Fact]
        public async Task SpecializationRepository_Crud_Works()
        {
            var repository = new SpecializationRepository(_context);
            var specialization = new Specialization { Name = "Maritime Law", Description = "Sea law" };

            await repository.AddAsync(specialization);
            (await repository.GetByIdAsync(specialization.Id))!.Name.Should().Be("Maritime Law");

            specialization.Name = "Updated";
            await repository.UpdateAsync(specialization);
            (await repository.GetAllAsync()).Any(s => s.Name == "Updated").Should().BeTrue();

            await repository.DeleteAsync(specialization.Id);
            (await repository.GetByIdAsync(specialization.Id)).Should().BeNull();
        }

        [Fact]
        public async Task PricingRepository_GetAndDelete_Work()
        {
            var user = new User { Email = "price@test.com", FullName = "P", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();
            var lawyer = new Lawyer { UserId = user.Id, ExperienceYears = 1, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            var pricing = new LawyerPricing
            {
                LawyerId = lawyer.Id,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 300,
                DurationMinutes = 30
            };

            var repository = new PricingRepository(_context);
            await repository.AddAsync(pricing);

            var found = await repository.GetPricingAsync(lawyer.Id, 1, 1);
            found.Should().NotBeNull();

            var all = await repository.GetLawyerPricingAsync(lawyer.Id);
            all.Should().HaveCount(1);

            await repository.DeleteAsync(lawyer.Id, 1, 1);
            (await repository.GetPricingAsync(lawyer.Id, 1, 1)).Should().BeNull();
        }

        [Fact]
        public async Task ReviewRepository_AddAndQuery_Work()
        {
            var user = new User { Email = "reviewer@test.com", FullName = "R", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            var lawyerUser = new User { Email = "reviewed@test.com", FullName = "L", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.AddRange(user, lawyerUser);
            await _context.SaveChangesAsync();
            var lawyer = new Lawyer { UserId = lawyerUser.Id, ExperienceYears = 1, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            var repository = new ReviewRepository(_context);
            var review = new Review
            {
                BookingId = 1,
                UserId = user.Id,
                LawyerId = lawyer.Id,
                Rating = 5,
                Comment = "Great",
                CreatedAt = DateTime.UtcNow
            };
            await repository.AddAsync(review);

            (await repository.GetLawyerReviewsAsync(lawyer.Id)).Should().HaveCount(1);
            (await repository.GetByIdAsync(review.Id))!.Rating.Should().Be(5);
        }

        [Fact]
        public async Task NotificationRepository_AddUpdateDelete_Work()
        {
            var user = new User { Email = "notify@test.com", FullName = "N", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var repository = new NotificationRepository(_context);
            var notification = new Notification
            {
                UserId = user.Id,
                Title = "Title",
                Message = "Message",
                Type = "Info",
                CreatedAt = DateTime.UtcNow
            };
            await repository.AddAsync(notification);

            (await repository.GetUserNotificationsAsync(user.Id)).Should().HaveCount(1);

            notification.IsRead = true;
            await repository.UpdateAsync(notification);
            (await repository.GetByIdAsync(notification.Id))!.IsRead.Should().BeTrue();

            await repository.DeleteAsync(notification.Id);
            (await repository.GetByIdAsync(notification.Id)).Should().BeNull();
        }

        [Fact]
        public async Task PaymentSessionRepository_Queries_Work()
        {
            var client = new User { Email = "pay@test.com", FullName = "P", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            var lawyerUser = new User { Email = "paylawyer@test.com", FullName = "L", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.AddRange(client, lawyerUser);
            await _context.SaveChangesAsync();
            var lawyer = new Lawyer { UserId = lawyerUser.Id, ExperienceYears = 1, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();
            var booking = new Booking
            {
                UserId = client.Id,
                LawyerId = lawyer.Id,
                SpecializationId = 1,
                InteractionTypeId = 1,
                PriceSnapshot = 100,
                DurationSnapshot = 30,
                Date = DateTime.UtcNow,
                Status = "Pending",
                PaymentStatus = "Pending",
                CreatedAt = DateTime.UtcNow
            };
            _context.Bookings.Add(booking);
            await _context.SaveChangesAsync();

            var repository = new PaymentSessionRepository(_context);
            var session = new PaymentSession
            {
                BookingId = booking.Id,
                Amount = 100,
                Status = "Success",
                Provider = "Stripe",
                ProviderSessionId = "sess_123",
                CreatedAt = DateTime.UtcNow
            };
            await repository.AddAsync(session);

            (await repository.GetByProviderSessionIdAsync("sess_123")).Should().NotBeNull();
            (await repository.GetByBookingIdAsync(booking.Id)).Should().NotBeNull();
            (await repository.GetAllAsync()).Should().NotBeEmpty();
        }

        [Fact]
        public async Task ChatRepositories_AddAndQuery_Work()
        {
            var roomRepository = new ChatRoomRepository(_context);
            var messageRepository = new ChatMessageRepository(_context);

            var user = new User { Email = "chat@test.com", FullName = "Chat", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var room = new ChatRoom { BookingId = 1, CreatedAt = DateTime.UtcNow };
            await roomRepository.AddAsync(room);

            (await roomRepository.GetByBookingIdAsync(1)).Should().NotBeNull();

            var message = new ChatMessage
            {
                ChatRoomId = room.Id,
                SenderId = user.Id,
                Message = "Hi",
                SentAt = DateTime.UtcNow
            };
            await messageRepository.AddAsync(message);

            (await messageRepository.GetChatMessagesAsync(room.Id)).Should().HaveCount(1);
            (await messageRepository.GetMessagesByBookingIdAsync(1)).Should().HaveCount(1);
        }

        public void Dispose() => _context.Dispose();
    }
}
