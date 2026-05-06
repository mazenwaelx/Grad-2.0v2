using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IAdminService
    {
        Task<List<UserResponseDto>> GetAllUsersAsync(int page = 1, int limit = 20);
        Task<List<LawyerResponseDto>> GetPendingLawyersAsync(int page = 1, int limit = 20);
        Task VerifyLawyerAsync(int lawyerId);
        Task RejectLawyerAsync(int lawyerId, string reason);
        Task SuspendUserAsync(int userId);
        Task UnsuspendUserAsync(int userId);
        Task<List<BookingResponseDto>> GetAllBookingsAsync(int page = 1, int limit = 20);
        Task<List<PaymentSessionResponseDto>> GetAllPaymentsAsync(int page = 1, int limit = 20);
    }
}
