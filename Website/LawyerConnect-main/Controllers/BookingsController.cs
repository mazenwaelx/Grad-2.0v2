using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BookingsController : ControllerBase
    {
        private readonly IBookingService _bookingService;
        private readonly ILawyerService _lawyerService;
        private readonly ILogger<BookingsController> _logger;

        public BookingsController(IBookingService bookingService, ILawyerService lawyerService, ILogger<BookingsController> logger)
        {
            _bookingService = bookingService;
            _lawyerService = lawyerService;
            _logger = logger;
        }

        [HttpPost]
        [Authorize]
        public async Task<ActionResult<BookingResponseDto>> CreateBooking([FromBody] BookingCreateDto dto)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var booking = await _bookingService.CreateBookingAsync(userId, dto);
                return CreatedAtAction(nameof(GetBooking), new { id = booking.Id }, booking);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating booking");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpGet("{id}")]
        [Authorize]
        public async Task<ActionResult<BookingResponseDto>> GetBooking(int id)
        {
            try
            {
                var booking = await _bookingService.GetBookingByIdAsync(id);
                if (booking == null)
                    return NotFound();

                return Ok(booking);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving booking");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("user")]
        [Authorize]
        public async Task<ActionResult<List<BookingResponseDto>>> GetUserBookings([FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var bookings = await _bookingService.GetUserBookingsAsync(userId, page, limit);
                return Ok(bookings);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving user bookings");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("lawyer")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<ActionResult<List<BookingResponseDto>>> GetLawyerBookings([FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var lawyerProfile = await _lawyerService.GetByUserIdAsync(userId);
                
                if (lawyerProfile == null)
                    return BadRequest("User is not associated with a lawyer profile.");

                var bookings = await _bookingService.GetLawyerBookingsAsync(lawyerProfile.Id, page, limit);
                return Ok(bookings);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving lawyer bookings");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpPut("{id}/status")]
        [Authorize(Roles = "Lawyer,Admin")]
        public async Task<IActionResult> UpdateBookingStatus(int id, [FromBody] string status)
        {
            try
            {
                await _bookingService.UpdateBookingStatusAsync(id, status);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating booking status");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpDelete("{id}")]
        [Authorize]
        public async Task<IActionResult> CancelBooking(int id)
        {
            try
            {
                await _bookingService.CancelBookingAsync(id);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error cancelling booking");
                return StatusCode(500, new { message = ex.Message });
            }
        }
    }
}
