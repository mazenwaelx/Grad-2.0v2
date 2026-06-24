using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IPaymentService
    {
        /// <summary>
        /// Create a payment session for a booking
        /// </summary>
        Task<PaymentSessionResponseDto> CreateSessionAsync(int userId, int bookingId, decimal amount);

        /// <summary>
        /// Confirm a payment session (mark as successful)
        /// </summary>
        Task<PaymentSessionResponseDto> ConfirmPaymentAsync(int sessionId);

        /// <summary>
        /// Handle webhook from payment provider
        /// </summary>
        Task HandleWebhookAsync(string provider, string payload);

        /// <summary>
        /// Refund a successful payment
        /// </summary>
        Task RefundPaymentAsync(int sessionId);

        /// <summary>
        /// Get payment session by ID
        /// </summary>
        Task<PaymentSessionResponseDto?> GetPaymentSessionAsync(int sessionId);

        /// <summary>
        /// Get user's payment sessions with pagination
        /// </summary>
        Task<List<PaymentSessionResponseDto>> GetUserPaymentSessionsAsync(int userId, int page = 1, int limit = 10);
    }
}
