namespace LawyerConnect.Models
{
    public class Review
    {
        public int Id { get; set; }
        public int BookingId { get; set; }
        public int UserId { get; set; }
        public int LawyerId { get; set; }
        public int Rating { get; set; } // 1-5
        public string Comment { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }

        // Navigation properties
        public Booking Booking { get; set; } = null!;
        public User User { get; set; } = null!;
        public Lawyer Lawyer { get; set; } = null!;
    }
}
