using LawyerConnect.Models;

namespace LawyerConnect.Repositories
{
    public interface IRefreshTokenRepository
    {
        // add new refresh token 
        Task AddAsync (RefreshToken token);
        
        //Get refresh token by tokenHash  (validating front-end token)
        Task<RefreshToken?> GetByTokenHashAsync (string refreshToken );

        // revoke a single refresh token 
        Task RevokeAsync (RefreshToken token,  RefreshTokenRevokeReason reason);

        // revoke all refresh token based used (Multi-device senario)
        Task RevokeAllAsync (int userId, RefreshTokenRevokeReason reason);

        // delete old/expired/revoked tokens (clean-up job)

        Task DeleteOldTokensAsync(int Days);

    }
}