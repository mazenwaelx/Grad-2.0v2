using System.ComponentModel.DataAnnotations;

namespace LawyerConnect.DTOs
{
    public class LawyerPricingDto
    {
        [Required]
        public int SpecializationId { get; set; }

        [Required]
        public int InteractionTypeId { get; set; }

        [Range(0, double.MaxValue, ErrorMessage = "Price must be a positive value.")]
        public decimal Price { get; set; }

        [Range(1, 480, ErrorMessage = "Duration must be between 1 and 480 minutes.")]
        public int DurationMinutes { get; set; }
    }
}
