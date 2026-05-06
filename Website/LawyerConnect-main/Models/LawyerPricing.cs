namespace LawyerConnect.Models
{
    public class LawyerPricing
    {
        public int LawyerId { get; set; }
        public int SpecializationId { get; set; }
        public int InteractionTypeId { get; set; }
        public decimal Price { get; set; }
        public int DurationMinutes { get; set; }

        // Navigation properties
        public Lawyer Lawyer { get; set; } = null!;
        public Specialization Specialization { get; set; } = null!;
        public InteractionType InteractionType { get; set; } = null!;
    }
}
