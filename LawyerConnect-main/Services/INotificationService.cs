using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface INotificationService
    {
        Task<NotificationResponseDto> CreateNotificationAsync(int userId, NotificationCreateDto dto);
        Task<List<NotificationResponseDto>> GetUserNotificationsAsync(int userId, int page = 1, int limit = 20);
        Task MarkAsReadAsync(int notificationId, int userId);
        Task DeleteNotificationAsync(int notificationId, int userId);
        Task<int> GetUnreadCountAsync(int userId);
        Task MarkAllAsReadAsync(int userId);
    }
}
