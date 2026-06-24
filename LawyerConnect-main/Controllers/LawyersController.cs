using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class LawyersController : ControllerBase
    {
        private readonly ILawyerService _lawyerService;
        private readonly IPricingService _pricingService;
        private readonly ILogger<LawyersController> _logger;

        public LawyersController(
            ILawyerService lawyerService,
            IPricingService pricingService,
            ILogger<LawyersController> logger)
        {
            _lawyerService = lawyerService;
            _pricingService = pricingService;
            _logger = logger;
        }

        [HttpPost("register")]
        [Authorize] // user must be authenticated, userId extracted from token
        public async Task<ActionResult<LawyerResponseDto>> Register([FromBody] LawyerRegisterDto dto)
        {
            try
            {
                // Log the incoming request
                _logger.LogInformation($"Lawyer registration attempt - ExperienceYears: {dto.ExperienceYears}, Address: {dto.Address}, SpecializationIds count: {dto.SpecializationIds?.Count ?? 0}, BaseHourlyRate: {dto.BaseHourlyRate}");
                
                // Validate model state
                if (!ModelState.IsValid)
                {
                    var errors = ModelState.Values
                        .SelectMany(v => v.Errors)
                        .Select(e => e.ErrorMessage)
                        .ToList();
                    
                    _logger.LogWarning($"Lawyer registration validation failed: {string.Join(", ", errors)}");
                    return BadRequest(new { message = "Validation failed", errors });
                }

                // Extract userId from token
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    _logger.LogWarning("Unauthorized lawyer registration attempt - invalid user ID claim");
                    return Unauthorized();
                }

                // Check if user already has a lawyer profile
                var existingLawyer = await _lawyerService.GetByUserIdAsync(userId);
                if (existingLawyer != null)
                {
                    _logger.LogWarning($"Lawyer profile already exists for user {userId}");
                    return Conflict("Lawyer profile already exists for this user.");
                }

                var lawyer = await _lawyerService.RegisterLawyerAsync(dto, userId);
                _logger.LogInformation($"Lawyer profile created successfully for user {userId}");
                return CreatedAtAction(nameof(GetById), new { id = lawyer.Id }, lawyer);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during lawyer registration");
                return StatusCode(500, new { message = "Internal server error", details = ex.Message });
            }
        }

        [HttpGet("search")]
        [AllowAnonymous]
        public async Task<ActionResult<List<LawyerResponseDto>>> Search([FromQuery] LawyerSearchDto filters)
        {
            try
            {
                var results = await _lawyerService.SearchLawyersAsync(filters);
                return Ok(results);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error searching lawyers");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet]
        [AllowAnonymous]
        public async Task<ActionResult<IEnumerable<LawyerResponseDto>>> GetPaged([FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            var result = await _lawyerService.GetPagedAsync(page, limit);
            return Ok(result);
        }

        [HttpGet("featured")]
        [AllowAnonymous]
        public async Task<ActionResult<List<LawyerResponseDto>>> GetFeatured([FromQuery] int limit = 3)
        {
            try
            {
                var lawyers = await _lawyerService.GetFeaturedLawyersAsync(limit);
                return Ok(lawyers);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving featured lawyers");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("{id}")]
        [AllowAnonymous]
        public async Task<ActionResult<LawyerResponseDto>> GetById(int id)
        {
            var lawyer = await _lawyerService.GetByIdAsync(id);
            if (lawyer == null) return NotFound();
            return Ok(lawyer);
        }

        [HttpGet("me")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<ActionResult<LawyerResponseDto>> GetMyProfile()
        {
            var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
            {
                return Unauthorized();
            }

            var lawyer = await _lawyerService.GetByUserIdAsync(userId);
            if (lawyer == null) return NotFound("Lawyer profile not found for this user.");
            return Ok(lawyer);
        }

        [HttpPut("{id}/verify")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Verify(int id)
        {
            await _lawyerService.VerifyLawyerAsync(id);
            return NoContent();
        }

        [HttpPost("{lawyerId}/pricing")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<IActionResult> SetPricing(int lawyerId, [FromBody] LawyerPricingDto dto)
        {
            try
            {
                // Verify the lawyer belongs to the current user (unless admin)
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    return Unauthorized();
                }

                var lawyer = await _lawyerService.GetByIdAsync(lawyerId);
                if (lawyer == null)
                    return NotFound(new { message = "Lawyer not found" });

                if (lawyer.UserId != userId && !User.IsInRole("Admin"))
                    return Forbid();

                await _pricingService.SetPricingAsync(lawyerId, dto);
                return CreatedAtAction(nameof(GetPricing), new { lawyerId, specializationId = dto.SpecializationId, interactionTypeId = dto.InteractionTypeId }, dto);
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid pricing request");
                return BadRequest(new { message = ex.Message });
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogWarning(ex, "Pricing operation rejected");
                return BadRequest(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error setting pricing");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpGet("{lawyerId}/pricing")]
        [AllowAnonymous]
        public async Task<ActionResult<List<LawyerPricingDto>>> GetLawyerPricing(int lawyerId)
        {
            try
            {
                var pricing = await _pricingService.GetLawyerPricingAsync(lawyerId);
                return Ok(pricing);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving pricing");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("{lawyerId}/pricing/{specializationId}/{interactionTypeId}")]
        [AllowAnonymous]
        public async Task<ActionResult<LawyerPricingDto>> GetPricing(int lawyerId, int specializationId, int interactionTypeId)
        {
            try
            {
                var pricing = await _pricingService.GetPricingAsync(lawyerId, specializationId, interactionTypeId);
                if (pricing == null)
                    return NotFound(new { message = "Pricing not found" });

                return Ok(pricing);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving pricing");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpPut("{lawyerId}/pricing")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<IActionResult> UpdatePricing(int lawyerId, [FromBody] LawyerPricingDto dto)
        {
            try
            {
                // Verify the lawyer belongs to the current user (unless admin)
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    return Unauthorized();
                }

                var lawyer = await _lawyerService.GetByIdAsync(lawyerId);
                if (lawyer == null)
                    return NotFound(new { message = "Lawyer not found" });

                if (lawyer.UserId != userId && !User.IsInRole("Admin"))
                    return Forbid();

                await _pricingService.UpdatePricingAsync(lawyerId, dto);
                return NoContent();
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid pricing update request");
                return BadRequest(new { message = ex.Message });
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogWarning(ex, "Pricing update rejected");
                return BadRequest(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating pricing");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpDelete("{lawyerId}/pricing/{specializationId}/{interactionTypeId}")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<IActionResult> DeletePricing(int lawyerId, int specializationId, int interactionTypeId)
        {
            try
            {
                // Verify the lawyer belongs to the current user (unless admin)
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                {
                    return Unauthorized();
                }

                var lawyer = await _lawyerService.GetByIdAsync(lawyerId);
                if (lawyer == null)
                    return NotFound(new { message = "Lawyer not found" });

                if (lawyer.UserId != userId && !User.IsInRole("Admin"))
                    return Forbid();

                await _pricingService.DeletePricingAsync(lawyerId, specializationId, interactionTypeId);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting pricing");
                return StatusCode(500, new { message = ex.Message });
            }
        }
    }
}

