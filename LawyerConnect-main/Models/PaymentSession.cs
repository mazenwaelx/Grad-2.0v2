namespace LawyerConnect.Models
{
    public class PaymentSession
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public decimal Amount { get; set; }
        public string Status { get; set; } = string.Empty; // Pending, Success, Failed
        public string Provider { get; set; } = string.Empty;
        public string ProviderSessionId { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }

        // Navigation properties
        public Booking Booking { get; set; } = null!;
    }
}