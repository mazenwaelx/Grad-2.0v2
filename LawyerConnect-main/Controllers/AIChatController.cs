using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/ai-chat")]
    public class AIChatController : ControllerBase
    {
        private readonly IAIChatService _aiChatService;
        private readonly ILogger<AIChatController> _logger;

        public AIChatController(IAIChatService aiChatService, ILogger<AIChatController> logger)
        {
            _aiChatService = aiChatService;
            _logger = logger;
        }

        [HttpPost("message")]
        [Authorize]
        public async Task<ActionResult<AIChatResponseDto>> SendMessage([FromBody] AIChatRequestDto request)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized(new { message = "User ID not found in token" });

                var response = await _aiChatService.SendMessageAsync(request.Message, userId.ToString(), request.ChatId);
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing AI chat message");
                return StatusCode(500, new { message = "Failed to process message. Please try again." });
            }
        }

        [HttpGet("chats")]
        [Authorize]
        public async Task<ActionResult<List<AIChatHistoryDto>>> GetUserChats()
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized(new { message = "User ID not found in token" });

                var chats = await _aiChatService.GetUserChatsAsync(userId.ToString());
                return Ok(chats);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving AI chat history");
                return StatusCode(500, new { message = "Failed to retrieve chat history" });
            }
        }

        [HttpGet("chats/{chatId}/messages")]
        [Authorize]
        public async Task<ActionResult<List<AIChatMessageDto>>> GetChatMessages(string chatId)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized(new { message = "User ID not found in token" });

                var messages = await _aiChatService.GetChatMessagesAsync(chatId, userId.ToString());
                return Ok(messages);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving chat messages");
                return StatusCode(500, new { message = "Failed to retrieve messages" });
            }
        }

        [HttpDelete("chats/{chatId}")]
        [Authorize]
        public async Task<IActionResult> DeleteChat(string chatId)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized(new { message = "User ID not found in token" });

                await _aiChatService.DeleteChatAsync(chatId, userId.ToString());
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting chat");
                return StatusCode(500, new { message = "Failed to delete chat" });
            }
        }

        [HttpPost("upload")]
        [Authorize]
        public async Task<ActionResult<FileUploadResponseDto>> UploadFile([FromForm] IFormFile file)
        {
            try
            {
                if (file == null || file.Length == 0)
                    return BadRequest(new { message = "No file provided" });

                var response = await _aiChatService.UploadFileAsync(file);
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error uploading file");
                return StatusCode(500, new { message = "Failed to upload file" });
            }
        }

        [HttpGet("files")]
        [Authorize]
        public async Task<ActionResult<List<UploadedFileDto>>> GetUploadedFiles()
        {
            try
            {
                var files = await _aiChatService.GetUploadedFilesAsync();
                return Ok(files);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving files");
                return StatusCode(500, new { message = "Failed to retrieve files" });
            }
        }

        [HttpDelete("files/{fileHash}")]
        [Authorize]
        public async Task<IActionResult> DeleteFile(string fileHash)
        {
            try
            {
                await _aiChatService.DeleteFileAsync(fileHash);
                return NoContent();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting file");
                return StatusCode(500, new { message = "Failed to delete file" });
            }
        }

        [HttpGet("health")]
        public async Task<ActionResult> CheckHealth()
        {
            try
            {
                var isHealthy = await _aiChatService.CheckHealthAsync();
                if (isHealthy)
                    return Ok(new { status = "healthy" });
                else
                    return StatusCode(503, new { status = "unavailable" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Health check failed");
                return StatusCode(503, new { status = "error" });
            }
        }
    }
}
