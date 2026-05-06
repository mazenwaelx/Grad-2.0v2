namespace LawyerConnect.DTOs
{
    public class BookingResponseDto
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public int LawyerId { get; set; }
        public int SpecializationId { get; set; }
        public int InteractionTypeId { get; set; }
        public decimal PriceSnapshot { get; set; }
        public int DurationSnapshot { get; set; }
        public DateTime Date { get; set; }
        public string Status { get; set; } = "";
        public string PaymentStatus { get; set; } = "";
        public DateTime CreatedAt { get; set; }
        
        // Navigation properties for display
        public string? LawyerName { get; set; }
        public string? UserName { get; set; }
        public string? SpecializationName { get; set; }
        public string? InteractionTypeName { get; set; }
    }
}

