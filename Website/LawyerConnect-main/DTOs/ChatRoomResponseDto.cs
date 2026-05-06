namespace LawyerConnect.DTOs
{
    public class ChatRoomResponseDto
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public bool IsArchived { get; set; }
        public DateTime CreatedAt { get; set; }
        public int MessageCount { get; set; }
    }
}
