using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface IReviewRepository
    {
        Task<Review?> GetByIdAsync(int id);
        Task<Review?> GetByBookingIdAsync(int bookingId);
        Task<List<Review>> GetLawyerReviewsAsync(int lawyerId, int page = 1, int limit = 10);
        Task AddAsync(Review review);
        Task UpdateAsync(Review review);
        Task DeleteAsync(Review review);
    }
}
