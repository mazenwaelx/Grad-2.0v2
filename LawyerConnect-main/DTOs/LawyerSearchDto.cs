namespace LawyerConnect.DTOs
{
    public class LawyerSearchDto
    {
        public int? SpecializationId { get; set; }
        public decimal? Latitude { get; set; }
        public decimal? Longitude { get; set; }
        public decimal? RadiusKm { get; set; } = 50; // Default 50km radius
        public int? MinExperienceYears { get; set; }
        public decimal? MinRating { get; set; }
        public int Page { get; set; } = 1;
        public int Limit { get; set; } = 10;
    }
}
