using LawyerConnect.Models;


namespace LawyerConnect.Repositories
{
    public interface ILawyerRepository
    {
        Task<Lawyer?> GetByIdAsync(int id);
        Task<Lawyer?> GetByUserIdAsync(int userId);
        Task<IEnumerable<Lawyer>> GetPagedAsync(int page, int limit);
        Task<List<Lawyer>> GetAllAsync();
        Task AddAsync(Lawyer lawyer);
        Task UpdateAsync(Lawyer lawyer);
    }
}

