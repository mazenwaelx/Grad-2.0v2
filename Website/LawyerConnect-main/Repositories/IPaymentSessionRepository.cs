using LawyerConnect.Models;
using System.Threading.Tasks;

namespace LawyerConnect.Repositories
{
    public interface IPaymentSessionRepository
    {
        Task<PaymentSession?> GetByIdAsync(int id);
        Task<PaymentSession?> GetByBookingIdAsync(int bookingId);
        Task<PaymentSession?> GetByProviderSessionIdAsync(string providerSessionId);
        Task<List<PaymentSession>> GetByUserIdAsync(int userId, int page = 1, int limit = 10);
        Task<List<PaymentSession>> GetAllAsync();
        Task AddAsync(PaymentSession paymentSession);
        Task UpdateAsync(PaymentSession paymentSession);
    }
}

