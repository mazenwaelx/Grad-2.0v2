namespace LawyerConnect.Models
{
    public class Specialization
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;

        // Navigation properties
        public List<LawyerSpecialization>? Lawyers { get; set; }
        public List<LawyerPricing>? Pricing { get; set; }
    }
}
