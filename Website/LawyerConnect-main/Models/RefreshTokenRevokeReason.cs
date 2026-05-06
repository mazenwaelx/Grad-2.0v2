namespace LawyerConnect.Models
{
    public enum RefreshTokenRevokeReason
    {
        Logout,
        LogoutAll,
        Rotation,
        ReplayDetected,
        PasswordChanged,
        AccountDeleted,
        AdminForceLogout
    }
}
