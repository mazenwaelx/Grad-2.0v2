using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Repositories;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Services
{
    public class PricingService : IPricingService
    {
        private readonly IPricingRepository _pricingRepository;
        private readonly ILawyerRepository _lawyerRepository;
        private readonly ISpecializationRepository _specializationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<PricingService> _logger;

        public PricingService(
            IPricingRepository pricingRepository,
            ILawyerRepository lawyerRepository,
            ISpecializationRepository specializationRepository,
            LawyerConnectDbContext context,
            ILogger<PricingService> logger)
        {
            _pricingRepository = pricingRepository;
            _lawyerRepository = lawyerRepository;
            _specializationRepository = specializationRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<LawyerPricingDto?> GetPricingAsync(int lawyerId, int specializationId, int interactionTypeId)
        {
            try
            {
                _logger.LogInformation($"Retrieving pricing for lawyer {lawyerId}, specialization {specializationId}, interaction {interactionTypeId}");

                var pricing = await _pricingRepository.GetPricingAsync(lawyerId, specializationId, interactionTypeId);
                if (pricing == null)
                {
                    _logger.LogWarning($"Pricing not found for lawyer {lawyerId}, specialization {specializationId}, interaction {interactionTypeId}");
                    return null;
                }

                return pricing.ToLawyerPricingDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve pricing for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task<List<LawyerPricingDto>> GetLawyerPricingAsync(int lawyerId)
        {
            try
            {
                _logger.LogInformation($"Retrieving all pricing for lawyer {lawyerId}");

                // Validate lawyer exists
                var lawyer = await _lawyerRepository.GetByIdAsync(lawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} not found");
                    throw new ArgumentException($"Lawyer with ID {lawyerId} not found");
                }

                var pricings = await _pricingRepository.GetLawyerPricingAsync(lawyerId);
                
                _logger.LogInformation($"Retrieved {pricings.Count} pricing entries for lawyer {lawyerId}");

                return pricings.ToLawyerPricingDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve pricing for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task SetPricingAsync(int lawyerId, LawyerPricingDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Setting pricing for lawyer {lawyerId}");

                // Validate lawyer exists
                var lawyer = await _lawyerRepository.GetByIdAsync(lawyerId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} not found");
                    throw new ArgumentException($"Lawyer with ID {lawyerId} not found");
                }

                // Validate specialization exists
                var specialization = await _specializationRepository.GetByIdAsync(dto.SpecializationId);
                if (specialization == null)
                {
                    _logger.LogWarning($"Specialization {dto.SpecializationId} not found");
                    throw new ArgumentException($"Specialization with ID {dto.SpecializationId} not found");
                }

                // Validate interaction type exists
                var interactionTypeExists = await _context.InteractionTypes
                    .AnyAsync(it => it.Id == dto.InteractionTypeId);
                if (!interactionTypeExists)
                {
                    _logger.LogWarning($"Interaction type {dto.InteractionTypeId} not found");
                    throw new ArgumentException($"Interaction type with ID {dto.InteractionTypeId} not found");
                }

                // Validate lawyer has this specialization
                var lawyerHasSpecialization = await _context.LawyerSpecializations
                    .AnyAsync(ls => ls.LawyerId == lawyerId && ls.SpecializationId == dto.SpecializationId);
                if (!lawyerHasSpecialization)
                {
                    _logger.LogWarning($"Lawyer {lawyerId} does not have specialization {dto.SpecializationId}");
                    throw new InvalidOperationException("Cannot set pricing for a specialization not assigned to this lawyer");
                }

                // Validate price
                if (dto.Price <= 0)
                {
                    _logger.LogWarning($"Invalid price: {dto.Price}");
                    throw new ArgumentException("Price must be greater than 0");
                }

                // Validate duration
                if (dto.DurationMinutes <= 0)
                {
                    _logger.LogWarning($"Invalid duration: {dto.DurationMinutes}");
                    throw new ArgumentException("Duration must be greater than 0 minutes");
                }

                // Check if pricing already exists
                var existingPricing = await _pricingRepository.GetPricingAsync(
                    lawyerId, dto.SpecializationId, dto.InteractionTypeId);

                if (existingPricing != null)
                {
                    _logger.LogWarning($"Pricing already exists for lawyer {lawyerId}, specialization {dto.SpecializationId}, interaction {dto.InteractionTypeId}");
                    throw new InvalidOperationException("Pricing for this specialization and interaction type already exists. Use update instead.");
                }

                var pricing = dto.ToLawyerPricing(lawyerId);
                await _pricingRepository.AddAsync(pricing);

                await transaction.CommitAsync();

                _logger.LogInformation($"Pricing set successfully for lawyer {lawyerId}");
            }
            catch (DbUpdateException ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Database constraint violation while setting pricing for lawyer {lawyerId}");
                throw new InvalidOperationException("Unable to save pricing due to invalid related data. Please verify specialization and interaction type.");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to set pricing for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task UpdatePricingAsync(int lawyerId, LawyerPricingDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Updating pricing for lawyer {lawyerId}");

                // Validate interaction type exists
                var interactionTypeExists = await _context.InteractionTypes
                    .AnyAsync(it => it.Id == dto.InteractionTypeId);
                if (!interactionTypeExists)
                {
                    _logger.LogWarning($"Interaction type {dto.InteractionTypeId} not found");
                    throw new ArgumentException($"Interaction type with ID {dto.InteractionTypeId} not found");
                }

                var pricing = await _pricingRepository.GetPricingAsync(
                    lawyerId, dto.SpecializationId, dto.InteractionTypeId);

                if (pricing == null)
                {
                    _logger.LogWarning($"Pricing not found for lawyer {lawyerId}, specialization {dto.SpecializationId}, interaction {dto.InteractionTypeId}");
                    throw new ArgumentException("Pricing not found");
                }

                // Validate price
                if (dto.Price <= 0)
                {
                    _logger.LogWarning($"Invalid price: {dto.Price}");
                    throw new ArgumentException("Price must be greater than 0");
                }

                // Validate duration
                if (dto.DurationMinutes <= 0)
                {
                    _logger.LogWarning($"Invalid duration: {dto.DurationMinutes}");
                    throw new ArgumentException("Duration must be greater than 0 minutes");
                }

                pricing.UpdateFromDto(dto);
                await _pricingRepository.UpdateAsync(pricing);

                await transaction.CommitAsync();

                _logger.LogInformation($"Pricing updated successfully for lawyer {lawyerId}");
            }
            catch (DbUpdateException ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Database constraint violation while updating pricing for lawyer {lawyerId}");
                throw new InvalidOperationException("Unable to update pricing due to invalid related data.");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to update pricing for lawyer {lawyerId}");
                throw;
            }
        }

        public async Task DeletePricingAsync(int lawyerId, int specializationId, int interactionTypeId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Deleting pricing for lawyer {lawyerId}, specialization {specializationId}, interaction {interactionTypeId}");

                var pricing = await _pricingRepository.GetPricingAsync(lawyerId, specializationId, interactionTypeId);
                if (pricing == null)
                {
                    _logger.LogWarning($"Pricing not found for lawyer {lawyerId}, specialization {specializationId}, interaction {interactionTypeId}");
                    throw new ArgumentException("Pricing not found");
                }

                await _pricingRepository.DeleteAsync(lawyerId, specializationId, interactionTypeId);

                await transaction.CommitAsync();

                _logger.LogInformation($"Pricing deleted successfully for lawyer {lawyerId}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to delete pricing for lawyer {lawyerId}");
                throw;
            }
        }
    }
}
