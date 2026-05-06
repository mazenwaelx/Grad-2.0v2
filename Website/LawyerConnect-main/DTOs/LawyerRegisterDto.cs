using System.ComponentModel.DataAnnotations;

namespace LawyerConnect.DTOs
{
    public class LawyerRegisterDto
    {
        [Range(0, 100, ErrorMessage = "Experience years must be between 0 and 100.")]
        public int ExperienceYears { get; set; }

        [Required]
        [StringLength(200, ErrorMessage = "Address cannot exceed 200 characters.")]
        public string Address { get; set; } = string.Empty;

        [Range(-90, 90, ErrorMessage = "Latitude must be between -90 and 90.")]
        public decimal Latitude { get; set; }

        [Range(-180, 180, ErrorMessage = "Longitude must be between -180 and 180.")]
        public decimal Longitude { get; set; }

        [Required]
        [MinLength(1, ErrorMessage = "At least one specialization must be selected.")]
        public List<int> SpecializationIds { get; set; } = new List<int>();

        [Range(0, 100000, ErrorMessage = "Base hourly rate must be valid.")]
        public decimal BaseHourlyRate { get; set; }
    }
}

