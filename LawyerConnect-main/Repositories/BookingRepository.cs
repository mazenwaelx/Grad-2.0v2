using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace LawyerConnect.Repositories
{
    public class BookingRepository : IBookingRepository
    {
        private readonly LawyerConnectDbContext _context;
        public BookingRepository(LawyerConnectDbContext context) => _context = context;

        public async Task<Booking?> GetByIdAsync(int id) =>
            await _context.Bookings
                .Include(b => b.User)
                .Include(b => b.Lawyer)
                    .ThenInclude(l => l.User)
                .Include(b => b.Specialization)
                .Include(b => b.InteractionType)
                .FirstOrDefaultAsync(b => b.Id == id);

        public async Task<IEnumerable<Booking>> GetUserBookingsAsync(int userId, int page = 1, int limit = 10) =>
            await _context.Bookings
                .Include(b => b.Lawyer)
                    .ThenInclude(l => l.User)
                .Include(b => b.Specialization)
                .Include(b => b.InteractionType)
                .Where(b => b.UserId == userId)
                .OrderByDescending(b => b.Date)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

        public async Task<IEnumerable<Booking>> GetLawyerBookingsAsync(int lawyerId, int page = 1, int limit = 10) =>
            await _context.Bookings
                .Include(b => b.User)
                .Include(b => b.Specialization)
                .Include(b => b.InteractionType)
                .Where(b => b.LawyerId == lawyerId)
                .OrderByDescending(b => b.Date)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

        public async Task<List<Booking>> GetLawyerBookingsForDateAsync(int lawyerId, DateTime date, int durationMinutes)
        {
            var startTime = date;
            var endTime = date.AddMinutes(durationMinutes);

            return await _context.Bookings
                .Where(b => b.LawyerId == lawyerId &&
                           ((b.Date >= startTime && b.Date < endTime) ||
                            (b.Date.AddMinutes(b.DurationSnapshot) > startTime && b.Date < endTime)))
                .ToListAsync();
        }

        public async Task<List<Booking>> GetAllAsync() =>
            await _context.Bookings
                .Include(b => b.User)
                .Include(b => b.Lawyer)
                .ToListAsync();

        public async Task AddAsync(Booking booking)
        {
            await _context.Bookings.AddAsync(booking);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(Booking booking)
        {
            _context.Bookings.Update(booking);
            await _context.SaveChangesAsync();
        }
    }
}

