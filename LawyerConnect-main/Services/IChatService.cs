using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IChatService
    {
        Task<ChatRoomResponseDto> GetChatRoomAsync(int bookingId, int userId);
        Task<ChatMessageResponseDto> SendMessageAsync(int bookingId, int senderId, string message);
        Task<List<ChatMessageResponseDto>> GetMessagesAsync(int bookingId, int userId, int page = 1, int limit = 50);
        Task ArchiveChatRoomAsync(int bookingId);
    }
}
