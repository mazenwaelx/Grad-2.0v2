using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using LawyerConnect.DTOs;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using LawyerConnect.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class UsersController : ControllerBase
    {
        private readonly IUserService _userService;
        private readonly IUserRepository _userRepository;
        private readonly IRefreshTokenRepository _refreshTokenRepository;
        private readonly ILogger<UsersController> _logger;


        public UsersController(IUserService userService, IUserRepository userRepository , IRefreshTokenRepository  refreshTokenRepository, ILogger<UsersController> logger)
        {
            _userService = userService;
            _userRepository = userRepository;
            _refreshTokenRepository = refreshTokenRepository;
            _logger = logger;
        }

        [HttpGet]
        [Authorize(Roles = "Admin")]
        public async Task<ActionResult<IEnumerable<UserResponseDto>>> GetUsers([FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            var users = await _userService.GetPagedAsync(page, limit);
            return Ok(users);
        }

        public class UpdateUserDto
        {
            public string FullName { get; set; } = string.Empty;
            public string Phone { get; set; } = string.Empty;
            public string City { get; set; } = string.Empty;
        }

        [HttpPut("update")]
        [Authorize]
        public async Task<IActionResult> UpdateProfile([FromBody] UpdateUserDto dto)
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null) return NotFound();

            user.FullName = string.IsNullOrWhiteSpace(dto.FullName) ? user.FullName : dto.FullName;
            user.Phone = string.IsNullOrWhiteSpace(dto.Phone) ? user.Phone : dto.Phone;
            user.City = string.IsNullOrWhiteSpace(dto.City) ? user.City : dto.City;

            await _userRepository.UpdateAsync(user);
            return NoContent();
        }


        [HttpDelete("delete-account")]
        [Authorize]
        public async Task<IActionResult> DeleteMyAccount()
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null) return NotFound();

            //Revoke ALL refresh tokens before deletion with reason
            await _refreshTokenRepository.RevokeAllAsync(userId, RefreshTokenRevokeReason.AccountDeleted);

            // Delete user (cascade delete will handle related data)
            await _userRepository.DeleteAsync(user);

            // Clear refresh token cookie
            Response.Cookies.Delete("refreshToken");

            return Ok(new { message = "Account deleted successfully." });
        }


        public class ChangePasswordDto
        {
            public string CurrentPassword { get; set; } = string.Empty;
            public string NewPassword { get; set; } = string.Empty;
        }

        [HttpPut("change-password")]
        [Authorize]
        public async Task<IActionResult> ChangePassword([FromBody] ChangePasswordDto dto)
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null) return NotFound();

            var currentHash = HashPassword(dto.CurrentPassword);
            if (!string.Equals(user.PasswordHash, currentHash, StringComparison.Ordinal))
            {
                return Unauthorized("Current password incorrect.");
            }

            user.PasswordHash = HashPassword(dto.NewPassword);
            await _userRepository.UpdateAsync(user);

            await _refreshTokenRepository.RevokeAllAsync(userId, RefreshTokenRevokeReason.PasswordChanged);

            _logger.LogInformation($"User {userId} changed password. All sessions revoked.");

            return Ok(new { message = "Password changed successfully. Please login again." });
        }

        public class UpdateRoleDto
        {
            public int UserId { get; set; }
            public string Role { get; set; } = string.Empty;
        }

        [HttpPut("update-role")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> UpdateRole([FromBody] UpdateRoleDto dto)
        {
            if (string.IsNullOrWhiteSpace(dto.Role))
            {
                return BadRequest("Role is required.");
            }

            // Validate role
            if (dto.Role != "User" && dto.Role != "Lawyer" && dto.Role != "Admin")
            {
                return BadRequest("Invalid role. Allowed roles: User, Lawyer, Admin");
            }

            await _userService.UpdateUserRoleAsync(dto.UserId, dto.Role);
            return NoContent();
        }

        private static string HashPassword(string password)
        {
            using var sha = SHA256.Create();
            var bytes = Encoding.UTF8.GetBytes(password);
            var hash = sha.ComputeHash(bytes);
            return Convert.ToHexString(hash);
        }

        public class UploadPhotoDto
        {
            public string PhotoBase64 { get; set; } = string.Empty;
        }

        [HttpPut("upload-photo")]
        [Authorize]
        public async Task<IActionResult> UploadProfilePhoto([FromBody] UploadPhotoDto dto)
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null) return NotFound();

            // Validate base64 image (basic validation)
            if (string.IsNullOrWhiteSpace(dto.PhotoBase64))
            {
                return BadRequest("Photo data is required.");
            }

            // Check if it's a valid base64 data URL
            if (!dto.PhotoBase64.StartsWith("data:image/"))
            {
                return BadRequest("Invalid image format. Please provide a base64 encoded image.");
            }

            user.ProfilePhoto = dto.PhotoBase64;
            await _userRepository.UpdateAsync(user);

            return Ok(new { profilePhoto = user.ProfilePhoto });
        }

        [HttpDelete("remove-photo")]
        [Authorize]
        public async Task<IActionResult> RemoveProfilePhoto()
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null) return NotFound();

            user.ProfilePhoto = null;
            await _userRepository.UpdateAsync(user);

            return NoContent();
        }
    }
}

