using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
    public class ChatRoomRepository : IChatRoomRepository
    {
        private readonly LawyerConnectDbContext _context;

        public ChatRoomRepository(LawyerConnectDbContext context)
        {
            _context = context;
        }

        public async Task<ChatRoom?> GetByIdAsync(int id)
        {
            return await _context.ChatRooms.Include(cr => cr.Messages).FirstOrDefaultAsync(cr => cr.Id == id);
        }

        public async Task<ChatRoom?> GetByBookingIdAsync(int bookingId)
        {
            return await _context.ChatRooms.Include(cr => cr.Messages).FirstOrDefaultAsync(cr => cr.BookingId == bookingId);
        }

        public async Task AddAsync(ChatRoom chatRoom)
        {
            await _context.ChatRooms.AddAsync(chatRoom);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(ChatRoom chatRoom)
        {
            _context.ChatRooms.Update(chatRoom);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(int id)
        {
            var chatRoom = await GetByIdAsync(id);
            if (chatRoom != null)
            {
                _context.ChatRooms.Remove(chatRoom);
                await _context.SaveChangesAsync();
            }
        }
    }
}
