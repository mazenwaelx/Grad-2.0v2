using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface ISpecializationService
    {
        Task<List<SpecializationDto>> GetAllAsync();
        Task<SpecializationDto?> GetByIdAsync(int id);
        Task<SpecializationDto> CreateAsync(SpecializationDto dto);
        Task UpdateAsync(int id, SpecializationDto dto);
        Task DeleteAsync(int id);
    }
}
