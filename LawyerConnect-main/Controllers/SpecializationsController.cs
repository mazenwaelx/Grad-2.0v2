using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class SpecializationsController : ControllerBase
    {
        private readonly ISpecializationService _specializationService;
        private readonly ILogger<SpecializationsController> _logger;

        public SpecializationsController(
            ISpecializationService specializationService,
            ILogger<SpecializationsController> logger)
        {
            _specializationService = specializationService;
            _logger = logger;
        }

        [HttpGet]
        public async Task<ActionResult<List<SpecializationDto>>> GetAll()
        {
            try
            {
                var specializations = await _specializationService.GetAllAsync();
                return Ok(specializations);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving specializations");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("{id}")]
        public async Task<ActionResult<SpecializationDto>> GetById(int id)
        {
            try
            {
                var specialization = await _specializationService.GetByIdAsync(id);
                if (specialization == null)
                    return NotFound(new { message = "Specialization not found" });

                return Ok(specialization);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving specialization");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpPost]
        [Authorize(Roles = "Admin")]
        public async Task<ActionResult<SpecializationDto>> Create([FromBody] SpecializationDto dto)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(dto.Name))
                    return BadRequest(new { message = "Specialization name is required" });

                var specialization = await _specializationService.CreateAsync(dto);
                return CreatedAtAction(nameof(GetById), new { id = specialization.Id }, specialization);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating specialization");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpPut("{id}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Update(int id, [FromBody] SpecializationDto dto)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(dto.Name))
                    return BadRequest(new { message = "Specialization name is required" });

                await _specializationService.UpdateAsync(id, dto);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating specialization");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpDelete("{id}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> Delete(int id)
        {
            try
            {
                await _specializationService.DeleteAsync(id);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting specialization");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }
    }
}
