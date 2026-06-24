using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Services
{
    public class ChatService : IChatService
    {
        private readonly IChatRoomRepository _chatRoomRepository;
        private readonly IChatMessageRepository _chatMessageRepository;
        private readonly IBookingRepository _bookingRepository;
        private readonly IUserRepository _userRepository;
        private readonly INotificationRepository _notificationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger<ChatService> _logger;

        public ChatService(
            IChatRoomRepository chatRoomRepository,
            IChatMessageRepository chatMessageRepository,
            IBookingRepository bookingRepository,
            IUserRepository userRepository,
            INotificationRepository notificationRepository,
            LawyerConnectDbContext context,
            ILogger<ChatService> logger)
        {
            _chatRoomRepository = chatRoomRepository;
            _chatMessageRepository = chatMessageRepository;
            _bookingRepository = bookingRepository;
            _userRepository = userRepository;
            _notificationRepository = notificationRepository;
            _context = context;
            _logger = logger;
        }

        public async Task<ChatRoomResponseDto> GetChatRoomAsync(int bookingId, int userId)
        {
            try
            {
                var chatRoom = await _chatRoomRepository.GetByBookingIdAsync(bookingId);
                if (chatRoom == null)
                {
                    _logger.LogWarning($"Chat room not found for booking {bookingId}");
                    throw new ArgumentException("Chat room not found");
                }

                // Validate user has access to this chat room
                var booking = await _bookingRepository.GetByIdAsync(bookingId);
                if (booking == null)
                {
                    _logger.LogWarning($"Booking {bookingId} not found");
                    throw new ArgumentException("Booking not found");
                }

                // Check if user is either the client or the lawyer
                var lawyer = await _context.Lawyers.FirstOrDefaultAsync(l => l.Id == booking.LawyerId);
                if (booking.UserId != userId && lawyer?.UserId != userId)
                {
                    _logger.LogWarning($"User {userId} attempted to access chat room for booking {bookingId} without permission");
                    throw new UnauthorizedAccessException("You do not have access to this chat room");
                }

                return chatRoom.ToChatRoomResponseDto();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get chat room for booking {bookingId}");
                throw;
            }
        }

        public async Task<ChatMessageResponseDto> SendMessageAsync(int bookingId, int senderId, string message)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                _logger.LogInformation($"Sending message in booking {bookingId} from user {senderId}");

                // Validate message content
                if (string.IsNullOrWhiteSpace(message))
                {
                    _logger.LogWarning($"Message send failed: Empty message from user {senderId}");
                    throw new ArgumentException("Message cannot be empty");
                }

                if (message.Length > 1000)
                {
                    _logger.LogWarning($"Message send failed: Message too long from user {senderId}");
                    throw new ArgumentException("Message cannot exceed 1000 characters");
                }

                // Validate chat room exists
                var chatRoom = await _chatRoomRepository.GetByBookingIdAsync(bookingId);
                if (chatRoom == null)
                {
                    _logger.LogWarning($"Message send failed: Chat room not found for booking {bookingId}");
                    throw new ArgumentException("Chat room not found");
                }

                // Validate chat room is not archived
                if (chatRoom.IsArchived)
                {
                    _logger.LogWarning($"Message send failed: Chat room {chatRoom.Id} is archived");
                    throw new InvalidOperationException("Cannot send messages to archived chat room");
                }

                // Validate sender exists
                var sender = await _userRepository.GetByIdAsync(senderId);
                if (sender == null)
                {
                    _logger.LogWarning($"Message send failed: Sender {senderId} not found");
                    throw new ArgumentException("Sender not found");
                }

                // Validate sender has access to this chat room
                var booking = await _bookingRepository.GetByIdAsync(bookingId);
                if (booking == null)
                {
                    _logger.LogWarning($"Message send failed: Booking {bookingId} not found");
                    throw new ArgumentException("Booking not found");
                }

                var lawyer = await _context.Lawyers.FirstOrDefaultAsync(l => l.Id == booking.LawyerId);
                if (booking.UserId != senderId && lawyer?.UserId != senderId)
                {
                    _logger.LogWarning($"Message send failed: User {senderId} does not have access to booking {bookingId}");
                    throw new UnauthorizedAccessException("You do not have access to this chat room");
                }

                // Create message using mapper
                var chatMessage = message.ToChatMessage(chatRoom.Id, senderId);
                await _chatMessageRepository.AddAsync(chatMessage);

                // Determine recipient
                int recipientId = senderId == booking.UserId ? lawyer!.UserId : booking.UserId;

                // Create notification for recipient
                var notification = new Notification
                {
                    UserId = recipientId,
                    Title = "New Message",
                    Message = $"{sender.FullName} sent you a message",
                    Type = "Message",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Message sent successfully in chat room {chatRoom.Id} by user {senderId}");

                return chatMessage.ToChatMessageResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to send message in booking {bookingId} from user {senderId}");
                throw;
            }
        }

        public async Task<List<ChatMessageResponseDto>> GetMessagesAsync(int bookingId, int userId, int page = 1, int limit = 50)
        {
            try
            {
                // Validate user has access to this chat room
                var booking = await _bookingRepository.GetByIdAsync(bookingId);
                if (booking == null)
                {
                    _logger.LogWarning($"Get messages failed: Booking {bookingId} not found");
                    throw new ArgumentException("Booking not found");
                }

                var lawyer = await _context.Lawyers.FirstOrDefaultAsync(l => l.Id == booking.LawyerId);
                if (booking.UserId != userId && lawyer?.UserId != userId)
                {
                    _logger.LogWarning($"Get messages failed: User {userId} does not have access to booking {bookingId}");
                    throw new UnauthorizedAccessException("You do not have access to this chat room");
                }

                var messages = await _chatMessageRepository.GetMessagesByBookingIdAsync(bookingId, page, limit);
                return messages.ToChatMessageResponseDtoList();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to get messages for booking {bookingId}");
                throw;
            }
        }

        public async Task ArchiveChatRoomAsync(int bookingId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var chatRoom = await _chatRoomRepository.GetByBookingIdAsync(bookingId);
                if (chatRoom == null)
                {
                    _logger.LogWarning($"Archive failed: Chat room not found for booking {bookingId}");
                    throw new ArgumentException("Chat room not found");
                }

                if (chatRoom.IsArchived)
                {
                    _logger.LogInformation($"Chat room {chatRoom.Id} is already archived");
                    return;
                }

                chatRoom.IsArchived = true;
                await _chatRoomRepository.UpdateAsync(chatRoom);

                await transaction.CommitAsync();

                _logger.LogInformation($"Chat room {chatRoom.Id} for booking {bookingId} archived successfully");
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to archive chat room for booking {bookingId}");
                throw;
            }
        }
    }
}
