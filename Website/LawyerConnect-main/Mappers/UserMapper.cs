using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class UserMapper
    {
        public static User ToUser(this UserRegisterDto dto, string passwordHash, string role = "User")
        {
            return new User
            {
                FullName = dto.FullName,
                Email = dto.Email,
                PasswordHash = passwordHash,
                Role = role,
                Phone = dto.Phone,
                City = dto.City,
                CreatedAt = DateTime.UtcNow
            };
        }
        public static UserResponseDto ToUserResponseDto(this User user)
        {
            return new UserResponseDto
            {
                Id = user.Id,
                FullName = user.FullName,
                Email = user.Email,
                Role = user.Role,
                Phone = user.Phone,
                City = user.City,
                ProfilePhoto = user.ProfilePhoto,
                CreatedAt = user.CreatedAt
            };
        }
    }
}

