namespace LawyerConnect.DTOs
{
    public class ReviewResponseDto
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public int UserId { get; set; }
        public int LawyerId { get; set; }
        public int Rating { get; set; }
        public string Comment { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        
        // Navigation properties for display
        public string? UserName { get; set; }
        public string? LawyerName { get; set; }
    }
}
