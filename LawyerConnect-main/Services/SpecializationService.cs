using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Repositories;

namespace LawyerConnect.Services
{
    public class SpecializationService : ISpecializationService
    {
        private readonly ISpecializationRepository _repository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<SpecializationService> _logger;

        public SpecializationService(
            ISpecializationRepository repository,
            LawyerConnectDbContext context,
            ILogger<SpecializationService> logger)
        {
            _repository = repository;
            _context = context;
            _logger = logger;
        }

        public async Task<List<SpecializationDto>> GetAllAsync()
        {
            try
            {
                _logger.LogInformation("Retrieving all specializations");

                var specializations = await _repository.GetAllAsync();
                
                _logger.LogInformation($"Retrieved {specializations.Count} specializations");

                return specializations.ToSpecializationDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve specializations");
                throw;
            }
        }

        public async Task<SpecializationDto?> GetByIdAsync(int id)
        {
            try
            {
                _logger.LogInformation($"Retrieving specialization {id}");

                var specialization = await _repository.GetByIdAsync(id);
                if (specialization == null)
                {
                    _logger.LogWarning($"Specialization {id} not found");
                    return null;
                }

                return specialization.ToSpecializationDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve specialization {id}");
                throw;
            }
        }

        public async Task<SpecializationDto> CreateAsync(SpecializationDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Creating specialization: {dto.Name}");

                // Validate input
                if (string.IsNullOrWhiteSpace(dto.Name))
                {
                    _logger.LogWarning("Specialization name is empty");
                    throw new ArgumentException("Specialization name cannot be empty");
                }

                // Check for duplicate name
                var allSpecializations = await _repository.GetAllAsync();
                if (allSpecializations.Any(s => s.Name.Equals(dto.Name, StringComparison.OrdinalIgnoreCase)))
                {
                    _logger.LogWarning($"Specialization with name '{dto.Name}' already exists");
                    throw new InvalidOperationException($"Specialization with name '{dto.Name}' already exists");
                }

                var specialization = dto.ToSpecialization();
                await _repository.AddAsync(specialization);

                await transaction.CommitAsync();

                _logger.LogInformation($"Specialization {specialization.Id} created successfully");

                return specialization.ToSpecializationDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, "Failed to create specialization");
                throw;
            }
        }

        public async Task UpdateAsync(int id, SpecializationDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Updating specialization {id}");

                var specialization = await _repository.GetByIdAsync(id);
                if (specialization == null)
                {
                    _logger.LogWarning($"Specialization {id} not found");
                    throw new ArgumentException($"Specialization with ID {id} not found");
                }

                // Validate input
                if (string.IsNullOrWhiteSpace(dto.Name))
                {
                    _logger.LogWarning("Specialization name is empty");
                    throw new ArgumentException("Specialization name cannot be empty");
                }

                // Check for duplicate name (excluding current specialization)
                var allSpecializations = await _repository.GetAllAsync();
                if (allSpecializations.Any(s => s.Id != id && s.Name.Equals(dto.Name, StringComparison.OrdinalIgnoreCase)))
                {
                    _logger.LogWarning($"Specialization with name '{dto.Name}' already exists");
                    throw new InvalidOperationException($"Specialization with name '{dto.Name}' already exists");
                }

                specialization.UpdateFromDto(dto);
                await _repository.UpdateAsync(specialization);

                await transaction.CommitAsync();

                _logger.LogInformation($"Specialization {id} updated successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to update specialization {id}");
                throw;
            }
        }

        public async Task DeleteAsync(int id)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Deleting specialization {id}");

                var specialization = await _repository.GetByIdAsync(id);
                if (specialization == null)
                {
                    _logger.LogWarning($"Specialization {id} not found");
                    throw new ArgumentException($"Specialization with ID {id} not found");
                }

                // Check if specialization is in use
                if (specialization.Lawyers?.Any() == true)
                {
                    _logger.LogWarning($"Cannot delete specialization {id} - it is assigned to {specialization.Lawyers.Count} lawyers");
                    throw new InvalidOperationException($"Cannot delete specialization '{specialization.Name}' because it is assigned to {specialization.Lawyers.Count} lawyer(s)");
                }

                await _repository.DeleteAsync(id);

                await transaction.CommitAsync();

                _logger.LogInformation($"Specialization {id} deleted successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to delete specialization {id}");
                throw;
            }
        }
    }
}
