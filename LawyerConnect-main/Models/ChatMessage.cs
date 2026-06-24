namespace LawyerConnect.Models
{
    public class ChatMessage
    {
        public int Id { get; set; }
        public int ChatRoomId { get; set; }
        public int SenderId { get; set; }
        public string Message { get; set; } = string.Empty;
        public DateTime SentAt { get; set; }

        // Navigation properties
        public ChatRoom ChatRoom { get; set; } = null!;
        public User Sender { get; set; } = null!;
    }
}
