using System.ComponentModel.DataAnnotations;

namespace LawyerConnect.DTOs
{
    public class NotificationCreateDto
    {
        [Required]
        public string Title { get; set; } = string.Empty;

        [Required]
        public string Message { get; set; } = string.Empty;

        [Required]
        public string Type { get; set; } = string.Empty; // Booking, Payment, System, Message
    }
}
