using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PaymentsController : ControllerBase
    {
        private readonly IPaymentService _paymentService;
        private readonly ILogger<PaymentsController> _logger;

        public PaymentsController(IPaymentService paymentService, ILogger<PaymentsController> logger)
        {
            _paymentService = paymentService;
            _logger = logger;
        }

        [HttpPost("create-session")]
        [Authorize]
        public async Task<ActionResult<PaymentSessionResponseDto>> CreateSession([FromBody] PaymentDto dto)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var session = await _paymentService.CreateSessionAsync(userId, dto.BookingId, dto.Amount);
                return CreatedAtAction(nameof(GetPaymentSession), new { id = session.Id }, session);
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid argument for payment session creation");
                return BadRequest(new { message = ex.Message });
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Unauthorized payment session creation attempt");
                return Forbid(ex.Message);
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogWarning(ex, "Invalid operation for payment session creation");
                return Conflict(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating payment session for booking {BookingId}", dto.BookingId);
                return StatusCode(500, new { message = "An error occurred while creating the payment session." });
            }
        }

        [HttpPost("confirm")]
        [Authorize]
        public async Task<ActionResult<PaymentSessionResponseDto>> Confirm([FromBody] ConfirmPaymentDto dto)
        {
            try
            {
                var session = await _paymentService.ConfirmPaymentAsync(dto.SessionId);
                return Ok(session);
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid argument for payment confirmation");
                return BadRequest(new { message = ex.Message });
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogWarning(ex, "Invalid operation for payment confirmation");
                return Conflict(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error confirming payment for session {SessionId}", dto.SessionId);
                return StatusCode(500, new { message = "An error occurred while confirming the payment." });
            }
        }

        [HttpGet("{id}")]
        [Authorize]
        public async Task<ActionResult<PaymentSessionResponseDto>> GetPaymentSession(int id)
        {
            try
            {
                var session = await _paymentService.GetPaymentSessionAsync(id);
                if (session == null)
                    return NotFound(new { message = "Payment session not found." });

                return Ok(session);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving payment session {SessionId}", id);
                return StatusCode(500, new { message = "An error occurred while retrieving the payment session." });
            }
        }

        [HttpGet("user")]
        [Authorize]
        public async Task<ActionResult<List<PaymentSessionResponseDto>>> GetUserPaymentSessions([FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                if (page < 1) page = 1;
                if (limit < 1 || limit > 100) limit = 10;

                var sessions = await _paymentService.GetUserPaymentSessionsAsync(userId, page, limit);
                return Ok(sessions);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving user payment sessions");
                return StatusCode(500, new { message = "An error occurred while retrieving payment sessions." });
            }
        }

        [HttpPost("refund")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> RefundPayment([FromBody] RefundPaymentDto dto)
        {
            try
            {
                await _paymentService.RefundPaymentAsync(dto.SessionId);
                return NoContent();
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Invalid argument for payment refund");
                return BadRequest(new { message = ex.Message });
            }
            catch (InvalidOperationException ex)
            {
                _logger.LogWarning(ex, "Invalid operation for payment refund");
                return Conflict(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error refunding payment for session {SessionId}", dto.SessionId);
                return StatusCode(500, new { message = "An error occurred while refunding the payment." });
            }
        }

        [HttpPost("webhook/{provider}")]
        [AllowAnonymous]
        public async Task<IActionResult> HandleWebhook(string provider, [FromBody] object payload)
        {
            try
            {
                var payloadString = payload.ToString() ?? string.Empty;
                await _paymentService.HandleWebhookAsync(provider, payloadString);
                return Ok();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error handling webhook from provider {Provider}", provider);
                return StatusCode(500, new { message = "An error occurred while processing the webhook." });
            }
        }
    }

    public class ConfirmPaymentDto
    {
        public int SessionId { get; set; }
        public string ProviderSessionId { get; set; } = string.Empty;
    }

    public class RefundPaymentDto
    {
        public int SessionId { get; set; }
        public string Reason { get; set; } = string.Empty;
    }
}

