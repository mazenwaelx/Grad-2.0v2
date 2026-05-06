using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Repositories;

namespace LawyerConnect.Services
{
    public class UserService : IUserService
    {
        private readonly IUserRepository _userRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<UserService> _logger;

        public UserService(
            IUserRepository userRepository,
            LawyerConnectDbContext context,
            ILogger<UserService> logger)
        {
            _userRepository = userRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<UserResponseDto> RegisterUserAsync(UserRegisterDto dto, string passwordHash, string role)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Registering new user with email {dto.Email}");

                // Validate input
                if (string.IsNullOrWhiteSpace(dto.Email))
                {
                    _logger.LogWarning("User registration failed: Email is empty");
                    throw new ArgumentException("Email cannot be empty");
                }

                if (string.IsNullOrWhiteSpace(dto.FullName))
                {
                    _logger.LogWarning("User registration failed: Full name is empty");
                    throw new ArgumentException("Full name cannot be empty");
                }

                if (string.IsNullOrWhiteSpace(passwordHash))
                {
                    _logger.LogWarning("User registration failed: Password hash is empty");
                    throw new ArgumentException("Password hash cannot be empty");
                }

                // Validate role
                var validRoles = new[] { "User", "Lawyer", "Admin" };
                if (!validRoles.Contains(role))
                {
                    _logger.LogWarning($"User registration failed: Invalid role '{role}'");
                    throw new ArgumentException($"Invalid role. Valid roles: {string.Join(", ", validRoles)}");
                }

                // Check for duplicate email
                var existingUser = await _userRepository.GetByEmailAsync(dto.Email);
                if (existingUser != null)
                {
                    _logger.LogWarning($"User registration failed: Email {dto.Email} already exists");
                    throw new InvalidOperationException($"User with email {dto.Email} already exists");
                }

                var user = dto.ToUser(passwordHash, role);
                await _userRepository.AddAsync(user);

                await transaction.CommitAsync();

                _logger.LogInformation($"User {user.Id} registered successfully with email {dto.Email}");

                return user.ToUserResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to register user with email {dto.Email}");
                throw;
            }
        }

        public async Task UpdateUserRoleAsync(int userId, string newRole)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Updating role for user {userId} to {newRole}");

                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException($"User with ID {userId} not found");
                }

                // Validate role
                var validRoles = new[] { "User", "Lawyer", "Admin" };
                if (!validRoles.Contains(newRole))
                {
                    _logger.LogWarning($"Invalid role: {newRole}");
                    throw new ArgumentException($"Invalid role. Valid roles: {string.Join(", ", validRoles)}");
                }

                if (user.Role == newRole)
                {
                    _logger.LogInformation($"User {userId} already has role {newRole}");
                    return;
                }

                var oldRole = user.Role;
                user.Role = newRole;
                await _userRepository.UpdateAsync(user);

                await transaction.CommitAsync();

                _logger.LogInformation($"User {userId} role updated from {oldRole} to {newRole}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to update role for user {userId}");
                throw;
            }
        }

        public async Task<UserResponseDto?> GetByIdAsync(int id)
        {
            try
            {
                _logger.LogInformation($"Retrieving user {id}");

                var user = await _userRepository.GetByIdAsync(id);
                if (user == null)
                {
                    _logger.LogWarning($"User {id} not found");
                    return null;
                }

                return user.ToUserResponseDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve user {id}");
                throw;
            }
        }

        public async Task<IEnumerable<UserResponseDto>> GetPagedAsync(int page, int limit)
        {
            try
            {
                _logger.LogInformation($"Retrieving users page {page}, limit {limit}");

                // Validate pagination
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var users = await _userRepository.GetPagedAsync(page, limit);
                var usersList = users.ToList();

                _logger.LogInformation($"Retrieved {usersList.Count} users");

                return usersList.Select(u => u.ToUserResponseDto());
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve users");
                throw;
            }
        }
    }
}

