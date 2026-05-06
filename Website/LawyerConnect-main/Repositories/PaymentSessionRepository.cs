using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;

namespace LawyerConnect.Repositories
{
    public class PaymentSessionRepository : IPaymentSessionRepository
    {
        private readonly LawyerConnectDbContext _context;
        public PaymentSessionRepository(LawyerConnectDbContext context) => _context = context;

        public async Task<PaymentSession?> GetByIdAsync(int id) =>
            await _context.PaymentSessions
                .Include(p => p.Booking)
                    .ThenInclude(b => b.User)
                .Include(p => p.Booking)
                    .ThenInclude(b => b.Lawyer)
                        .ThenInclude(l => l.User)
                .FirstOrDefaultAsync(p => p.Id == id);

        public async Task<PaymentSession?> GetByBookingIdAsync(int bookingId) =>
            await _context.PaymentSessions
                .Include(p => p.Booking)
                    .ThenInclude(b => b.User)
                .Include(p => p.Booking)
                    .ThenInclude(b => b.Lawyer)
                        .ThenInclude(l => l.User)
                .FirstOrDefaultAsync(p => p.BookingId == bookingId);

        public async Task<PaymentSession?> GetByProviderSessionIdAsync(string providerSessionId) =>
            await _context.PaymentSessions
                .Include(p => p.Booking)
                    .ThenInclude(b => b.User)
                .Include(p => p.Booking)
                    .ThenInclude(b => b.Lawyer)
                        .ThenInclude(l => l.User)
                .FirstOrDefaultAsync(p => p.ProviderSessionId == providerSessionId);

        public async Task<List<PaymentSession>> GetByUserIdAsync(int userId, int page = 1, int limit = 10) =>
            await _context.PaymentSessions
                .Include(p => p.Booking)
                    .ThenInclude(b => b.User)
                .Include(p => p.Booking)
                    .ThenInclude(b => b.Lawyer)
                        .ThenInclude(l => l.User)
                .Where(p => p.Booking.UserId == userId)
                .OrderByDescending(p => p.CreatedAt)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

        public async Task<List<PaymentSession>> GetAllAsync() =>
            await _context.PaymentSessions
                .Include(p => p.Booking)
                    .ThenInclude(b => b.User)
                .Include(p => p.Booking)
                    .ThenInclude(b => b.Lawyer)
                        .ThenInclude(l => l.User)
                .OrderByDescending(p => p.CreatedAt)
                .ToListAsync();

        public async Task AddAsync(PaymentSession paymentSession)
        {
            await _context.PaymentSessions.AddAsync(paymentSession);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(PaymentSession paymentSession)
        {
            _context.PaymentSessions.Update(paymentSession);
            await _context.SaveChangesAsync();
        }
    }
}

