namespace LawyerConnect.DTOs
{
    public class UserResponseDto
    {
        public int Id { get; set; }
        public string FullName { get; set; } = string.Empty;
        public string Email { get; set; }= string.Empty;
        public string Role { get; set; }= string.Empty;
        public string Phone { get; set; }= string.Empty;
        public string City { get; set; }= string.Empty;
        public string? ProfilePhoto { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}

