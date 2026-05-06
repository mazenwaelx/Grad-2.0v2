namespace LawyerConnect.Models
{
    public class ChatRoom
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public bool IsArchived { get; set; } = false;
        public DateTime CreatedAt { get; set; }

        // Navigation properties
        public Booking Booking { get; set; } = null!;
        public List<ChatMessage>? Messages { get; set; }
    }
}
