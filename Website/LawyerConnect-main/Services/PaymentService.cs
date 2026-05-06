using LawyerConnect.DTOs;
using LawyerConnect.Models;
using LawyerConnect.Repositories;
using LawyerConnect.Data;
using LawyerConnect.Mappers;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using Stripe;
using Stripe.Checkout;

namespace LawyerConnect.Services
{
    public class PaymentService : IPaymentService
    {
        private readonly IPaymentSessionRepository _paymentSessionRepository;
        private readonly IBookingRepository _bookingRepository;
        private readonly INotificationRepository _notificationRepository;
        private readonly LawyerConnectDbContext _context;
        private readonly IConfiguration _configuration;
        private readonly ILogger<PaymentService> _logger;

        public PaymentService(
            IPaymentSessionRepository paymentSessionRepository,
            IBookingRepository bookingRepository,
            INotificationRepository notificationRepository,
            LawyerConnectDbContext context,
            IConfiguration configuration,
            ILogger<PaymentService> logger)
        {
            _paymentSessionRepository = paymentSessionRepository;
            _bookingRepository = bookingRepository;
            _notificationRepository = notificationRepository;
            _context = context;
            _configuration = configuration;
            _logger = logger;
        }

        public async Task<PaymentSessionResponseDto> CreateSessionAsync(int userId, int bookingId, decimal amount)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                // Validate booking exists and belongs to user
                var booking = await _bookingRepository.GetByIdAsync(bookingId);
                if (booking == null)
                {
                    _logger.LogWarning($"Payment creation failed: Booking {bookingId} not found");
                    throw new ArgumentException("Booking not found");
                }

                if (booking.UserId != userId)
                {
                    _logger.LogWarning($"Payment creation failed: User {userId} attempted to pay for booking {bookingId} owned by user {booking.UserId}");
                    throw new UnauthorizedAccessException("You can only pay for your own bookings");
                }

                // Validate booking status
                if (booking.Status != "Pending")
                {
                    _logger.LogWarning($"Payment creation failed: Booking {bookingId} has status {booking.Status}, expected Pending");
                    throw new InvalidOperationException($"Cannot create payment for booking with status: {booking.Status}");
                }

                if (booking.PaymentStatus == "Paid")
                {
                    _logger.LogWarning($"Payment creation failed: Booking {bookingId} is already paid");
                    throw new InvalidOperationException("Booking is already paid");
                }

                // Validate amount matches booking price
                if (amount != booking.PriceSnapshot)
                {
                    _logger.LogWarning($"Payment creation failed: Amount {amount} does not match booking price {booking.PriceSnapshot}");
                    throw new ArgumentException($"Payment amount ({amount:C}) must match booking price ({booking.PriceSnapshot:C})");
                }

                // Check for existing pending payment session
                var existingSession = await _paymentSessionRepository.GetByBookingIdAsync(bookingId);
                if (existingSession != null && existingSession.Status == "Pending")
                {
                    _logger.LogInformation($"Returning existing pending payment session {existingSession.Id} for booking {bookingId}");
                    await transaction.CommitAsync();
                    return existingSession.ToPaymentSessionResponseDto();
                }

                // Create Stripe Checkout Session (skip if no real key configured)
                var stripeKey = _configuration["Stripe:SecretKey"] ?? "";
                var isStripeConfigured = !string.IsNullOrWhiteSpace(stripeKey)
                    && !stripeKey.StartsWith("YOUR_");

                string stripeSessionId;
                string? checkoutUrl = null;

                if (isStripeConfigured)
                {
                    (stripeSessionId, checkoutUrl) = await CreateStripeCheckoutSessionAsync(bookingId, amount);
                }
                else
                {
                    stripeSessionId = $"sim_{Guid.NewGuid():N}";
                    _logger.LogWarning("Stripe not configured — using simulated payment session for booking {BookingId}", bookingId);
                }

                // Create new payment session
                var paymentSession = new PaymentSession
                {
                    BookingId = bookingId,
                    Amount = amount,
                    Status = "Pending",
                    Provider = isStripeConfigured ? "Stripe" : "Simulated",
                    ProviderSessionId = stripeSessionId,
                    CreatedAt = DateTime.UtcNow
                };

                await _paymentSessionRepository.AddAsync(paymentSession);

                // Update booking payment status
                booking.PaymentStatus = "Pending";
                await _bookingRepository.UpdateAsync(booking);

                // Create notification for user
                var notification = new Notification
                {
                    UserId = userId,
                    Title = "Payment Session Created",
                    Message = $"Payment session created for booking #{bookingId}. Amount: {amount:C}",
                    Type = "Payment",
                    IsRead = false,
                    CreatedAt = DateTime.UtcNow
                };
                await _notificationRepository.AddAsync(notification);

                await transaction.CommitAsync();

                _logger.LogInformation($"Payment session {paymentSession.Id} created successfully for booking {bookingId}, amount: {amount:C}");

                return paymentSession.ToPaymentSessionResponseDto(checkoutUrl);
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to create payment session for booking {bookingId}");
                throw;
            }
        }

        public async Task<PaymentSessionResponseDto> ConfirmPaymentAsync(int sessionId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var paymentSession = await _paymentSessionRepository.GetByIdAsync(sessionId);
                if (paymentSession == null)
                {
                    _logger.LogWarning($"Payment confirmation failed: Session {sessionId} not found");
                    throw new ArgumentException("Payment session not found");
                }

                if (paymentSession.Status != "Pending")
                {
                    _logger.LogWarning($"Payment confirmation failed: Session {sessionId} has status {paymentSession.Status}, expected Pending");
                    throw new InvalidOperationException($"Cannot confirm payment with status: {paymentSession.Status}");
                }

                // Update payment session status
                paymentSession.Status = "Success";
                await _paymentSessionRepository.UpdateAsync(paymentSession);

                // Update booking status
                var booking = await _bookingRepository.GetByIdAsync(paymentSession.BookingId);
                if (booking != null)
                {
                    booking.PaymentStatus = "Paid";
                    booking.Status = "Confirmed";
                    await _bookingRepository.UpdateAsync(booking);

                    // Create notifications for both user and lawyer
                    var notifications = new List<Notification>
                    {
                        new Notification
                        {
                            UserId = booking.UserId,
                            Title = "Payment Confirmed",
                            Message = $"Your payment of {paymentSession.Amount:C} has been confirmed. Your booking is now confirmed.",
                            Type = "Payment",
                            IsRead = false,
                            CreatedAt = DateTime.UtcNow
                        },
                        new Notification
                        {
                            UserId = booking.Lawyer.UserId,
                            Title = "New Confirmed Booking",
                            Message = $"You have a new confirmed booking. Payment of {paymentSession.Amount:C} has been received.",
                            Type = "Booking",
                            IsRead = false,
                            CreatedAt = DateTime.UtcNow
                        }
                    };

                    foreach (var notification in notifications)
                    {
                        await _notificationRepository.AddAsync(notification);
                    }

                    _logger.LogInformation($"Payment confirmed for session {sessionId}, booking {booking.Id} status updated to Confirmed");
                }

                await transaction.CommitAsync();

                return paymentSession.ToPaymentSessionResponseDto();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to confirm payment for session {sessionId}");
                throw;
            }
        }

        public async Task HandleWebhookAsync(string provider, string payload)
        {
            try
            {
                _logger.LogInformation($"Processing webhook from {provider}");

                if (provider.ToLower() != "stripe")
                {
                    _logger.LogWarning($"Unsupported payment provider: {provider}");
                    return;
                }

                // Verify and parse Stripe webhook
                var stripeEvent = await VerifyStripeWebhookAsync(payload);
                if (stripeEvent == null)
                {
                    _logger.LogError("Failed to verify Stripe webhook signature");
                    return;
                }

                switch (stripeEvent.Type)
                {
                    case Events.CheckoutSessionCompleted:
                        await HandleStripeCheckoutCompleted(stripeEvent);
                        break;
                    case Events.PaymentIntentSucceeded:
                        await HandleStripePaymentSucceeded(stripeEvent);
                        break;
                    case Events.PaymentIntentPaymentFailed:
                        await HandleStripePaymentFailed(stripeEvent);
                        break;
                    default:
                        _logger.LogInformation($"Unhandled Stripe webhook event type: {stripeEvent.Type}");
                        break;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error processing webhook from {provider}: {payload}");
                throw;
            }
        }

        public async Task RefundPaymentAsync(int sessionId)
        {
            await using var transaction = await _context.Database.BeginTransactionAsync();
            try
            {
                var paymentSession = await _paymentSessionRepository.GetByIdAsync(sessionId);
                if (paymentSession == null)
                {
                    _logger.LogWarning($"Refund failed: Payment session {sessionId} not found");
                    throw new ArgumentException("Payment session not found");
                }

                if (paymentSession.Status != "Success")
                {
                    _logger.LogWarning($"Refund failed: Session {sessionId} has status {paymentSession.Status}, expected Success");
                    throw new InvalidOperationException("Can only refund successful payments");
                }

                // Process Stripe refund (skip if not configured)
                var stripeKey = _configuration["Stripe:SecretKey"] ?? "";
                if (!string.IsNullOrWhiteSpace(stripeKey) && !stripeKey.StartsWith("YOUR_")
                    && paymentSession.Provider == "Stripe")
                {
                    await ProcessStripeRefundAsync(paymentSession.ProviderSessionId, paymentSession.Amount);
                }

                // Update payment session status to indicate refund
                paymentSession.Status = "Refunded";
                await _paymentSessionRepository.UpdateAsync(paymentSession);

                // Update booking status
                var booking = await _bookingRepository.GetByIdAsync(paymentSession.BookingId);
                if (booking != null)
                {
                    booking.PaymentStatus = "Refunded";
                    booking.Status = "Cancelled";
                    await _bookingRepository.UpdateAsync(booking);

                    // Create notifications for both user and lawyer
                    var notifications = new List<Notification>
                    {
                        new Notification
                        {
                            UserId = booking.UserId,
                            Title = "Payment Refunded",
                            Message = $"Your payment of {paymentSession.Amount:C} has been refunded. Your booking has been cancelled.",
                            Type = "Payment",
                            IsRead = false,
                            CreatedAt = DateTime.UtcNow
                        },
                        new Notification
                        {
                            UserId = booking.Lawyer.UserId,
                            Title = "Booking Cancelled",
                            Message = $"A booking has been cancelled and refunded. Amount: {paymentSession.Amount:C}",
                            Type = "Booking",
                            IsRead = false,
                            CreatedAt = DateTime.UtcNow
                        }
                    };

                    foreach (var notification in notifications)
                    {
                        await _notificationRepository.AddAsync(notification);
                    }

                    _logger.LogInformation($"Payment refunded for session {sessionId}, booking {booking.Id} cancelled");
                }

                await transaction.CommitAsync();
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();
                _logger.LogError(ex, $"Failed to refund payment for session {sessionId}");
                throw;
            }
        }

        public async Task<PaymentSessionResponseDto?> GetPaymentSessionAsync(int sessionId)
        {
            var paymentSession = await _paymentSessionRepository.GetByIdAsync(sessionId);
            return paymentSession?.ToPaymentSessionResponseDto();
        }

        public async Task<List<PaymentSessionResponseDto>> GetUserPaymentSessionsAsync(int userId, int page = 1, int limit = 10)
        {
            var sessions = await _paymentSessionRepository.GetByUserIdAsync(userId, page, limit);
            return sessions.ToPaymentSessionResponseDtoList();
        }

        #region Private Helper Methods

        private async Task<(string sessionId, string checkoutUrl)> CreateStripeCheckoutSessionAsync(int bookingId, decimal amount)
        {
            try
            {
                var options = new SessionCreateOptions
                {
                    PaymentMethodTypes = new List<string> { "card" },
                    LineItems = new List<SessionLineItemOptions>
                    {
                        new SessionLineItemOptions
                        {
                            PriceData = new SessionLineItemPriceDataOptions
                            {
                                UnitAmount = (long)(amount * 100), // Convert to cents
                                Currency = _configuration["Stripe:Currency"] ?? "usd",
                                ProductData = new SessionLineItemPriceDataProductDataOptions
                                {
                                    Name = $"Legal Consultation - Booking #{bookingId}",
                                    Description = "Payment for legal consultation booking"
                                }
                            },
                            Quantity = 1
                        }
                    },
                    Mode = "payment",
                    SuccessUrl = $"{_configuration["App:BaseUrl"]}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                    CancelUrl = $"{_configuration["App:BaseUrl"]}/payment/cancel",
                    Metadata = new Dictionary<string, string>
                    {
                        { "booking_id", bookingId.ToString() }
                    }
                };

                var service = new SessionService();
                var session = await service.CreateAsync(options);

                _logger.LogInformation($"Stripe checkout session created: {session.Id} for booking {bookingId}");
                return (session.Id, session.Url);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to create Stripe checkout session for booking {bookingId}");
                throw new InvalidOperationException("Failed to create payment session with Stripe", ex);
            }
        }

        private async Task<Event?> VerifyStripeWebhookAsync(string payload)
        {
            try
            {
                var webhookSecret = _configuration["Stripe:WebhookSecret"];
                if (string.IsNullOrEmpty(webhookSecret))
                {
                    _logger.LogError("Stripe webhook secret not configured");
                    return null;
                }

                // In a real implementation, you would get the signature from the request headers
                // For now, we'll parse the event directly (this should be enhanced for production)
                var stripeEvent = EventUtility.ParseEvent(payload);
                return stripeEvent;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to verify Stripe webhook");
                return null;
            }
        }

        private async Task HandleStripeCheckoutCompleted(Event stripeEvent)
        {
            try
            {
                var session = stripeEvent.Data.Object as Session;
                if (session?.Metadata?.TryGetValue("booking_id", out var bookingIdStr) == true &&
                    int.TryParse(bookingIdStr, out var bookingId))
                {
                    var paymentSession = await _paymentSessionRepository.GetByProviderSessionIdAsync(session.Id);
                    if (paymentSession != null && paymentSession.Status == "Pending")
                    {
                        await ConfirmPaymentAsync(paymentSession.Id);
                        _logger.LogInformation($"Payment automatically confirmed via Stripe checkout completion for session {paymentSession.Id}");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to handle Stripe checkout completion");
            }
        }

        private async Task HandleStripePaymentSucceeded(Event stripeEvent)
        {
            try
            {
                var paymentIntent = stripeEvent.Data.Object as PaymentIntent;
                if (paymentIntent != null)
                {
                    // Find payment session by payment intent ID
                    var paymentSession = await _paymentSessionRepository.GetByProviderSessionIdAsync(paymentIntent.Id);
                    if (paymentSession != null && paymentSession.Status == "Pending")
                    {
                        await ConfirmPaymentAsync(paymentSession.Id);
                        _logger.LogInformation($"Payment automatically confirmed via webhook for session {paymentSession.Id}");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to handle Stripe payment succeeded webhook");
            }
        }

        private async Task HandleStripePaymentFailed(Event stripeEvent)
        {
            try
            {
                var paymentIntent = stripeEvent.Data.Object as PaymentIntent;
                if (paymentIntent != null)
                {
                    var paymentSession = await _paymentSessionRepository.GetByProviderSessionIdAsync(paymentIntent.Id);
                    if (paymentSession != null && paymentSession.Status == "Pending")
                    {
                        paymentSession.Status = "Failed";
                        await _paymentSessionRepository.UpdateAsync(paymentSession);

                        var booking = await _bookingRepository.GetByIdAsync(paymentSession.BookingId);
                        if (booking != null)
                        {
                            booking.PaymentStatus = "Failed";
                            await _bookingRepository.UpdateAsync(booking);

                            // Notify user of payment failure
                            var notification = new Notification
                            {
                                UserId = booking.UserId,
                                Title = "Payment Failed",
                                Message = $"Payment of {paymentSession.Amount:C} failed. Please try again.",
                                Type = "Payment",
                                IsRead = false,
                                CreatedAt = DateTime.UtcNow
                            };
                            await _notificationRepository.AddAsync(notification);
                        }

                        _logger.LogWarning($"Payment failed for session {paymentSession.Id}");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to handle Stripe payment failed webhook");
            }
        }

        private async Task ProcessStripeRefundAsync(string sessionId, decimal amount)
        {
            try
            {
                // Get the checkout session to find the payment intent
                var sessionService = new SessionService();
                var session = await sessionService.GetAsync(sessionId);

                if (session.PaymentIntentId != null)
                {
                    var refundOptions = new RefundCreateOptions
                    {
                        PaymentIntent = session.PaymentIntentId,
                        Amount = (long)(amount * 100), // Convert to cents
                        Reason = RefundReasons.RequestedByCustomer
                    };

                    var refundService = new RefundService();
                    var refund = await refundService.CreateAsync(refundOptions);

                    _logger.LogInformation($"Stripe refund created: {refund.Id} for session {sessionId}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to process Stripe refund for session {sessionId}");
                throw new InvalidOperationException("Failed to process refund with Stripe", ex);
            }
        }

        private async Task HandlePaymentSucceeded(string providerSessionId)
        {
            try
            {
                var paymentSession = await _paymentSessionRepository.GetByProviderSessionIdAsync(providerSessionId);
                if (paymentSession != null && paymentSession.Status == "Pending")
                {
                    await ConfirmPaymentAsync(paymentSession.Id);
                    _logger.LogInformation($"Payment automatically confirmed via webhook for session {paymentSession.Id}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to handle payment succeeded webhook for provider session {providerSessionId}");
            }
        }

        private async Task HandlePaymentFailed(string providerSessionId)
        {
            try
            {
                var paymentSession = await _paymentSessionRepository.GetByProviderSessionIdAsync(providerSessionId);
                if (paymentSession != null && paymentSession.Status == "Pending")
                {
                    paymentSession.Status = "Failed";
                    await _paymentSessionRepository.UpdateAsync(paymentSession);

                    var booking = await _bookingRepository.GetByIdAsync(paymentSession.BookingId);
                    if (booking != null)
                    {
                        booking.PaymentStatus = "Failed";
                        await _bookingRepository.UpdateAsync(booking);

                        // Notify user of payment failure
                        var notification = new Notification
                        {
                            UserId = booking.UserId,
                            Title = "Payment Failed",
                            Message = $"Payment of {paymentSession.Amount:C} failed. Please try again.",
                            Type = "Payment",
                            IsRead = false,
                            CreatedAt = DateTime.UtcNow
                        };
                        await _notificationRepository.AddAsync(notification);
                    }

                    _logger.LogWarning($"Payment failed for session {paymentSession.Id}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to handle payment failed webhook for provider session {providerSessionId}");
            }
        }

        #endregion
    }
}
