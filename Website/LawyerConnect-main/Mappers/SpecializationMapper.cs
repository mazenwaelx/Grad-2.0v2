using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class SpecializationMapper
    {
        /// <summary>
        /// Convert SpecializationDto to Specialization entity
        /// </summary>
        public static Specialization ToSpecialization(this SpecializationDto dto)
        {
            return new Specialization
            {
                Name = dto.Name,
                Description = dto.Description
            };
        }

        /// <summary>
        /// Convert Specialization entity to SpecializationDto
        /// </summary>
        public static SpecializationDto ToSpecializationDto(this Specialization specialization)
        {
            return new SpecializationDto
            {
                Id = specialization.Id,
                Name = specialization.Name,
                Description = specialization.Description
            };
        }

        /// <summary>
        /// Convert list of Specialization entities to list of SpecializationDto
        /// </summary>
        public static List<SpecializationDto> ToSpecializationDtoList(this IEnumerable<Specialization> specializations)
        {
            return specializations.Select(s => s.ToSpecializationDto()).ToList();
        }

        /// <summary>
        /// Update existing Specialization entity from SpecializationDto
        /// </summary>
        public static void UpdateFromDto(this Specialization specialization, SpecializationDto dto)
        {
            specialization.Name = dto.Name;
            specialization.Description = dto.Description;
        }
    }
}
