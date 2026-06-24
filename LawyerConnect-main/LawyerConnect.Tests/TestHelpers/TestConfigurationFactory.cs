using Microsoft.Extensions.Configuration;

namespace LawyerConnect.Tests.TestHelpers
{
    public static class TestConfigurationFactory
    {
        public static IConfiguration Create()
        {
            return new ConfigurationBuilder()
                .AddInMemoryCollection(new Dictionary<string, string?>
                {
                    ["Jwt:Key"] = "LawyerConnect_Test_JWT_Secret_Key_Minimum_32_Chars",
                    ["Jwt:Issuer"] = "LawyerConnectTest",
                    ["Jwt:Audience"] = "LawyerConnectTest",
                    ["Jwt:ExpiresMinutes"] = "30",
                    ["Jwt:RefreshTokenExpirationDays"] = "7",
                    ["Jwt:TokenCleanupDaysOld"] = "14",
                    ["Jwt:TokenCleanupIntervalHours"] = "10",
                    ["RateLimiting:Limit"] = "5",
                    ["RateLimiting:WindowSeconds"] = "60",
                    ["Stripe:SecretKey"] = "YOUR_STRIPE_SECRET_KEY_HERE",
                    ["Stripe:WebhookSecret"] = "whsec_test",
                    ["App:BaseUrl"] = "http://localhost:3002"
                })
                .Build();
        }
    }
}
