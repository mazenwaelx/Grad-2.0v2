using LawyerConnect.Models;


namespace LawyerConnect.Repositories
{
    public interface IUserRepository
    {
        Task<User?> GetByIdAsync(int id);
        Task<User?> GetByEmailAsync(string email);
        Task<IEnumerable<User>> GetPagedAsync(int page, int limit); //pagination
        Task<List<User>> GetAllAsync();
        Task AddAsync(User user);
        Task UpdateAsync(User user);

        Task DeleteAsync(User user);
    }
}

