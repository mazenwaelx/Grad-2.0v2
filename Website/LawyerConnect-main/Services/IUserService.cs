using LawyerConnect.DTOs;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LawyerConnect.Services
{
    public interface IUserService
    {
        Task<UserResponseDto> RegisterUserAsync(UserRegisterDto dto, string passwordHash, string role);
        Task<UserResponseDto?> GetByIdAsync(int id);
        Task<IEnumerable<UserResponseDto>> GetPagedAsync(int page, int limit);
        Task UpdateUserRoleAsync(int userId, string newRole);
    }
}

