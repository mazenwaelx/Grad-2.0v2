using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
    public class PricingRepository : IPricingRepository
    {
        private readonly LawyerConnectDbContext _context;

        public PricingRepository(LawyerConnectDbContext context)
        {
            _context = context;
        }

        public async Task<LawyerPricing?> GetPricingAsync(int lawyerId, int specializationId, int interactionTypeId)
        {
            return await _context.LawyerPricings
                .FirstOrDefaultAsync(lp => lp.LawyerId == lawyerId 
                    && lp.SpecializationId == specializationId 
                    && lp.InteractionTypeId == interactionTypeId);
        }

        public async Task<List<LawyerPricing>> GetLawyerPricingAsync(int lawyerId)
        {
            return await _context.LawyerPricings
                .Where(lp => lp.LawyerId == lawyerId)
                .Include(lp => lp.Specialization)
                .Include(lp => lp.InteractionType)
                .ToListAsync();
        }

        public async Task AddAsync(LawyerPricing pricing)
        {
            await _context.LawyerPricings.AddAsync(pricing);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(LawyerPricing pricing)
        {
            _context.LawyerPricings.Update(pricing);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(int lawyerId, int specializationId, int interactionTypeId)
        {
            var pricing = await GetPricingAsync(lawyerId, specializationId, interactionTypeId);
            if (pricing != null)
            {
                _context.LawyerPricings.Remove(pricing);
                await _context.SaveChangesAsync();
            }
        }
    }
}
