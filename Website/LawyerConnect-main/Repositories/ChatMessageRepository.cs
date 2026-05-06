using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
    public class ChatMessageRepository : IChatMessageRepository
    {
        private readonly LawyerConnectDbContext _context;

        public ChatMessageRepository(LawyerConnectDbContext context)
        {
            _context = context;
        }

        public async Task<ChatMessage?> GetByIdAsync(int id)
        {
            return await _context.ChatMessages.Include(cm => cm.Sender).FirstOrDefaultAsync(cm => cm.Id == id);
        }

        public async Task<List<ChatMessage>> GetChatMessagesAsync(int chatRoomId, int page = 1, int limit = 50)
        {
            return await _context.ChatMessages
                .Where(cm => cm.ChatRoomId == chatRoomId)
                .Include(cm => cm.Sender)
                .OrderBy(cm => cm.SentAt)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();
        }

        public async Task<List<ChatMessage>> GetMessagesByBookingIdAsync(int bookingId, int page = 1, int limit = 50)
        {
            var chatRoom = await _context.ChatRooms
                .FirstOrDefaultAsync(cr => cr.BookingId == bookingId);

            if (chatRoom == null)
                return new List<ChatMessage>();

            return await _context.ChatMessages
                .Include(cm => cm.Sender)
                .Where(cm => cm.ChatRoomId == chatRoom.Id)
                .OrderBy(cm => cm.SentAt)
                .Skip((page - 1) * limit)
                .Take(limit)
                .ToListAsync();
        }

        public async Task AddAsync(ChatMessage message)
        {
            await _context.ChatMessages.AddAsync(message);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(ChatMessage message)
        {
            _context.ChatMessages.Update(message);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(int id)
        {
            var message = await GetByIdAsync(id);
            if (message != null)
            {
                _context.ChatMessages.Remove(message);
                await _context.SaveChangesAsync();
            }
        }
    }
}
