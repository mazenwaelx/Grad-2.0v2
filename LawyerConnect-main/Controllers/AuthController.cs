using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using LawyerConnect.DTOs;
using LawyerConnect.Mappers;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AuthController : ControllerBase
    {
        private readonly IAuthService _authService;
        private readonly IUserRepository _userRepository;
        private readonly IConfiguration _config;
        private readonly ILogger<AuthController> _logger;

        public AuthController(
            IAuthService authService,
            IUserRepository userRepository,
            IConfiguration config,
            ILogger<AuthController> logger)
        {
            _authService = authService;
            _userRepository = userRepository;
            _config = config;
            _logger = logger;
        }

        [HttpPost("register")]
        [AllowAnonymous]
        public async Task<ActionResult<AuthResponseDto>> Register(RegisterRequestDto dto)
        {
            try
            {
                // Validate required fields
                if (string.IsNullOrWhiteSpace(dto.User.Email) || string.IsNullOrWhiteSpace(dto.User.Password))
                {
                    return BadRequest("Email and password are required.");
                }

                var existing = await _userRepository.GetByEmailAsync(dto.User.Email);
                if (existing != null)
                {
                    return Conflict("Email already registered.");
                }

                // Determine role
                string role = "User"; // Default role if not provided 

                if (!string.IsNullOrWhiteSpace(dto.User.Role)) //if role provided 
                {
                    var requestedRole = dto.User.Role.Trim();

                    // Validate role
                    if (requestedRole != "User" && requestedRole != "Lawyer" && requestedRole != "Admin")
                    {
                        return BadRequest("Invalid role. Allowed roles: User, Lawyer, Admin");
                    }

                    // Check if trying to register as Admin
                    if (requestedRole == "Admin")
                    {
                        var adminSecret = _config["AdminSecret"];
                        if (string.IsNullOrWhiteSpace(adminSecret) || dto.User.AdminSecret != adminSecret)
                        {
                            return Unauthorized("Admin registration requires a valid admin secret key.");
                        }
                        role = "Admin";
                    }
                    else
                    {
                        role = requestedRole; // User or Lawyer
                    }
                }

                // If registering as lawyer, validate lawyer data is provided
                if (role == "Lawyer" && dto.Lawyer == null)
                {
                    return BadRequest("Lawyer profile information is required when registering as a lawyer.");
                }

                // If lawyer data is provided but role is not Lawyer, set role to Lawyer
                if (dto.Lawyer != null && role == "User")
                {
                    role = "Lawyer";
                }

                var passwordHash = HashObject(dto.User.Password);
                var result = await _authService.RegisterAsync(dto, passwordHash, role);
                return CreatedAtAction(nameof(Me), new { }, result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Registration error for email: {Email}", dto.User?.Email ?? "unknown");
                return StatusCode(500, "An error occurred during registration.");
            }
        }


        [HttpPost("login")]
        [AllowAnonymous]
        public async Task<ActionResult<AuthResponseDto>> Login(LoginDto dto)
        {
            try
            {
                var ipAddress = Request.HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";
                var userAgent = Request.Headers.UserAgent.ToString();

                var result = await _authService.LoginAsync(dto, ipAddress, userAgent);

                // Set refresh token in HttpOnly cookie
                if (!string.IsNullOrWhiteSpace(result.RefreshToken) && result.RefreshTokenExpires.HasValue)
                {
                    Response.Cookies.Append("refreshToken", result.RefreshToken, new CookieOptions
                    {
                        HttpOnly = true,
                        Secure = true,
                        SameSite = SameSiteMode.Lax,
                        Expires = result.RefreshTokenExpires
                    });
                }

                return Ok(result);
            }
            catch (UnauthorizedAccessException ex)
            {
                return Unauthorized(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Login error: {ex.Message}");
                return StatusCode(500, "An error occurred during login.");
            }
        }

        [HttpGet("me")]
        [Authorize]
        public async Task<ActionResult<UserResponseDto>> Me()
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    return Unauthorized();
                }

                var user = await _authService.GetUserByIdAsync(userId);
                return Ok(user);
            }
            catch (KeyNotFoundException)
            {
                return NotFound();
            }
            catch (Exception ex)
            {
                _logger.LogError($"Get user error: {ex.Message}");
                return StatusCode(500, "An error occurred.");
            }
        }

        [HttpPost("refresh")]
        [AllowAnonymous]
        public async Task<ActionResult<AuthResponseDto>> Refresh()
        {
            try
            {
                // Get refresh token from cookie
                if (!Request.Cookies.TryGetValue("refreshToken", out var refreshToken))
                {
                    _logger.LogWarning("Refresh attempt failed: No refresh token in cookie");
                    return Unauthorized("Refresh token not found.");
                }

                var ipAddress = Request.HttpContext.Connection.RemoteIpAddress?.ToString() ?? "Unknown";
                var userAgent = Request.Headers.UserAgent.ToString();

                var result = await _authService.RefreshTokenAsync(refreshToken, ipAddress, userAgent);

                // Update refresh token in HttpOnly cookie
                if (!string.IsNullOrWhiteSpace(result.RefreshToken) && result.RefreshTokenExpires.HasValue)
                {
                    Response.Cookies.Append("refreshToken", result.RefreshToken, new CookieOptions
                    {
                        HttpOnly = true,
                        Secure = true,
                        SameSite = SameSiteMode.Lax,
                        Expires = result.RefreshTokenExpires
                    });
                }

                return Ok(result);
            }
            catch (UnauthorizedAccessException ex)
            {
                Response.Cookies.Delete("refreshToken");
                return Unauthorized(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Token refresh error: {ex.Message}");
                return StatusCode(500, "An error occurred during token refresh.");
            }
        }

        [HttpPost("logout")]
        [Authorize]
        public async Task<IActionResult> Logout([FromQuery] bool logoutAllDevices = false)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    _logger.LogWarning("Logout attempt failed: Invalid user ID claim");
                    return Unauthorized();
                }

                // Get current refresh token from cookie
                Request.Cookies.TryGetValue("refreshToken", out var refreshToken);

                await _authService.LogoutAsync(userId, refreshToken ?? string.Empty, logoutAllDevices);

                // Clear the refresh token cookie
                Response.Cookies.Delete("refreshToken");

                return Ok(new { message = logoutAllDevices ? "Logged out from all devices." : "Logged out successfully." });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Logout error: {ex.Message}");
                return StatusCode(500, "An error occurred during logout.");
            }
        }



        #region --- Utilities ---

        /// <summary>
        /// Hash a string using SHA256
        /// </summary>
        private static string HashObject(string input)
        {
            using var sha = SHA256.Create();
            var bytes = Encoding.UTF8.GetBytes(input);
            var hash = sha.ComputeHash(bytes);
            return Convert.ToHexString(hash);
        }

        #endregion
    }
}

