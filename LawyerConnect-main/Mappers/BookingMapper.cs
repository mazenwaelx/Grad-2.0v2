using LawyerConnect.DTOs;
using LawyerConnect.Models;

namespace LawyerConnect.Mappers
{
    public static class BookingMapper
    {
        public static Booking ToBooking(this BookingCreateDto dto, int userId, decimal priceSnapshot, int durationSnapshot)
        {
            return new Booking
            {
                UserId = userId,
                LawyerId = dto.LawyerId,
                SpecializationId = dto.SpecializationId,
                InteractionTypeId = dto.InteractionTypeId,
                PriceSnapshot = priceSnapshot,
                DurationSnapshot = durationSnapshot,
                Date = dto.Date,
                Status = "Pending",
                PaymentStatus = "Pending",
                CreatedAt = DateTime.UtcNow
            };
        }

        public static BookingResponseDto ToBookingResponseDto(this Booking booking)
        {
            return new BookingResponseDto
            {
                Id = booking.Id,
                UserId = booking.UserId,
                LawyerId = booking.LawyerId,
                SpecializationId = booking.SpecializationId,
                InteractionTypeId = booking.InteractionTypeId,
                PriceSnapshot = booking.PriceSnapshot,
                DurationSnapshot = booking.DurationSnapshot,
                Date = booking.Date,
                Status = booking.Status,
                PaymentStatus = booking.PaymentStatus,
                CreatedAt = booking.CreatedAt,
                LawyerName = booking.Lawyer?.User?.FullName,
                UserName = booking.User?.FullName,
                SpecializationName = booking.Specialization?.Name,
                InteractionTypeName = booking.InteractionType?.Name
            };
        }

        public static List<BookingResponseDto> ToBookingResponseDtoList(this IEnumerable<Booking> bookings)
        {
            return bookings.Select(b => b.ToBookingResponseDto()).ToList();
        }
    }
}

