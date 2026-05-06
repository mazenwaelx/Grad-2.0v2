using LawyerConnect.DTOs;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LawyerConnect.Services
{
    public interface ILawyerService
    {
        Task<LawyerResponseDto> RegisterLawyerAsync(LawyerRegisterDto dto, int userId);
        Task<LawyerResponseDto?> GetByIdAsync(int id);
        Task<LawyerResponseDto?> GetByUserIdAsync(int userId);
        Task<IEnumerable<LawyerResponseDto>> GetPagedAsync(int page, int limit);
        Task<List<LawyerResponseDto>> GetFeaturedLawyersAsync(int limit = 3);
        Task VerifyLawyerAsync(int id);
        Task<List<LawyerResponseDto>> SearchLawyersAsync(LawyerSearchDto filters);
    }
}

