using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class LawyerMapper
    {
        public static Lawyer ToLawyer(this LawyerRegisterDto dto, int userId)
        {
            return new Lawyer
            {
                UserId = userId,
                ExperienceYears = dto.ExperienceYears,
                Address = dto.Address,
                Latitude = dto.Latitude,
                Longitude = dto.Longitude,
                IsVerified = false,
                CreatedAt = DateTime.UtcNow
            };
        }

        public static LawyerResponseDto ToLawyerResponseDto(this Lawyer lawyer)
        {
            return new LawyerResponseDto
            {
                Id = lawyer.Id,
                UserId = lawyer.UserId,
                FullName = lawyer.User?.FullName ?? string.Empty,
                Email = lawyer.User?.Email ?? string.Empty,
                ExperienceYears = lawyer.ExperienceYears,
                IsVerified = lawyer.IsVerified,
                Address = lawyer.Address,
                Latitude = lawyer.Latitude,
                Longitude = lawyer.Longitude,
                Specializations = lawyer.Specializations?.Select(s => s.Specialization.Name).ToList() ?? new List<string>(),
                AverageRating = lawyer.Reviews?.Any() == true 
                    ? (decimal)lawyer.Reviews.Average(r => r.Rating) 
                    : 0,
                ReviewCount = lawyer.Reviews?.Count ?? 0,
                CreatedAt = lawyer.CreatedAt
            };
        }
    }
}

