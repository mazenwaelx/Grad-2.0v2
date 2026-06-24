namespace LawyerConnect.DTOs
{
    public class PaymentSessionResponseDto
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public decimal Amount { get; set; }
        public string Status { get; set; } = string.Empty;
        public string Provider { get; set; } = string.Empty;
        public string ProviderSessionId { get; set; } = string.Empty;
        public string? CheckoutUrl { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
