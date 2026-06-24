using FluentAssertions;
using LawyerConnect.Data;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.Extensions.Logging.Abstractions;

namespace LawyerConnect.Tests.Services
{
    public class ServiceCoverageGapTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;

        public ServiceCoverageGapTests()
        {
            _context = TestDbContextFactory.Create();
        }

        [Fact]
        public async Task NotificationService_DeleteNotificationAsync_RemovesOwnedNotification()
        {
            var repository = new NotificationRepository(_context);
            var userRepository = new UserRepository(_context);
            var service = new NotificationService(
                repository,
                userRepository,
                _context,
                NullLogger<NotificationService>.Instance);

            var user = new User { Email = "gap1@test.com", FullName = "N", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            var notification = new Notification
            {
                UserId = user.Id,
                Title = "T",
                Message = "M",
                Type = "System",
                CreatedAt = DateTime.UtcNow
            };
            await repository.AddAsync(notification);

            await service.DeleteNotificationAsync(notification.Id, user.Id);

            (await repository.GetByIdAsync(notification.Id)).Should().BeNull();
        }

        [Fact]
        public async Task NotificationService_MarkAllAsReadAsync_MarksAllUserNotifications()
        {
            var repository = new NotificationRepository(_context);
            var userRepository = new UserRepository(_context);
            var service = new NotificationService(
                repository,
                userRepository,
                _context,
                NullLogger<NotificationService>.Instance);

            var user = new User { Email = "gap2@test.com", FullName = "N", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            await repository.AddAsync(new Notification { UserId = user.Id, Title = "1", Message = "m", Type = "System", CreatedAt = DateTime.UtcNow });
            await repository.AddAsync(new Notification { UserId = user.Id, Title = "2", Message = "m", Type = "System", CreatedAt = DateTime.UtcNow });

            await service.MarkAllAsReadAsync(user.Id);

            var notifications = await repository.GetUserNotificationsAsync(user.Id);
            notifications.Should().OnlyContain(n => n.IsRead);
        }

        [Fact]
        public async Task ReviewService_GetFeaturedReviewsAsync_ReturnsTopReviews()
        {
            var service = new ReviewService(
                new BookingRepository(_context),
                new LawyerRepository(_context),
                new NotificationRepository(_context),
                new ReviewRepository(_context),
                _context,
                NullLogger<ReviewService>.Instance);

            var user = new User { Email = "gap3@test.com", FullName = "U", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            var lawyerUser = new User { Email = "gap4@test.com", FullName = "L", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.AddRange(user, lawyerUser);
            await _context.SaveChangesAsync();
            var lawyer = new Lawyer { UserId = lawyerUser.Id, ExperienceYears = 1, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            _context.Reviews.Add(new Review { BookingId = 1, UserId = user.Id, LawyerId = lawyer.Id, Rating = 5, Comment = "Excellent", CreatedAt = DateTime.UtcNow });
            _context.Reviews.Add(new Review { BookingId = 2, UserId = user.Id, LawyerId = lawyer.Id, Rating = 3, Comment = "Okay", CreatedAt = DateTime.UtcNow });
            await _context.SaveChangesAsync();

            var featured = await service.GetFeaturedReviewsAsync(1);
            featured.Should().HaveCount(1);
            featured[0].Rating.Should().Be(5);
        }

        [Fact]
        public async Task BookingService_GetUserBookingsAsync_ReturnsBookings()
        {
            var service = new BookingService(
                new BookingRepository(_context),
                new LawyerRepository(_context),
                new PricingRepository(_context),
                new ChatRoomRepository(_context),
                new NotificationRepository(_context),
                _context,
                NullLogger<BookingService>.Instance);

            var client = new User { Email = "gap5@test.com", FullName = "C", PasswordHash = "h", Role = "User", CreatedAt = DateTime.UtcNow };
            var lawyerUser = new User { Email = "gap6@test.com", FullName = "L", PasswordHash = "h", Role = "Lawyer", CreatedAt = DateTime.UtcNow };
            _context.Users.AddRange(client, lawyerUser);
            await _context.SaveChangesAsync();
            var lawyer = new Lawyer { UserId = lawyerUser.Id, ExperienceYears = 1, Address = "A", CreatedAt = DateTime.UtcNow };
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();
            _context.Bookings.Add(new Booking
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
            });
            await _context.SaveChangesAsync();

            var bookings = await service.GetUserBookingsAsync(client.Id);
            bookings.Should().HaveCount(1);
        }

        [Fact]
        public async Task AdminService_UnsuspendUserAsync_CreatesRestoreNotification()
        {
            var userRepository = new UserRepository(_context);
            var notificationRepository = new NotificationRepository(_context);
            var service = new AdminService(
                userRepository,
                new LawyerRepository(_context),
                new BookingRepository(_context),
                new PaymentSessionRepository(_context),
                notificationRepository,
                _context,
                NullLogger<AdminService>.Instance);

            var user = new User
            {
                Email = "gap7@test.com",
                FullName = "Suspended",
                PasswordHash = "h",
                Role = "User",
                CreatedAt = DateTime.UtcNow
            };
            await userRepository.AddAsync(user);

            await service.UnsuspendUserAsync(user.Id);

            var notifications = await notificationRepository.GetUserNotificationsAsync(user.Id);
            notifications.Should().ContainSingle(n => n.Title == "Account Restored");
        }

        public void Dispose() => _context.Dispose();
    }
}
