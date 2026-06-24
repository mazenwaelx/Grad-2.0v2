using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface ISpecializationRepository
    {
        Task<Specialization?> GetByIdAsync(int id);
        Task<List<Specialization>> GetAllAsync();
        Task AddAsync(Specialization specialization);
        Task UpdateAsync(Specialization specialization);
        Task DeleteAsync(int id);
    }
}
