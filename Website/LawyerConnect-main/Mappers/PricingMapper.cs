using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class PricingMapper
    {
        /// <summary>
        /// Convert LawyerPricingDto to LawyerPricing entity
        /// </summary>
        public static LawyerPricing ToLawyerPricing(this LawyerPricingDto dto, int lawyerId)
        {
            return new LawyerPricing
            {
                LawyerId = lawyerId,
                SpecializationId = dto.SpecializationId,
                InteractionTypeId = dto.InteractionTypeId,
                Price = dto.Price,
                DurationMinutes = dto.DurationMinutes
            };
        }

        /// <summary>
        /// Convert LawyerPricing entity to LawyerPricingDto
        /// </summary>
        public static LawyerPricingDto ToLawyerPricingDto(this LawyerPricing pricing)
        {
            return new LawyerPricingDto
            {
                SpecializationId = pricing.SpecializationId,
                InteractionTypeId = pricing.InteractionTypeId,
                Price = pricing.Price,
                DurationMinutes = pricing.DurationMinutes
            };
        }

        /// <summary>
        /// Convert list of LawyerPricing entities to list of LawyerPricingDto
        /// </summary>
        public static List<LawyerPricingDto> ToLawyerPricingDtoList(this IEnumerable<LawyerPricing> pricings)
        {
            return pricings.Select(p => p.ToLawyerPricingDto()).ToList();
        }

        /// <summary>
        /// Update existing LawyerPricing entity from LawyerPricingDto
        /// </summary>
        public static void UpdateFromDto(this LawyerPricing pricing, LawyerPricingDto dto)
        {
            pricing.Price = dto.Price;
            pricing.DurationMinutes = dto.DurationMinutes;
        }
    }
}
