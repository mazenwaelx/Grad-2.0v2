using LawyerConnect.Data;
using LawyerConnect.DTOs;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InteractionTypesController : ControllerBase
    {
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<InteractionTypesController> _logger;

        public InteractionTypesController(LawyerConnectDbContext context, ILogger<InteractionTypesController> logger)
        {
            _context = context;
            _logger = logger;
        }

        [HttpGet]
        [AllowAnonymous]
        public async Task<ActionResult<IEnumerable<InteractionTypeDto>>> GetAll()
        {
            try
            {
                var types = await _context.InteractionTypes
                    .Select(it => new InteractionTypeDto
                    {
                        Id = it.Id,
                        Name = it.Name,
                        Description = null
                    })
                    .ToListAsync();
                
                return Ok(types);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving interaction types");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }
    }
}
