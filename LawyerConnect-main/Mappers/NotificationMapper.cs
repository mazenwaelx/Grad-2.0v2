using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class NotificationMapper
    {
        /// <summary>
        /// Convert NotificationCreateDto to Notification entity
        /// </summary>
        public static Notification ToNotification(this NotificationCreateDto dto, int userId)
        {
            return new Notification
            {
                UserId = userId,
                Title = dto.Title,
                Message = dto.Message,
                Type = dto.Type,
                IsRead = false,
                CreatedAt = DateTime.UtcNow
            };
        }

        /// <summary>
        /// Convert Notification entity to NotificationResponseDto
        /// </summary>
        public static NotificationResponseDto ToNotificationResponseDto(this Notification notification)
        {
            return new NotificationResponseDto
            {
                Id = notification.Id,
                UserId = notification.UserId,
                Title = notification.Title,
                Message = notification.Message,
                Type = notification.Type,
                IsRead = notification.IsRead,
                CreatedAt = notification.CreatedAt
            };
        }

        /// <summary>
        /// Convert list of Notification entities to list of NotificationResponseDto
        /// </summary>
        public static List<NotificationResponseDto> ToNotificationResponseDtoList(this IEnumerable<Notification> notifications)
        {
            return notifications.Select(n => n.ToNotificationResponseDto()).ToList();
        }
    }
}
