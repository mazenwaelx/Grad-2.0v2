using Xunit;
using Moq;
using FluentAssertions;
using LawyerConnect.Services;
using LawyerConnect.Repositories;
using LawyerConnect.Models;
using LawyerConnect.Data;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace LawyerConnect.Tests.Services
{
    public class ChatServiceTests
    {
        private readonly Mock<IChatRoomRepository> _chatRoomRepositoryMock;
        private readonly Mock<IChatMessageRepository> _chatMessageRepositoryMock;
        private readonly Mock<IBookingRepository> _bookingRepositoryMock;
        private readonly Mock<IUserRepository> _userRepositoryMock;
        private readonly Mock<INotificationRepository> _notificationRepositoryMock;
        private readonly Mock<ILogger<ChatService>> _loggerMock;
        private readonly LawyerConnectDbContext _context;
        private readonly ChatService _chatService;

        public ChatServiceTests()
        {
            _chatRoomRepositoryMock = new Mock<IChatRoomRepository>();
            _chatMessageRepositoryMock = new Mock<IChatMessageRepository>();
            _bookingRepositoryMock = new Mock<IBookingRepository>();
            _userRepositoryMock = new Mock<IUserRepository>();
            _notificationRepositoryMock = new Mock<INotificationRepository>();
            _loggerMock = new Mock<ILogger<ChatService>>();

            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);

            _chatService = new ChatService(
                _chatRoomRepositoryMock.Object,
                _chatMessageRepositoryMock.Object,
                _bookingRepositoryMock.Object,
                _userRepositoryMock.Object,
                _notificationRepositoryMock.Object,
                _context,
                _loggerMock.Object
            );
        }

        [Fact]
        public async Task GetChatRoomAsync_ValidUser_ReturnsChatRoom()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = false
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            var result = await _chatService.GetChatRoomAsync(1, 1);

            // Assert
            result.Should().NotBeNull();
            result.Id.Should().Be(1);
        }

        [Fact]
        public async Task GetChatRoomAsync_UnauthorizedUser_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 2, // Different user
                LawyerId = 3
            };

            var lawyer = new Lawyer
            {
                Id = 3,
                UserId = 4
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            Func<Task> act = async () => await _chatService.GetChatRoomAsync(1, 1);

            // Assert
            await act.Should().ThrowAsync<UnauthorizedAccessException>()
                .WithMessage("You do not have access to this chat room");
        }

        [Fact]
        public async Task SendMessageAsync_ValidInput_SendsMessage()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = false
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3
            };

            var sender = new User
            {
                Id = 1,
                FullName = "User 1"
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _userRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(sender);
            _chatMessageRepositoryMock.Setup(x => x.AddAsync(It.IsAny<ChatMessage>())).Returns(Task.CompletedTask);
            _notificationRepositoryMock.Setup(x => x.AddAsync(It.IsAny<Notification>())).Returns(Task.CompletedTask);
            
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            var result = await _chatService.SendMessageAsync(1, 1, "Hello");

            // Assert
            result.Should().NotBeNull();
            result.Message.Should().Be("Hello");
            _chatMessageRepositoryMock.Verify(x => x.AddAsync(It.IsAny<ChatMessage>()), Times.Once);
            _notificationRepositoryMock.Verify(x => x.AddAsync(It.IsAny<Notification>()), Times.Once);
        }

        [Fact]
        public async Task SendMessageAsync_EmptyMessage_ThrowsArgumentException()
        {
            // Arrange & Act
            Func<Task> act = async () => await _chatService.SendMessageAsync(1, 1, "");

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Message cannot be empty");
        }

        [Fact]
        public async Task SendMessageAsync_MessageTooLong_ThrowsArgumentException()
        {
            // Arrange
            var longMessage = new string('a', 1001);

            // Act
            Func<Task> act = async () => await _chatService.SendMessageAsync(1, 1, longMessage);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Message cannot exceed 1000 characters");
        }

        [Fact]
        public async Task SendMessageAsync_ArchivedChatRoom_ThrowsInvalidOperationException()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = true
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);

            // Act
            Func<Task> act = async () => await _chatService.SendMessageAsync(1, 1, "Hello");

            // Assert
            await act.Should().ThrowAsync<InvalidOperationException>()
                .WithMessage("Cannot send messages to archived chat room");
        }

        [Fact]
        public async Task SendMessageAsync_UnauthorizedSender_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = false
            };

            var booking = new Booking
            {
                Id = 1,
                UserId = 2, // Different user
                LawyerId = 3
            };

            var lawyer = new Lawyer
            {
                Id = 3,
                UserId = 4
            };

            var sender = new User
            {
                Id = 1,
                FullName = "User 1"
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);
            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _userRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(sender);
            
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            Func<Task> act = async () => await _chatService.SendMessageAsync(1, 1, "Hello");

            // Assert
            await act.Should().ThrowAsync<UnauthorizedAccessException>()
                .WithMessage("You do not have access to this chat room");
        }

        [Fact]
        public async Task GetMessagesAsync_ValidUser_ReturnsMessages()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 1,
                LawyerId = 2
            };

            var lawyer = new Lawyer
            {
                Id = 2,
                UserId = 3
            };

            var messages = new List<ChatMessage>
            {
                new ChatMessage 
                { 
                    Id = 1, 
                    ChatRoomId = 1, 
                    SenderId = 1, 
                    Message = "Hello",
                    Sender = new User { Id = 1, FullName = "User 1" }
                }
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            _chatMessageRepositoryMock.Setup(x => x.GetMessagesByBookingIdAsync(1, 1, 50)).ReturnsAsync(messages);
            
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            var result = await _chatService.GetMessagesAsync(1, 1, 1, 50);

            // Assert
            result.Should().NotBeNull();
            result.Should().HaveCount(1);
        }

        [Fact]
        public async Task GetMessagesAsync_UnauthorizedUser_ThrowsUnauthorizedAccessException()
        {
            // Arrange
            var booking = new Booking
            {
                Id = 1,
                UserId = 2, // Different user
                LawyerId = 3
            };

            var lawyer = new Lawyer
            {
                Id = 3,
                UserId = 4
            };

            _bookingRepositoryMock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(booking);
            
            _context.Lawyers.Add(lawyer);
            await _context.SaveChangesAsync();

            // Act
            Func<Task> act = async () => await _chatService.GetMessagesAsync(1, 1, 1, 50);

            // Assert
            await act.Should().ThrowAsync<UnauthorizedAccessException>()
                .WithMessage("You do not have access to this chat room");
        }

        [Fact]
        public async Task ArchiveChatRoomAsync_ValidChatRoom_ArchivesChatRoom()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = false
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);
            _chatRoomRepositoryMock.Setup(x => x.UpdateAsync(It.IsAny<ChatRoom>())).Returns(Task.CompletedTask);

            // Act
            await _chatService.ArchiveChatRoomAsync(1);

            // Assert
            chatRoom.IsArchived.Should().BeTrue();
            _chatRoomRepositoryMock.Verify(x => x.UpdateAsync(It.IsAny<ChatRoom>()), Times.Once);
        }

        [Fact]
        public async Task ArchiveChatRoomAsync_AlreadyArchived_DoesNothing()
        {
            // Arrange
            var chatRoom = new ChatRoom
            {
                Id = 1,
                BookingId = 1,
                IsArchived = true
            };

            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(1)).ReturnsAsync(chatRoom);

            // Act
            await _chatService.ArchiveChatRoomAsync(1);

            // Assert
            _chatRoomRepositoryMock.Verify(x => x.UpdateAsync(It.IsAny<ChatRoom>()), Times.Never);
        }

        [Fact]
        public async Task ArchiveChatRoomAsync_ChatRoomNotFound_ThrowsArgumentException()
        {
            // Arrange
            _chatRoomRepositoryMock.Setup(x => x.GetByBookingIdAsync(999)).ReturnsAsync((ChatRoom?)null);

            // Act
            Func<Task> act = async () => await _chatService.ArchiveChatRoomAsync(999);

            // Assert
            await act.Should().ThrowAsync<ArgumentException>()
                .WithMessage("Chat room not found");
        }
    }
}
