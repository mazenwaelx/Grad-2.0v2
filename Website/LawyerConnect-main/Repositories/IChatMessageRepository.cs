using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface IChatMessageRepository
    {
        Task<ChatMessage?> GetByIdAsync(int id);
        Task<List<ChatMessage>> GetChatMessagesAsync(int chatRoomId, int page = 1, int limit = 50);
        Task<List<ChatMessage>> GetMessagesByBookingIdAsync(int bookingId, int page = 1, int limit = 50);
        Task AddAsync(ChatMessage message);
        Task UpdateAsync(ChatMessage message);
        Task DeleteAsync(int id);
    }
}
