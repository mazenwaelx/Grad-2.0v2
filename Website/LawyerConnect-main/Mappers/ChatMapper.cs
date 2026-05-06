using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class ChatMapper
    {
        public static ChatMessage ToChatMessage(this string message, int chatRoomId, int senderId)
        {
            return new ChatMessage
            {
                ChatRoomId = chatRoomId,
                SenderId = senderId,
                Message = message,
                SentAt = DateTime.UtcNow
            };
        }

        public static ChatMessageResponseDto ToChatMessageResponseDto(this ChatMessage message)
        {
            return new ChatMessageResponseDto
            {
                Id = message.Id,
                ChatRoomId = message.ChatRoomId,
                SenderId = message.SenderId,
                SenderName = message.Sender?.FullName ?? string.Empty,
                Message = message.Message,
                SentAt = message.SentAt
            };
        }

        public static List<ChatMessageResponseDto> ToChatMessageResponseDtoList(this IEnumerable<ChatMessage> messages)
        {
            return messages.Select(m => m.ToChatMessageResponseDto()).ToList();
        }

        public static ChatRoomResponseDto ToChatRoomResponseDto(this ChatRoom chatRoom)
        {
            return new ChatRoomResponseDto
            {
                Id = chatRoom.Id,
                BookingId = chatRoom.BookingId,
                CreatedAt = chatRoom.CreatedAt,
                IsArchived = chatRoom.IsArchived,
                MessageCount = chatRoom.Messages?.Count ?? 0
            };
        }
    }
}
