using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace LawyerConnect.Repositories
{
    public class UserRepository : IUserRepository
    {
        private readonly LawyerConnectDbContext _context;

        public UserRepository(LawyerConnectDbContext context) => _context = context;

        public async Task<User?> GetByIdAsync(int id) =>
            await _context.Users.Include(u => u.LawyerProfile).FirstOrDefaultAsync(u => u.Id == id);

        public async Task<User?> GetByEmailAsync(string email) =>
            await _context.Users.Include(u => u.LawyerProfile).FirstOrDefaultAsync(u => u.Email == email);

        public async Task<IEnumerable<User>> GetPagedAsync(int page, int limit) =>
            await _context.Users // from users 
                .OrderBy(u => u.Id) // order by id asec
                .Skip((page - 1) * limit) //offset X Rows
                .Take(limit) // Fetch @limit Rows Only 
                .ToListAsync(); // convert the last Linq expr => sql query and retrieve a list<user> which is casting to IEnumerable auto

        public async Task<List<User>> GetAllAsync() =>
            await _context.Users.ToListAsync();

        public async Task AddAsync(User user)
        {
            await _context.Users.AddAsync(user);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(User user)
        {
            _context.Users.Update(user); // no DB connection just modified the user state in memory NO Async
            await _context.SaveChangesAsync(); // no send updates from memorry to the DB
        }

        public async Task DeleteAsync(User user)
        {
            _context.Users.Remove(user);
            await _context.SaveChangesAsync();
        }
    }
}

