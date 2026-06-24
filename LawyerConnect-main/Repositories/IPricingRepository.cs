using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface IPricingRepository
    {
        Task<LawyerPricing?> GetPricingAsync(int lawyerId, int specializationId, int interactionTypeId);
        Task<List<LawyerPricing>> GetLawyerPricingAsync(int lawyerId);
        Task AddAsync(LawyerPricing pricing);
        Task UpdateAsync(LawyerPricing pricing);
        Task DeleteAsync(int lawyerId, int specializationId, int interactionTypeId);
    }
}
