using FluentAssertions;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Moq;

namespace LawyerConnect.Tests.Services
{
    public class TokenCleanupServiceTests
    {
        [Fact]
        public async Task ExecuteAsync_RunsCleanupOnceBeforeCancellation()
        {
            var refreshTokenRepositoryMock = new Mock<IRefreshTokenRepository>();
            refreshTokenRepositoryMock
                .Setup(x => x.DeleteOldTokensAsync(It.IsAny<int>()))
                .Returns(Task.CompletedTask);

            var services = new ServiceCollection();
            services.AddSingleton(refreshTokenRepositoryMock.Object);
            var provider = services.BuildServiceProvider();

            var config = TestConfigurationFactory.Create();
            var service = new TokenCleanupService(provider, NullLogger<TokenCleanupService>.Instance, config);

            using var cts = new CancellationTokenSource();
            cts.CancelAfter(TimeSpan.FromMilliseconds(100));

            await service.StartAsync(cts.Token);
            await Task.Delay(150);
            await service.StopAsync(CancellationToken.None);

            refreshTokenRepositoryMock.Verify(x => x.DeleteOldTokensAsync(14), Times.AtLeastOnce);
        }
    }
}
