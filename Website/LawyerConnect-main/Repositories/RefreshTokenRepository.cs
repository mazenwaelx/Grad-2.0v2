using LawyerConnect.Data;
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Repositories
{
public class RefreshTokenRepository : IRefreshTokenRepository
{
    private readonly LawyerConnectDbContext _db;

    public RefreshTokenRepository(LawyerConnectDbContext db)
    {
        _db = db;
    }

    public async Task AddAsync(RefreshToken token)
    {
        _db.RefreshTokens.Add(token);
        await _db.SaveChangesAsync();
    }

    public Task<RefreshToken?> GetByTokenHashAsync(string tokenHash)
    {
        return _db.RefreshTokens
                .Include(r => r.User) 
                .SingleOrDefaultAsync(r => r.TokenHash == tokenHash);
    }

    public async Task RevokeAsync(RefreshToken token , RefreshTokenRevokeReason reason)
    {
        token.Revoked = true;
        token.RevokedDate = DateTime.UtcNow;
        token.RevokeReason = reason;
        await _db.SaveChangesAsync();
    }

    public async Task RevokeAllAsync(int userId ,RefreshTokenRevokeReason reason)
    {
        var tokens = await _db.RefreshTokens
                .Where(r => r.UserId == userId && !r.Revoked) // not revoked 
                .ToListAsync();
        foreach (var token in tokens)
        {
            token.Revoked = true; // revoke all maybe a replay attack 
            token.RevokedDate = DateTime.UtcNow;
            token.RevokeReason = reason;
        }

        await _db.SaveChangesAsync();
    }

    public async Task DeleteOldTokensAsync(int Days) 
    {
        var cutoffDate = DateTime.UtcNow.AddDays(-Days);
        var tokensToDelete = await _db.RefreshTokens
                .Where(r => r.Revoked && r.RevokedDate.HasValue && r.RevokedDate < cutoffDate)
                .ToListAsync();

        _db.RefreshTokens.RemoveRange(tokensToDelete);
        await _db.SaveChangesAsync();
    }
}
}