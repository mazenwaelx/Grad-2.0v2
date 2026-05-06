using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
    public class ReviewRepository : IReviewRepository
    {
        private readonly LawyerConnectDbContext _context;

        public ReviewRepository(LawyerConnectDbContext context)
        {
            _context = context;
        }

        public async Task<Review?> GetByIdAsync(int id)
        {
            return await _context.Reviews
                .Include(r => r.User)
                .Include(r => r.Lawyer)
                    .ThenInclude(l => l.User)
                .FirstOrDefaultAsync(r => r.Id == id);
        }

        public async Task<Review?> GetByBookingIdAsync(int bookingId)
        {
            return await _context.Reviews
                .Include(r => r.User)
                .Include(r => r.Lawyer)
                    .ThenInclude(l => l.User)
                .FirstOrDefaultAsync(r => r.BookingId == bookingId);
        }

        public async Task<List<Review>> GetLawyerReviewsAsync(int lawyerId, int page = 1, int limit = 10)
        {
            return await _context.Reviews
                .Include(r => r.User)
                .Include(r => r.Lawyer)
                    .ThenInclude(l => l.User)
                .Where(r => r.LawyerId == lawyerId)
                .OrderByDescending(r => r.CreatedAt)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();
        }

        public async Task AddAsync(Review review)
        {
            await _context.Reviews.AddAsync(review);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(Review review)
        {
            _context.Reviews.Update(review);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(Review review)
        {
            _context.Reviews.Remove(review);
            await _context.SaveChangesAsync();
        }
    }
}
