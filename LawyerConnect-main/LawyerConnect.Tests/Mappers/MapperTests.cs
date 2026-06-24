using FluentAssertions;
using LawyerConnect.DTOs;
using LawyerConnect.Mappers;
using LawyerConnect.Models;
using LawyerConnect.Tests.TestHelpers;

namespace LawyerConnect.Tests.Mappers
{
    public class MapperTests
    {
        [Fact]
        public void UserMapper_MapsUserAndResponseDto()
        {
            var dto = new UserRegisterDto
            {
                FullName = "Jane Doe",
                Email = "jane@test.com",
                Phone = "111",
                City = "Cairo"
            };

            var user = dto.ToUser(PasswordHasher.Hash("pw"), "User");
            user.FullName.Should().Be("Jane Doe");
            user.Role.Should().Be("User");

            user.Id = 5;
            var response = user.ToUserResponseDto();
            response.Id.Should().Be(5);
            response.Email.Should().Be("jane@test.com");
        }

        [Fact]
        public void LawyerMapper_MapsLawyerAndResponseDto()
        {
            var dto = new LawyerRegisterDto
            {
                ExperienceYears = 8,
                Address = "Street 1",
                Latitude = 1,
                Longitude = 2,
                SpecializationIds = new List<int> { 1 }
            };

            var lawyer = dto.ToLawyer(10);
            lawyer.UserId.Should().Be(10);
            lawyer.IsVerified.Should().BeFalse();

            lawyer.User = new User { FullName = "Lawyer Name", Email = "lawyer@test.com" };
            lawyer.Specializations = new List<LawyerSpecialization>
            {
                new() { Specialization = new Specialization { Name = "Criminal Law" } }
            };
            lawyer.Reviews = new List<Review>
            {
                new() { Rating = 4 },
                new() { Rating = 5 }
            };

            var response = lawyer.ToLawyerResponseDto();
            response.FullName.Should().Be("Lawyer Name");
            response.Specializations.Should().ContainSingle("Criminal Law");
            response.AverageRating.Should().Be(4.5m);
            response.ReviewCount.Should().Be(2);
        }

        [Fact]
        public void BookingMapper_MapsBookingAndResponseDto()
        {
            var createDto = new BookingCreateDto
            {
                LawyerId = 2,
                SpecializationId = 1,
                InteractionTypeId = 1,
                Date = DateTime.UtcNow
            };

            var booking = createDto.ToBooking(1, 500m, 60);
            booking.Status.Should().Be("Pending");
            booking.PriceSnapshot.Should().Be(500m);

            booking.User = new User { FullName = "Client" };
            booking.Lawyer = new Lawyer { User = new User { FullName = "Lawyer" } };
            booking.Specialization = new Specialization { Name = "Family Law" };
            booking.InteractionType = new InteractionType { Name = "Consultation" };

            var response = booking.ToBookingResponseDto();
            response.UserName.Should().Be("Client");
            response.LawyerName.Should().Be("Lawyer");
            response.SpecializationName.Should().Be("Family Law");
            response.InteractionTypeName.Should().Be("Consultation");

            var list = new[] { booking }.ToBookingResponseDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void PricingMapper_MapsPricingDtoAndUpdatesEntity()
        {
            var dto = new LawyerPricingDto
            {
                SpecializationId = 1,
                InteractionTypeId = 1,
                Price = 400m,
                DurationMinutes = 45
            };

            var entity = dto.ToLawyerPricing(7);
            entity.LawyerId.Should().Be(7);
            entity.Price.Should().Be(400m);

            var mapped = entity.ToLawyerPricingDto();
            mapped.Price.Should().Be(400m);

            dto.Price = 500m;
            entity.UpdateFromDto(dto);
            entity.Price.Should().Be(500m);

            var list = new[] { entity }.ToLawyerPricingDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void SpecializationMapper_MapsSpecializationDto()
        {
            var dto = new SpecializationDto { Name = "Tax Law", Description = "Tax matters" };
            var entity = dto.ToSpecialization();
            entity.Name.Should().Be("Tax Law");

            var mapped = entity.ToSpecializationDto();
            mapped.Description.Should().Be("Tax matters");

            dto.Name = "Updated";
            entity.UpdateFromDto(dto);
            entity.Name.Should().Be("Updated");

            var list = new[] { entity }.ToSpecializationDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void ReviewMapper_MapsReviewAndResponseDto()
        {
            var dto = new ReviewCreateDto { BookingId = 1, LawyerId = 2, Rating = 5, Comment = "Great" };
            var review = dto.ToReview(3);
            review.UserId.Should().Be(3);
            review.LawyerId.Should().Be(2);

            review.User = new User { FullName = "Reviewer" };
            var response = review.ToReviewResponseDto();
            response.UserName.Should().Be("Reviewer");

            var list = new[] { review }.ToReviewResponseDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void NotificationMapper_MapsNotificationAndResponseDto()
        {
            var dto = new NotificationCreateDto
            {
                Title = "Hello",
                Message = "World",
                Type = "Info"
            };

            var notification = dto.ToNotification(1);
            notification.UserId.Should().Be(1);

            var response = notification.ToNotificationResponseDto();
            response.Title.Should().Be("Hello");

            var list = new[] { notification }.ToNotificationResponseDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void PaymentMapper_MapsPaymentSessionAndResponseDto()
        {
            var dto = new PaymentDto { BookingId = 1, Amount = 250m, Provider = "Stripe" };
            var session = dto.ToPaymentSession();
            session.Status.Should().Be("Pending");
            session.Amount.Should().Be(250m);

            session.ProviderSessionId = "sess_1";
            var response = session.ToPaymentSessionResponseDto("https://checkout");
            response.CheckoutUrl.Should().Be("https://checkout");

            var list = new[] { session }.ToPaymentSessionResponseDtoList();
            list.Should().HaveCount(1);
        }

        [Fact]
        public void ChatMapper_MapsChatEntities()
        {
            var message = "Hello".ToChatMessage(1, 2);
            message.Message.Should().Be("Hello");
            message.ChatRoomId.Should().Be(1);

            message.Sender = new User { FullName = "Sender" };
            var messageResponse = message.ToChatMessageResponseDto();
            messageResponse.SenderName.Should().Be("Sender");

            var room = new ChatRoom
            {
                BookingId = 1,
                CreatedAt = DateTime.UtcNow,
                Messages = new List<ChatMessage> { message, new ChatMessage() }
            };
            var roomResponse = room.ToChatRoomResponseDto();
            roomResponse.MessageCount.Should().Be(2);

            var messages = new[] { message }.ToChatMessageResponseDtoList();
            messages.Should().HaveCount(1);
        }
    }
}
