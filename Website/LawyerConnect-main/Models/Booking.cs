namespace LawyerConnect.Models
{
    public class Booking
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public int LawyerId { get; set; }
        public int SpecializationId { get; set; }
        public int InteractionTypeId { get; set; }
        public decimal PriceSnapshot { get; set; }
        public int DurationSnapshot { get; set; }
        public DateTime Date { get; set; }
        public string Status { get; set; } = string.Empty; // Pending, Confirmed, Completed, Cancelled
        public string PaymentStatus { get; set; } = string.Empty; // Pending, Paid, Failed
        public DateTime CreatedAt { get; set; }

        // Navigation properties
        public User User { get; set; } = null!;
        public Lawyer Lawyer { get; set; } = null!;
        public Specialization Specialization { get; set; } = null!;
        public InteractionType InteractionType { get; set; } = null!;
        public PaymentSession? PaymentSession { get; set; }
        public Review? Review { get; set; }
        public ChatRoom? ChatRoom { get; set; }
    }
}