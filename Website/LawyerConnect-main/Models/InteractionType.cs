namespace LawyerConnect.Models
{
    public class InteractionType
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty; // Meeting, Phone, Chat

        // Navigation properties
        public List<LawyerPricing>? Pricing { get; set; }
        public List<Booking>? Bookings { get; set; }
    }
}
