using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize(Roles = "Admin")]
    public class AdminController : ControllerBase
    {
        private readonly IAdminService _adminService;
        private readonly ILogger<AdminController> _logger;

        public AdminController(IAdminService adminService, ILogger<AdminController> logger)
        {
            _adminService = adminService;
            _logger = logger;
        }

        [HttpGet("users")]
        public async Task<ActionResult<List<UserResponseDto>>> GetAllUsers([FromQuery] int page = 1, [FromQuery] int limit = 20)
        {
            try
            {
                var users = await _adminService.GetAllUsersAsync(page, limit);
                return Ok(users);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving all users");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("lawyers/pending")]
        public async Task<ActionResult<List<LawyerResponseDto>>> GetPendingLawyers([FromQuery] int page = 1, [FromQuery] int limit = 20)
        {
            try
            {
                var lawyers = await _adminService.GetPendingLawyersAsync(page, limit);
                return Ok(lawyers);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving pending lawyers");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpPut("lawyers/{id}/verify")]
        public async Task<IActionResult> VerifyLawyer(int id)
        {
            try
            {
                await _adminService.VerifyLawyerAsync(id);
                return Ok(new { message = "Lawyer verified successfully" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error verifying lawyer");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpPut("lawyers/{id}/reject")]
        public async Task<IActionResult> RejectLawyer(int id, [FromBody] RejectLawyerDto dto)
        {
            try
            {
                await _adminService.RejectLawyerAsync(id, dto.Reason);
                return Ok(new { message = "Lawyer rejected successfully" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error rejecting lawyer");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpPut("users/{id}/suspend")]
        public async Task<IActionResult> SuspendUser(int id)
        {
            try
            {
                await _adminService.SuspendUserAsync(id);
                return Ok(new { message = "User suspended successfully" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error suspending user");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpPut("users/{id}/unsuspend")]
        public async Task<IActionResult> UnsuspendUser(int id)
        {
            try
            {
                await _adminService.UnsuspendUserAsync(id);
                return Ok(new { message = "User unsuspended successfully" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error unsuspending user");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpGet("bookings")]
        public async Task<ActionResult<List<BookingResponseDto>>> GetAllBookings([FromQuery] int page = 1, [FromQuery] int limit = 20)
        {
            try
            {
                var bookings = await _adminService.GetAllBookingsAsync(page, limit);
                return Ok(bookings);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving all bookings");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("payments")]
        public async Task<ActionResult<List<PaymentSessionResponseDto>>> GetAllPayments([FromQuery] int page = 1, [FromQuery] int limit = 20)
        {
            try
            {
                var payments = await _adminService.GetAllPaymentsAsync(page, limit);
                return Ok(payments);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving all payments");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }
    }
}
