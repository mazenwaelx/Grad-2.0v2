using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class ReviewMapper
    {
        public static Review ToReview(this ReviewCreateDto dto, int userId)
        {
            return new Review
            {
                BookingId = dto.BookingId,
                UserId = userId,
                LawyerId = dto.LawyerId,
                Rating = dto.Rating,
                Comment = dto.Comment,
                CreatedAt = DateTime.UtcNow
            };
        }

        public static ReviewResponseDto ToReviewResponseDto(this Review review)
        {
            return new ReviewResponseDto
            {
                Id = review.Id,
                BookingId = review.BookingId,
                UserId = review.UserId,
                LawyerId = review.LawyerId,
                Rating = review.Rating,
                Comment = review.Comment,
                CreatedAt = review.CreatedAt,
                UserName = review.User?.FullName,
                LawyerName = review.Lawyer?.User?.FullName
            };
        }

        public static List<ReviewResponseDto> ToReviewResponseDtoList(this IEnumerable<Review> reviews)
        {
            return reviews.Select(r => r.ToReviewResponseDto()).ToList();
        }
    }
}