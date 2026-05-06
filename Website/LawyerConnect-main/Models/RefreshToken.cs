namespace LawyerConnect.Models
{
    public class RefreshToken
    {
    public Guid Id { get; set; }

    public int UserId { get; set; }

    public string TokenHash { get; set; } = null!;

    public DateTime ExpiresAt { get; set; }

    public bool Revoked { get; set; }

    public DateTime CreatedAt { get; set; }

    public Guid? ReplacedByTokenId { get; set; }
    public DateTime? RevokedDate { get; set;}
    public RefreshTokenRevokeReason? RevokeReason { get; set; } // based enum 

    public string? IpAddress { get; set; }
    public string? UserAgent { get; set; }

    public User User { get; set; } = null!;
    public RefreshToken? Refreshtoken { get; set;} 

    }
}

