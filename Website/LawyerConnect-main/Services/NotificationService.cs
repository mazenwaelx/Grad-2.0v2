using LawyerConnect.DTOs;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using LawyerConnect.Repositories;

namespace LawyerConnect.Services
{
    public class NotificationService : INotificationService
    {
        private readonly INotificationRepository _notificationRepository;
        private readonly IUserRepository _userRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<NotificationService> _logger;

        private static readonly HashSet<string> ValidNotificationTypes = new()
        {
            "Booking", "Payment", "System", "Message", "Review"
        };

        public NotificationService(
            INotificationRepository notificationRepository,
            IUserRepository userRepository,
            LawyerConnectDbContext context,
            ILogger<NotificationService> logger)
        {
            _notificationRepository = notificationRepository;
            _userRepository = userRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<NotificationResponseDto> CreateNotificationAsync(int userId, NotificationCreateDto dto)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Creating notification for user {userId}");

                // Validate notification type
                if (!ValidNotificationTypes.Contains(dto.Type))
                {
                    _logger.LogWarning($"Invalid notification type: {dto.Type}");
                    throw new ArgumentException($"Invalid notification type. Valid types: {string.Join(", ", ValidNotificationTypes)}");
                }

                // Validate user exists
                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                // Validate input
                if (string.IsNullOrWhiteSpace(dto.Title))
                {
                    _logger.LogWarning("Notification title is empty");
                    throw new ArgumentException("Notification title cannot be empty");
                }

                if (string.IsNullOrWhiteSpace(dto.Message))
                {
                    _logger.LogWarning("Notification message is empty");
                    throw new ArgumentException("Notification message cannot be empty");
                }

                // Create notification using mapper
                var notification = dto.ToNotification(userId);
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Notification {notification.Id} created successfully for user {userId}");

                return notification.ToNotificationResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to create notification for user {userId}");
                throw;
            }
        }

        public async Task<List<NotificationResponseDto>> GetUserNotificationsAsync(int userId, int page = 1, int limit = 20)
        {
            try
            {
                _logger.LogInformation($"Retrieving notifications for user {userId}, page {page}, limit {limit}");

                // Validate pagination parameters
                if (page < 1)
                {
                    _logger.LogWarning($"Invalid page number: {page}");
                    throw new ArgumentException("Page number must be greater than 0");
                }

                if (limit < 1 || limit > 100)
                {
                    _logger.LogWarning($"Invalid limit: {limit}");
                    throw new ArgumentException("Limit must be between 1 and 100");
                }

                // Validate user exists
                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                var notifications = await _notificationRepository.GetUserNotificationsAsync(userId, page, limit);
                
                _logger.LogInformation($"Retrieved {notifications.Count} notifications for user {userId}");

                return notifications.ToNotificationResponseDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to retrieve notifications for user {userId}");
                throw;
            }
        }

        public async Task MarkAsReadAsync(int notificationId, int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Marking notification {notificationId} as read for user {userId}");

                var notification = await _notificationRepository.GetByIdAsync(notificationId);
                if (notification == null)
                {
                    _logger.LogWarning($"Notification {notificationId} not found");
                    throw new ArgumentException("Notification not found");
                }

                // Validate user owns this notification
                if (notification.UserId != userId)
                {
                    _logger.LogWarning($"User {userId} attempted to mark notification {notificationId} as read without permission");
                    throw new UnauthorizedAccessException("You do not have permission to modify this notification");
                }

                if (notification.IsRead)
                {
                    _logger.LogInformation($"Notification {notificationId} is already marked as read");
                    return;
                }

                notification.IsRead = true;
                await _notificationRepository.UpdateAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Notification {notificationId} marked as read successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to mark notification {notificationId} as read");
                throw;
            }
        }

        public async Task DeleteNotificationAsync(int notificationId, int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Deleting notification {notificationId} for user {userId}");

                var notification = await _notificationRepository.GetByIdAsync(notificationId);
                if (notification == null)
                {
                    _logger.LogWarning($"Notification {notificationId} not found");
                    throw new ArgumentException("Notification not found");
                }

                // Validate user owns this notification
                if (notification.UserId != userId)
                {
                    _logger.LogWarning($"User {userId} attempted to delete notification {notificationId} without permission");
                    throw new UnauthorizedAccessException("You do not have permission to delete this notification");
                }

                await _notificationRepository.DeleteAsync(notificationId);

                await transaction.CommitAsync();

                _logger.LogInformation($"Notification {notificationId} deleted successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to delete notification {notificationId}");
                throw;
            }
        }

        public async Task<int> GetUnreadCountAsync(int userId)
        {
            try
            {
                _logger.LogInformation($"Getting unread notification count for user {userId}");

                // Validate user exists
                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                var notifications = await _notificationRepository.GetUserNotificationsAsync(userId, 1, 1000);
                var unreadCount = notifications.Count(n => !n.IsRead);

                _logger.LogInformation($"User {userId} has {unreadCount} unread notifications");

                return unreadCount;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get unread count for user {userId}");
                throw;
            }
        }

        public async Task MarkAllAsReadAsync(int userId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Marking all notifications as read for user {userId}");

                // Validate user exists
                var user = await _userRepository.GetByIdAsync(userId);
                if (user == null)
                {
                    _logger.LogWarning($"User {userId} not found");
                    throw new ArgumentException("User not found");
                }

                var notifications = await _notificationRepository.GetUserNotificationsAsync(userId, 1, 1000);
                var unreadNotifications = notifications.Where(n => !n.IsRead).ToList();

                foreach (var notification in unreadNotifications)
                {
                    notification.IsRead = true;
                    await _notificationRepository.UpdateAsync(notification);
                }

                await transaction.CommitAsync();

                _logger.LogInformation($"Marked {unreadNotifications.Count} notifications as read for user {userId}");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to mark all notifications as read for user {userId}");
                throw;
            }
        }
    }
}
