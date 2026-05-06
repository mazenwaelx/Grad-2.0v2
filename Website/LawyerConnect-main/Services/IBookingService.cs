using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IBookingService
    {
        Task<BookingResponseDto> CreateBookingAsync(int userId, BookingCreateDto dto);
        Task<BookingResponseDto?> GetBookingByIdAsync(int id);
        Task<List<BookingResponseDto>> GetUserBookingsAsync(int userId, int page = 1, int limit = 10);
        Task<List<BookingResponseDto>> GetLawyerBookingsAsync(int lawyerId, int page = 1, int limit = 10);
        Task UpdateBookingStatusAsync(int id, string status);
        Task CancelBookingAsync(int id);
        Task CompleteBookingAsync(int id);
    }
}
