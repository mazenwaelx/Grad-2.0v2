namespace LawyerConnect.DTOs
{
    public class LawyerResponseDto
    {
        public int Id { get; set; }
        public int UserId { get; set; }
        public string FullName { get; set; } = "";              
        public string Email { get; set; } = "";
        public int ExperienceYears { get; set; }
        public bool IsVerified { get; set; }
        public string Address { get; set; } = "";
        public decimal Latitude { get; set; }
        public decimal Longitude { get; set; }
        public List<string> Specializations { get; set; } = new List<string>();
        public decimal AverageRating { get; set; }
        public int ReviewCount { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}

