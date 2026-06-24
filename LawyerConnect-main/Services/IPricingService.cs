using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IPricingService
    {
        Task<LawyerPricingDto?> GetPricingAsync(int lawyerId, int specializationId, int interactionTypeId);
        Task<List<LawyerPricingDto>> GetLawyerPricingAsync(int lawyerId);
        Task SetPricingAsync(int lawyerId, LawyerPricingDto dto);
        Task UpdatePricingAsync(int lawyerId, LawyerPricingDto dto);
        Task DeletePricingAsync(int lawyerId, int specializationId, int interactionTypeId);
    }
}
