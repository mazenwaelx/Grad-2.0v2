using System.Security.Cryptography;
using System.Text;

namespace LawyerConnect.Tests.TestHelpers
{
    public static class PasswordHasher
    {
        public static string Hash(string input)
        {
            using var sha = SHA256.Create();
            return Convert.ToHexString(sha.ComputeHash(Encoding.UTF8.GetBytes(input)));
        }
    }
}
