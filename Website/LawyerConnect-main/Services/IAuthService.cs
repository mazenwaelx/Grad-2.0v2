using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Services
{
    public interface IAuthService
    {
        /// <summary>
        /// Register a new user with email, password, and role
        /// </summary>
        Task<AuthResponseDto> RegisterAsync(RegisterRequestDto dto, string passwordHash, string role);

        /// <summary>
        /// Login user with email and password, returns access token and refresh token
        /// </summary>
        Task<AuthResponseDto> LoginAsync(LoginDto dto, string ipAddress, string userAgent);

        /// <summary>
        /// Refresh access token using refresh token from cookie
        /// Implements token rotation and sliding expiration
        /// </summary>
        Task<AuthResponseDto> RefreshTokenAsync(string refreshToken, string ipAddress, string userAgent);

        /// <summary>
        /// Logout user by revoking refresh token(s)
        /// </summary>
        Task LogoutAsync(int userId, string refreshToken, bool logoutAllDevices);

        /// <summary>
        /// Get user by ID
        /// </summary>
        Task<UserResponseDto> GetUserByIdAsync(int userId);
    }
}
