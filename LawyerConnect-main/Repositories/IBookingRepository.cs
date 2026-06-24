using LawyerConnect.Models;


namespace LawyerConnect.Repositories
{
    public interface IBookingRepository
    {
        Task<Booking?> GetByIdAsync(int id);
        Task<IEnumerable<Booking>> GetUserBookingsAsync(int userId, int page = 1, int limit = 10);
        Task<IEnumerable<Booking>> GetLawyerBookingsAsync(int lawyerId, int page = 1, int limit = 10);
        Task<List<Booking>> GetLawyerBookingsForDateAsync(int lawyerId, DateTime date, int durationMinutes);
        Task<List<Booking>> GetAllAsync();
        Task AddAsync(Booking booking);
        Task UpdateAsync(Booking booking);

        // also we can add a deleteAsync booking authorized by adminUser or (user in Within a certain grace period)
    }
}

