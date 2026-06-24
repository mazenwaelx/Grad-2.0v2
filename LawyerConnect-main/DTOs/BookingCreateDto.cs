using System.ComponentModel.DataAnnotations;

namespace LawyerConnect.DTOs
{
    public class BookingCreateDto
    {
        [Required]
        public int LawyerId { get; set; }

        [Required]
        public int SpecializationId { get; set; }

        [Required]
        public int InteractionTypeId { get; set; }

        [Required]
        public DateTime Date { get; set; }
    }
}
