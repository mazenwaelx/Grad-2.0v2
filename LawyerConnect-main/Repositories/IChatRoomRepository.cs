using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface IChatRoomRepository
    {
        Task<ChatRoom?> GetByIdAsync(int id);
        Task<ChatRoom?> GetByBookingIdAsync(int bookingId);
        Task AddAsync(ChatRoom chatRoom);
        Task UpdateAsync(ChatRoom chatRoom);
        Task DeleteAsync(int id);
    }
}
