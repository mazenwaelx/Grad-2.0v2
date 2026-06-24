using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface INotificationRepository
    {
        Task<Notification?> GetByIdAsync(int id);
        Task<List<Notification>> GetUserNotificationsAsync(int userId, int page = 1, int limit = 20);
        Task AddAsync(Notification notification);
        Task UpdateAsync(Notification notification);
        Task DeleteAsync(int id);
    }
}
