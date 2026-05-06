using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
    public class SpecializationRepository : ISpecializationRepository
    {
        private readonly LawyerConnectDbContext _context;

        public SpecializationRepository(LawyerConnectDbContext context)
        {
            _context = context;
        }

        public async Task<Specialization?> GetByIdAsync(int id)
        {
            return await _context.Specializations.FindAsync(id);
        }

        public async Task<List<Specialization>> GetAllAsync()
        {
            return await _context.Specializations.ToListAsync();
        }

        public async Task AddAsync(Specialization specialization)
        {
            await _context.Specializations.AddAsync(specialization);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(Specialization specialization)
        {
            _context.Specializations.Update(specialization);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(int id)
        {
            var specialization = await GetByIdAsync(id);
            if (specialization != null)
            {
                _context.Specializations.Remove(specialization);
                await _context.SaveChangesAsync();
            }
        }
    }
}
