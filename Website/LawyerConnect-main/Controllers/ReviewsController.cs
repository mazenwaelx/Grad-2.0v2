using System.Security.Claims;
using LawyerConnect.DTOs;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LawyerConnect.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ReviewsController : ControllerBase
    {
        private readonly IReviewService _reviewService;
        private readonly ILogger<ReviewsController> _logger;

        public ReviewsController(IReviewService reviewService, ILogger<ReviewsController> logger)
        {
            _reviewService = reviewService;
            _logger = logger;
        }

        [HttpPost]
        [Authorize]
        public async Task<ActionResult<ReviewResponseDto>> CreateReview([FromBody] ReviewCreateDto dto)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var userId))
                    return Unauthorized();

                var review = await _reviewService.CreateReviewAsync(userId, dto);
                return CreatedAtAction(nameof(GetLawyerReviews), new { lawyerId = dto.LawyerId }, review);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating review");
                return StatusCode(500, new { message = ex.Message });
            }
        }

        [HttpGet("lawyer/{lawyerId}")]
        [AllowAnonymous]
        public async Task<ActionResult<List<ReviewResponseDto>>> GetLawyerReviews(int lawyerId, [FromQuery] int page = 1, [FromQuery] int limit = 10)
        {
            try
            {
                var reviews = await _reviewService.GetLawyerReviewsAsync(lawyerId, page, limit);
                return Ok(reviews);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving lawyer reviews");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("lawyer/{lawyerId}/rating")]
        [AllowAnonymous]
        public async Task<ActionResult<decimal>> GetLawyerAverageRating(int lawyerId)
        {
            try
            {
                var rating = await _reviewService.GetLawyerAverageRatingAsync(lawyerId);
                return Ok(new { averageRating = rating });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving lawyer rating");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpGet("featured")]
        [AllowAnonymous]
        public async Task<ActionResult<List<ReviewResponseDto>>> GetFeaturedReviews([FromQuery] int limit = 3)
        {
            try
            {
                var reviews = await _reviewService.GetFeaturedReviewsAsync(limit);
                return Ok(reviews);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving featured reviews");
                return StatusCode(500, new { message = "Internal server error" });
            }
        }

        [HttpDelete("{id}")]
        [Authorize(Roles = "Admin")]
        public async Task<ActionResult> DeleteReview(int id)
        {
            try
            {
                var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
                if (string.IsNullOrWhiteSpace(userIdClaim) || !int.TryParse(userIdClaim, out var adminUserId))
                    return Unauthorized();

                await _reviewService.DeleteReviewAsync(id, adminUserId);
                return NoContent();
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Unauthorized attempt to delete review {ReviewId}", id);
                return Forbid();
            }
            catch (ArgumentException ex)
            {
                _logger.LogWarning(ex, "Review not found: {ReviewId}", id);
                return NotFound(new { message = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting review {ReviewId}", id);
                return StatusCode(500, new { message = "Internal server error" });
            }
        }
    }
}
