using LawyerConnect.Repositories;
using Microsoft.Extensions.Hosting;

namespace LawyerConnect.Services
{
    public class TokenCleanupService : BackgroundService
    {
        private readonly IServiceProvider _serviceProvider;
        private readonly ILogger<TokenCleanupService> _logger;
        private readonly IConfiguration _config;
        private TimeSpan _cleanupInterval;
        private int _daysToKeepRevokedTokens;

        public TokenCleanupService(IServiceProvider serviceProvider, ILogger<TokenCleanupService> logger, IConfiguration config)
        {
            _serviceProvider = serviceProvider;
            _logger = logger;
            _config = config;
            
            // Read from configuration
            _daysToKeepRevokedTokens = int.TryParse(_config["Jwt:TokenCleanupDaysOld"], out var days) ? days : 14;
            var cleanupHours = int.TryParse(_config["Jwt:TokenCleanupIntervalHours"], out var hours) ? hours : 10;
            _cleanupInterval = TimeSpan.FromHours(cleanupHours);
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation($"Token Cleanup Service started. Cleanup interval: {_cleanupInterval.TotalHours} hours. Keeping revoked tokens for {_daysToKeepRevokedTokens} days.");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    using (var scope = _serviceProvider.CreateScope())
                    {
                        var refreshTokenRepository = scope.ServiceProvider.GetRequiredService<IRefreshTokenRepository>();
                        
                        // Delete revoked tokens older than configured days
                        await refreshTokenRepository.DeleteOldTokensAsync(_daysToKeepRevokedTokens);
                        
                        _logger.LogInformation($"Token cleanup completed at {DateTime.UtcNow}. Deleted revoked tokens older than {_daysToKeepRevokedTokens} days.");
                    }

                    await Task.Delay(_cleanupInterval, stoppingToken);
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error in token cleanup service: {ex.Message}");
                    await Task.Delay(_cleanupInterval, stoppingToken);
                }
            }

            _logger.LogInformation("Token Cleanup Service stopped.");
        }
    }
}
