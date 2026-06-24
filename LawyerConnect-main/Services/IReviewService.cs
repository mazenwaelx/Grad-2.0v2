using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IReviewService
    {
        Task<ReviewResponseDto> CreateReviewAsync(int userId, ReviewCreateDto dto);
        Task<List<ReviewResponseDto>> GetLawyerReviewsAsync(int lawyerId, int page = 1, int limit = 10);
        Task<List<ReviewResponseDto>> GetFeaturedReviewsAsync(int limit = 3);
        Task<decimal> GetLawyerAverageRatingAsync(int lawyerId);
        Task DeleteReviewAsync(int id, int adminUserId);
    }
}
