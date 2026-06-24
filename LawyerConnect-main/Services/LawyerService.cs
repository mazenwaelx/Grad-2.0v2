using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Models;
using LawyerConnect.Repositories;

namespace LawyerConnect.Services
{
    public class LawyerService : ILawyerService
    {
        private readonly ILawyerRepository _lawyerRepository;
        private readonly IUserRepository _userRepository;
        private readonly ISpecializationRepository _specializationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<LawyerService> _logger;

        public LawyerService(
            ILawyerRepository lawyerRepository, 
            IUserRepository userRepository,
            ISpecializationRepository specializationRepository,
            LawyerConnectDbContext context,
            ILogger<LawyerService> logger)
        {
            _lawyerRepository = lawyerRepository;
            _userRepository = userRepository;
            _specializationRepository = specializationRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<LawyerResponseDto> RegisterLawyerAsync(LawyerRegisterDto dto, int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Registering lawyer profile for user {userId}");

                // Validate user exists
                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                // Check if lawyer profile already exists
                var existingLawyer = await _lawyerRepository.GetByUserIdAsync(userId);
                if (existingLawyer != null)
                {
                    _logger.LogWarning($"Lawyer profile already exists for user {userId}");
                    throw new InvalidOperationException("Lawyer profile already exists for this user");
                }

                // Validate specializations
                if (dto.SpecializationIds.Any())
                {
                    foreach (var specializationId in dto.SpecializationIds)
                    {
                        var specialization = await _specializationRepository.GetByIdAsync(specializationId);
                        if (specialization == null)
                        {
                            _logger.LogWarning($"Specialization {specializationId} not found");
                            throw new ArgumentException($"Specialization with ID {specializationId} not found");
                        }
                    }
                }

                // Update user role to "Lawyer" if not already
                if (user.Role != "Lawyer" && user.Role != "Admin")
                {
                    user.Role = "Lawyer";
                    await _userRepository.UpdateAsync(user);
                    _logger.LogInformation($"Updated user {userId} role to Lawyer");
                }

                var lawyer = dto.ToLawyer(userId);
                await _lawyerRepository.AddAsync(lawyer);
                
                // Add specializations
                if (dto.SpecializationIds.Any())
                {
                    foreach (var specializationId in dto.SpecializationIds)
                    {
                        lawyer.Specializations ??= new List<LawyerSpecialization>();
                        lawyer.Specializations.Add(new LawyerSpecialization
                        {
                            LawyerId = lawyer.Id,
                            SpecializationId = specializationId
                        });
                    }
                    await _lawyerRepository.UpdateAsync(lawyer);

                    // Generate pricing matrix
                    var interactionTypes = _context.InteractionTypes.ToList();
                    foreach (var specId in dto.SpecializationIds)
                    {
                        foreach (var interactionType in interactionTypes)
                        {
                            var pricing = new LawyerPricing
                            {
                                LawyerId = lawyer.Id,
                                SpecializationId = specId,
                                InteractionTypeId = interactionType.Id,
                                Price = dto.BaseHourlyRate,
                                DurationMinutes = 60
                            };
                            _context.LawyerPricings.Add(pricing);
                        }
                    }
                    await _context.SaveChangesAsync();
                }
                
                await transaction.CommitAsync();

                // Reload the lawyer with the User relationship
                var createdLawyer = await _lawyerRepository.GetByIdAsync(lawyer.Id);
                if (createdLawyer == null)
                {
                    _logger.LogError($"Failed to retrieve created lawyer profile for user {userId}");
                    throw new InvalidOperationException("Failed to retrieve the created lawyer profile");
                }
                
                _logger.LogInformation($"Lawyer profile {createdLawyer.Id} created successfully for user {userId}");

                return createdLawyer.ToLawyerResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to register lawyer profile for user {userId}");
                throw;
            }
        }

        public async Task<LawyerResponseDto?> GetByIdAsync(int id)
        {
            try
            {
                _logger.LogInformation($"Retrieving lawyer {id}");

                var lawyer = await _lawyerRepository.GetByIdAsync(id);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {id} not found");
                    return null;
                }

                return lawyer.ToLawyerResponseDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve lawyer {id}");
                throw;
            }
        }

        public async Task<LawyerResponseDto?> GetByUserIdAsync(int userId)
        {
            try
            {
                _logger.LogInformation($"Retrieving lawyer profile for user {userId}");

                var lawyer = await _lawyerRepository.GetByUserIdAsync(userId);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer profile not found for user {userId}");
                    return null;
                }

                return lawyer.ToLawyerResponseDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve lawyer profile for user {userId}");
                throw;
            }
        }

        public async Task<IEnumerable<LawyerResponseDto>> GetPagedAsync(int page, int limit)
        {
            try
            {
                _logger.LogInformation($"Retrieving lawyers page {page}, limit {limit}");

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

                var lawyers = await _lawyerRepository.GetPagedAsync(page, limit);
                var lawyersList = lawyers.ToList();
                
                _logger.LogInformation($"Retrieved {lawyersList.Count} lawyers");

                return lawyersList.Select(l => l.ToLawyerResponseDto());
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve lawyers");
                throw;
            }
        }

        public async Task<List<LawyerResponseDto>> GetFeaturedLawyersAsync(int limit = 3)
        {
            try
            {
                _logger.LogInformation($"Retrieving top {limit} featured lawyers");

                // Get all verified lawyers with includes
                var allLawyers = await _lawyerRepository.GetAllAsync();
                var verifiedLawyers = allLawyers.Where(l => l.IsVerified).ToList();

                if (!verifiedLawyers.Any())
                {
                    _logger.LogInformation("No verified lawyers found");
                    return new List<LawyerResponseDto>();
                }

                // Calculate average rating for each lawyer
                var lawyersWithRatings = verifiedLawyers.Select(l => new
                {
                    Lawyer = l,
                    AvgRating = l.Reviews?.Any() == true 
                        ? (decimal)l.Reviews.Average(r => r.Rating) 
                        : 0m,
                    ReviewCount = l.Reviews?.Count ?? 0
                }).ToList();

                // Sort by: 1) Average rating (desc), 2) Review count (desc), 3) Created date (desc)
                var featured = lawyersWithRatings
                    .OrderByDescending(x => x.AvgRating)
                    .ThenByDescending(x => x.ReviewCount)
                    .ThenByDescending(x => x.Lawyer.CreatedAt)
                    .Take(limit)
                    .Select(x => x.Lawyer.ToLawyerResponseDto())
                    .ToList();

                _logger.LogInformation($"Retrieved {featured.Count} featured lawyers");
                return featured;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to retrieve featured lawyers");
                throw;
            }
        }

        public async Task<List<LawyerResponseDto>> SearchLawyersAsync(LawyerSearchDto filters)
        {
            try
            {
                _logger.LogInformation($"Searching lawyers with filters: page {filters.Page}, limit {filters.Limit}");

                // Validate pagination
                if (filters.Page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {filters.Page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (filters.Limit < 1 || filters.Limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {filters.Limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                var lawyers = await _lawyerRepository.GetPagedAsync(filters.Page, filters.Limit);
                
                // Filter by verification status (only verified lawyers)
                var results = lawyers.Where(l => l.IsVerified).ToList();

                // Filter by specialization
                if (filters.SpecializationId.HasValue)
                {
                    results = results.Where(l => l.Specializations?.Any(s => s.SpecializationId == filters.SpecializationId) ?? false).ToList();
                    _logger.LogInformation($"Filtered by specialization {filters.SpecializationId}: {results.Count} results");
                }

                // Filter by location (distance calculation)
                if (filters.Latitude.HasValue && filters.Longitude.HasValue && filters.RadiusKm.HasValue)
                {
                    results = results.Where(l => CalculateDistance(
                        filters.Latitude.Value, 
                        filters.Longitude.Value, 
                        l.Latitude, 
                        l.Longitude) <= filters.RadiusKm.Value).ToList();
                    _logger.LogInformation($"Filtered by location (radius {filters.RadiusKm}km): {results.Count} results");
                }

                // Filter by experience
                if (filters.MinExperienceYears.HasValue)
                {
                    results = results.Where(l => l.ExperienceYears >= filters.MinExperienceYears.Value).ToList();
                    _logger.LogInformation($"Filtered by experience (min {filters.MinExperienceYears} years): {results.Count} results");
                }

                // Filter by rating
                if (filters.MinRating.HasValue)
                {
                    results = results.Where(l => 
                    {
                        var avgRating = l.Reviews?.Any() == true 
                            ? (decimal)l.Reviews.Average(r => r.Rating) 
                            : 0;
                        return avgRating >= filters.MinRating.Value;
                    }).ToList();
                    _logger.LogInformation($"Filtered by rating (min {filters.MinRating}): {results.Count} results");
                }

                _logger.LogInformation($"Search completed: {results.Count} lawyers found");

                return results.Select(l => l.ToLawyerResponseDto()).ToList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to search lawyers");
                throw;
            }
        }

        public async Task VerifyLawyerAsync(int id)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Verifying lawyer {id}");

                var lawyer = await _lawyerRepository.GetByIdAsync(id);
                if (lawyer == null)
                {
                    _logger.LogWarning($"Lawyer {id} not found");
                    throw new ArgumentException($"Lawyer with ID {id} not found");
                }

                if (lawyer.IsVerified)
                {
                    _logger.LogInformation($"Lawyer {id} is already verified");
                    return;
                }

                lawyer.IsVerified = true;
                await _lawyerRepository.UpdateAsync(lawyer);

                await transaction.CommitAsync();

                _logger.LogInformation($"Lawyer {id} verified successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to verify lawyer {id}");
                throw;
            }
        }

        /// <summary>
        /// Calculate distance between two coordinates using Haversine formula (in kilometers)
        /// </summary>
        private decimal CalculateDistance(decimal lat1, decimal lon1, decimal lat2, decimal lon2)
        {
            const decimal R = 6371; // Earth's radius in kilometers
            
            var dLat = (lat2 - lat1) * (decimal)Math.PI / 180;
            var dLon = (lon2 - lon1) * (decimal)Math.PI / 180;
            
            var a = (decimal)Math.Sin((double)dLat / 2) * (decimal)Math.Sin((double)dLat / 2) +
                    (decimal)Math.Cos((double)lat1 * Math.PI / 180) * (decimal)Math.Cos((double)lat2 * Math.PI / 180) *
                    (decimal)Math.Sin((double)dLon / 2) * (decimal)Math.Sin((double)dLon / 2);
            
            var c = 2 * (decimal)Math.Atan2(Math.Sqrt((double)a), Math.Sqrt((double)(1 - a)));
            
            return R * c;
        }
    }
}

