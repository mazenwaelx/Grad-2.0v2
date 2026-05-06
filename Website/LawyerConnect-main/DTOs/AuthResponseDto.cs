namespace LawyerConnect.DTOs
{
    public class AuthResponseDto
    {
        public string? Token { get; set; }
        public DateTime? ExpiresAt { get; set; }
        public UserResponseDto? User { get; set; }
        public string? RefreshToken { get; set; }
        public DateTime? RefreshTokenExpires { get; set; }
    }
}

