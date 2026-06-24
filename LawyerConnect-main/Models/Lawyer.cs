namespace LawyerConnect.Models
{
    public class Lawyer
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public int ExperienceYears { get; set; }
        public bool IsVerified { get; set; }
        public string Address { get; set; } = string.Empty;
        public decimal Latitude { get; set; } 
        public decimal Longitude { get; set; }
        public decimal AverageRating { get; set; } = 0;
        public int ReviewsCount { get; set; } = 0;
        public DateTime CreatedAt { get; set; }

        // Navigation properties
        public User User { get; set; } = null!;
        public List<LawyerSpecialization>? Specializations { get; set; }
        public List<LawyerPricing>? Pricing { get; set; }
        public List<Booking>? Bookings { get; set; }
        public List<Review>? Reviews { get; set; }
    }
}