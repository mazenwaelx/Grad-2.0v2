using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/chat")]
    [Authorize]
    public class ChatController : ControllerBase
    {
        private readonly IChatService _chatService;
        private readonly ILogger<ChatController> _logger;

        public ChatController(IChatService chatService, ILogger<ChatController> logger)
        {
            _chatService = chatService;
            _logger = logger;
        }

        [HttpGet("{bookingId}")]
        public async Task<ActionResult<ChatRoomResponseDto>> GetChatRoom(int bookingId)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var chatRoom = await _chatService.GetChatRoomAsync(bookingId, userId);
                return Ok(chatRoom);
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Unauthorized access to chat room");
                return Forbid();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving chat room");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpPost("{bookingId}/messages")]
        public async Task<ActionResult<ChatMessageResponseDto>> SendMessage(int bookingId, [FromBody] string message)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var chatMessage = await _chatService.SendMessageAsync(bookingId, userId, message);
                return CreatedAtAction(nameof(GetMessages), new { bookingId }, chatMessage);
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Unauthorized message send attempt");
                return Forbid();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending message");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpGet("{bookingId}/messages")]
        public async Task<ActionResult<List<ChatMessageResponseDto>>> GetMessages(int bookingId, [FromQuery] int page = 1, [FromQuery] int limit = 50)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var messages = await _chatService.GetMessagesAsync(bookingId, userId, page, limit);
                return Ok(messages);
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Unauthorized access to messages");
                return Forbid();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving messages");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpDelete("{bookingId}")]
        public async Task<IActionResult> ArchiveChat(int bookingId)
        {
            try
            {
                await _chatService.ArchiveChatRoomAsync(bookingId);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error archiving chat");
                return StatusCode(500, new { message = ex.Message });
            }
        }
    }
}
