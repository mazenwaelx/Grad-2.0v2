using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using LawyerConnect.DTOs;
using LawyerConnect.Mappers;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using Microsoft.IdentityModel.Tokens;
using LawyerConnect.Data;


namespace LawyerConnect.Services
{
    public class AuthService : IAuthService
    {
        private readonly IUserRepository _userRepository;
        private readonly IRefreshTokenRepository _refreshTokenRepository;
        private readonly IConfiguration _config;
        private readonly ILogger<AuthService> _logger;
        private readonly LawyerConnectDbContext _context;

        public AuthService(
            IUserRepository userRepository,
            IRefreshTokenRepository refreshTokenRepository,
            IConfiguration config,
            ILogger<AuthService> logger , 
            LawyerConnectDbContext context)
        {
            _userRepository = userRepository;
            _refreshTokenRepository = refreshTokenRepository;
            _config = config;
            _logger = logger;
            _context = context;
        }

        /// <summary>
        /// Register a new user with email, password, and role
        /// </summary>
        public async Task<AuthResponseDto> RegisterAsync(RegisterRequestDto dto, string passwordHash, string role)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                // Create user entity
                var user = new User
                {
                    Email = dto.User.Email,
                    PasswordHash = passwordHash,
                    FullName = dto.User.FullName,
                    Phone = dto.User.Phone,
                    City = dto.User.City,
                    Role = role,
                    CreatedAt = DateTime.UtcNow
                };

                // Add user to database
                await _userRepository.AddAsync(user);

                // If registering as lawyer, create lawyer profile within the same transaction
                if (role == "Lawyer" && dto.Lawyer != null)
                {
                    // Validate specialization IDs exist
                    var specializationRepository = _context.Set<Specialization>();
                    var validSpecializationIds = new List<int>();
                    
                    foreach (var specId in dto.Lawyer.SpecializationIds)
                    {
                        var exists = await specializationRepository.FindAsync(specId);
                        if (exists != null)
                        {
                            validSpecializationIds.Add(specId);
                        }
                        else
                        {
                            _logger.LogWarning($"Invalid specialization ID {specId} provided during lawyer registration for user {user.Email}");
                        }
                    }

                    // Create lawyer profile
                    var lawyer = new Lawyer
                    {
                        UserId = user.Id,
                        ExperienceYears = dto.Lawyer.ExperienceYears,
                        Address = dto.Lawyer.Address,
                        Latitude = dto.Lawyer.Latitude,
                        Longitude = dto.Lawyer.Longitude,
                        IsVerified = false,
                        CreatedAt = DateTime.UtcNow
                    };

                    // Add lawyer to database
                    _context.Lawyers.Add(lawyer);
                    await _context.SaveChangesAsync(); // Save to get lawyer.Id

                    // Add lawyer specializations
                    if (validSpecializationIds.Any())
                    {
                        var lawyerSpecializations = validSpecializationIds.Select(specId => new LawyerSpecialization
                        {
                            LawyerId = lawyer.Id,
                            SpecializationId = specId
                        }).ToList();

                        _context.LawyerSpecializations.AddRange(lawyerSpecializations);
                        await _context.SaveChangesAsync();
                    }

                    // Generate default pricing matrix for each assigned specialization
                    // against all interaction types so the lawyer is immediately bookable.
                    var interactionTypes = _context.InteractionTypes.ToList();
                    var basePrice = dto.Lawyer.BaseHourlyRate > 0 ? dto.Lawyer.BaseHourlyRate : 500m;

                    if (interactionTypes.Any() && validSpecializationIds.Any())
                    {
                        var pricingRows = new List<LawyerPricing>();
                        foreach (var specId in validSpecializationIds)
                        {
                            foreach (var interactionType in interactionTypes)
                            {
                                pricingRows.Add(new LawyerPricing
                                {
                                    LawyerId = lawyer.Id,
                                    SpecializationId = specId,
                                    InteractionTypeId = interactionType.Id,
                                    Price = basePrice,
                                    DurationMinutes = 60
                                });
                            }
                        }

                        _context.LawyerPricings.AddRange(pricingRows);
                        await _context.SaveChangesAsync();
                    }

                    _logger.LogInformation($"Lawyer profile created for user {user.Id} with {validSpecializationIds.Count} specializations");
                }

                // Commit the transaction
                await transaction.CommitAsync();
                _logger.LogInformation($"User {user.Id} ({user.Email}) registered successfully with role {role}");

                // Generate access token on registration so authenticated follow-up actions work.
                var accessToken = GenerateJwt(user.Id, user.Email, user.Role, out var expiresAt);

                return new AuthResponseDto
                {
                    Token = accessToken,
                    ExpiresAt = expiresAt,
                    User = user.ToUserResponseDto()
                };
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Registration failed for email {dto.User.Email}");
                throw;
            }
        }

        /// <summary>
        /// Login user with email and password, returns access token and refresh token
        /// </summary>
        public async Task<AuthResponseDto> LoginAsync(LoginDto dto, string ipAddress, string userAgent)
        {
            var user = await _userRepository.GetByEmailAsync(dto.Email);
            if (user == null)
            {
                _logger.LogWarning($"Login attempt failed: User not found for email {dto.Email}");
                throw new UnauthorizedAccessException("Invalid credentials.");
            }

            var hashedInput = HashObject(dto.Password);
            if (!string.Equals(user.PasswordHash, hashedInput, StringComparison.Ordinal))
            {
                _logger.LogWarning($"Login attempt failed: Invalid password for user {user.Id} ({user.Email})");
                throw new UnauthorizedAccessException("Invalid credentials.");
            }

            // Generate tokens
            var accessToken = GenerateJwt(user.Id, user.Email, user.Role, out var expiresAt);
            var refreshToken = GenerateRefreshToken();
            var hashedRefreshToken = HashObject(refreshToken);

            // Get refresh token expiration from config
            var refreshTokenExpirationDays = int.TryParse(_config["Jwt:RefreshTokenExpirationDays"], out var days) ? days : 7;
            var refreshExpires = DateTime.UtcNow.AddDays(refreshTokenExpirationDays);

            // Store refresh token in database
            await _refreshTokenRepository.AddAsync(new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = user.Id,
                TokenHash = hashedRefreshToken,
                ExpiresAt = refreshExpires,
                CreatedAt = DateTime.UtcNow,
                IpAddress = ipAddress,
                UserAgent = userAgent
            });

            _logger.LogInformation($"User {user.Id} ({user.Email}) logged in successfully from IP {ipAddress}");

            return new AuthResponseDto
            {
                Token = accessToken,
                ExpiresAt = expiresAt,
                User = user.ToUserResponseDto(),
                RefreshToken = refreshToken, // Return refresh token to set in cookie
                RefreshTokenExpires = refreshExpires
            };
        }

        /// <summary>
        /// Refresh access token using refresh token
        /// Implements token rotation and sliding expiration (< 3 days extends to 7 days)
        /// </summary>
        public async Task<AuthResponseDto> RefreshTokenAsync(string refreshToken, string ipAddress, string userAgent)
        {
            if (string.IsNullOrWhiteSpace(refreshToken))
            {
                _logger.LogWarning("Refresh attempt failed: No refresh token provided");
                throw new UnauthorizedAccessException("Refresh token not found.");
            }

            var hashedToken = HashObject(refreshToken);
            var storedToken = await _refreshTokenRepository.GetByTokenHashAsync(hashedToken);

            if (storedToken == null)
            {
                _logger.LogWarning("Refresh attempt failed: Invalid refresh token hash");
                throw new UnauthorizedAccessException("Invalid refresh token.");
            }

            // Replay attack detection
            if (storedToken.Revoked)
            {
                _logger.LogError($"SECURITY ALERT: Replay attack detected for user {storedToken.UserId}. Revoked token used. All sessions revoked.");
                await _refreshTokenRepository.RevokeAllAsync(storedToken.UserId, RefreshTokenRevokeReason.ReplayDetected);
                throw new UnauthorizedAccessException("Refresh token has been revoked. All sessions logged out for security.");
            }

            // Check expiration
            if (storedToken.ExpiresAt < DateTime.UtcNow)
            {
                _logger.LogWarning($"Refresh attempt failed: Token expired for user {storedToken.UserId}");
                throw new UnauthorizedAccessException("Refresh token expired.");
            }

            // Check if token is close to expiration (sliding expiration)
            var timeUntilExpiry = storedToken.ExpiresAt - DateTime.UtcNow;
            var shouldRotate = timeUntilExpiry.TotalDays < 3; // Rotate if less than 3 days left

            // Generate new access token
            var newAccessToken = GenerateJwt(storedToken.UserId, storedToken.User.Email, storedToken.User.Role, out var expiresAt);

            // Generate new refresh token (rotation)
            var newRefreshToken = GenerateRefreshToken();
            var newHashedRefreshToken = HashObject(newRefreshToken);
            DateTime newRefreshExpires;

            if (shouldRotate)
            {
                var refreshTokenExpirationDays = int.TryParse(_config["Jwt:RefreshTokenExpirationDays"], out var days) ? days : 7;
                newRefreshExpires = DateTime.UtcNow.AddDays(refreshTokenExpirationDays);
                _logger.LogInformation($"Token rotation triggered for user {storedToken.UserId}: Token expiring soon (< 3 days)");
            }
            else
            {
                newRefreshExpires = storedToken.ExpiresAt;
            }

            // Create new refresh token record
            var newTokenRecord = new RefreshToken
            {
                Id = Guid.NewGuid(),
                UserId = storedToken.UserId,
                TokenHash = newHashedRefreshToken,
                ExpiresAt = newRefreshExpires,
                CreatedAt = DateTime.UtcNow,
                IpAddress = ipAddress,
                UserAgent = userAgent
            };

            await _refreshTokenRepository.AddAsync(newTokenRecord);
            storedToken.ReplacedByTokenId = newTokenRecord.Id;
            await _refreshTokenRepository.RevokeAsync(storedToken, RefreshTokenRevokeReason.Rotation);

            _logger.LogInformation($"User {storedToken.UserId} token refreshed successfully");

            return new AuthResponseDto
            {
                Token = newAccessToken,
                ExpiresAt = expiresAt,
                User = storedToken.User.ToUserResponseDto(),
                RefreshToken = newRefreshToken,
                RefreshTokenExpires = newRefreshExpires
            };
        }

        /// <summary>
        /// Logout user by revoking refresh token(s)
        /// </summary>
        public async Task LogoutAsync(int userId, string refreshToken, bool logoutAllDevices)
        {
            // Revoke current refresh token if provided
            if (!string.IsNullOrWhiteSpace(refreshToken))
            {
                var hashedToken = HashObject(refreshToken);
                var storedToken = await _refreshTokenRepository.GetByTokenHashAsync(hashedToken);

                if (storedToken != null)
                {
                    await _refreshTokenRepository.RevokeAsync(storedToken, RefreshTokenRevokeReason.Logout);
                }
            }

            // Multi-device logout: revoke all tokens
            if (logoutAllDevices)
            {
                _logger.LogInformation($"User {userId} logged out from all devices");
                await _refreshTokenRepository.RevokeAllAsync(userId, RefreshTokenRevokeReason.LogoutAll);
            }
            else
            {
                _logger.LogInformation($"User {userId} logged out from current device");
            }
        }

        /// <summary>
        /// Get user by ID
        /// </summary>
        public async Task<UserResponseDto> GetUserByIdAsync(int userId)
        {
            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null)
            {
                throw new KeyNotFoundException($"User with ID {userId} not found.");
            }

            return user.ToUserResponseDto();
        }

        #region --- Private Utility Methods ---

        /// <summary>
        /// Generate a secure refresh token (32 bytes, base64 encoded)
        /// </summary>
        private string GenerateRefreshToken()
        {
            var bytes = new byte[32];
            using var rng = RandomNumberGenerator.Create();
            rng.GetBytes(bytes);
            return Convert.ToBase64String(bytes);
        }

        /// <summary>
        /// Generate JWT access token with user claims
        /// </summary>
        private string GenerateJwt(int userId, string email, string role, out DateTime expiresAt)
        {
            var key = _config["Jwt:Key"] ?? throw new InvalidOperationException("JWT Key missing.");
            var issuer = _config["Jwt:Issuer"];
            var audience = _config["Jwt:Audience"];
            var expiresMinutes = int.TryParse(_config["Jwt:ExpiresMinutes"], out var exp) ? exp : 30;

            var securityKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key));
            var credentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);

            var claims = new List<Claim>
            {
                new Claim(ClaimTypes.NameIdentifier, userId.ToString()),
                new Claim(ClaimTypes.Email, email),
                new Claim(ClaimTypes.Role, role)
            };

            expiresAt = DateTime.UtcNow.AddMinutes(expiresMinutes);

            var token = new JwtSecurityToken(
                issuer: issuer,
                audience: audience,
                claims: claims,
                expires: expiresAt,
                signingCredentials: credentials);

            return new JwtSecurityTokenHandler().WriteToken(token);
        }

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
