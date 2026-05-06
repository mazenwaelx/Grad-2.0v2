namespace LawyerConnect.Models
{
    public class LawyerSpecialization
    {
        public int LawyerId { get; set; }
        public int SpecializationId { get; set; }

        // Navigation properties
        public Lawyer Lawyer { get; set; } = null!;
        public Specialization Specialization { get; set; } = null!;
    }
}
