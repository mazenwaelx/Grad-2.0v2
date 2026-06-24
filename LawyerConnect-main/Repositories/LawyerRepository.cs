using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace LawyerConnect.Repositories
{
    public class LawyerRepository : ILawyerRepository
    {
        private readonly LawyerConnectDbContext _context;

        public LawyerRepository(LawyerConnectDbContext context) => _context = context;

        public async Task<Lawyer?> GetByIdAsync(int id) =>
            await _context.Lawyers
                .Include(l => l.User)
                .Include(l => l.Specializations!)
                    .ThenInclude(ls => ls.Specialization)
                .Include(l => l.Reviews)
                .FirstOrDefaultAsync(l => l.Id == id);

        public async Task<Lawyer?> GetByUserIdAsync(int userId) =>
            await _context.Lawyers
                .Include(l => l.User)
                .Include(l => l.Specializations!)
                    .ThenInclude(ls => ls.Specialization)
                .Include(l => l.Reviews)
                .FirstOrDefaultAsync(l => l.UserId == userId);

        public async Task<IEnumerable<Lawyer>> GetPagedAsync(int page, int limit) =>
            await _context.Lawyers
                .Include(l => l.User)
                .Include(l => l.Specializations!)
                    .ThenInclude(ls => ls.Specialization)
                .Include(l => l.Reviews)
                .OrderBy(l => l.Id)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();

        public async Task<List<Lawyer>> GetAllAsync() =>
            await _context.Lawyers
                .Include(l => l.User)
                .Include(l => l.Specializations!)
                    .ThenInclude(ls => ls.Specialization)
                .Include(l => l.Reviews)
                .ToListAsync();

        public async Task AddAsync(Lawyer lawyer)
        {
            await _context.Lawyers.AddAsync(lawyer);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(Lawyer lawyer)
        {
            _context.Lawyers.Update(lawyer);
            await _context.SaveChangesAsync();
        }
    }
}

