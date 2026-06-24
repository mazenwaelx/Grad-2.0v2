using FluentAssertions;
using LawyerConnect.Middlewares;
using LawyerConnect.Tests.TestHelpers;
using Microsoft.AspNetCore.Http;

namespace LawyerConnect.Tests.Middlewares
{
    public class RateLimitingMiddlewareTests
    {
        [Fact]
        public async Task InvokeAsync_ExemptPath_AllowsRequest()
        {
            var called = false;
            RequestDelegate next = _ =>
            {
                called = true;
                return Task.CompletedTask;
            };

            var middleware = new RateLimitingMiddleware(next, TestConfigurationFactory.Create());
            var context = new DefaultHttpContext();
            context.Request.Path = "/api/specializations";
            context.Request.Method = "GET";
            context.Connection.RemoteIpAddress = System.Net.IPAddress.Parse("127.0.0.1");

            await middleware.InvokeAsync(context);

            called.Should().BeTrue();
        }

        [Fact]
        public async Task InvokeAsync_ExceedsAuthLimit_Returns429()
        {
            var middleware = new RateLimitingMiddleware(_ => Task.CompletedTask, TestConfigurationFactory.Create());
            var ip = System.Net.IPAddress.Parse("10.0.0.1");

            for (var i = 0; i < 5; i++)
            {
                var okContext = new DefaultHttpContext();
                okContext.Request.Path = "/api/auth/login";
                okContext.Request.Method = "POST";
                okContext.Connection.RemoteIpAddress = ip;
                await middleware.InvokeAsync(okContext);
            }

            var blockedContext = new DefaultHttpContext();
            blockedContext.Request.Path = "/api/auth/login";
            blockedContext.Request.Method = "POST";
            blockedContext.Connection.RemoteIpAddress = ip;

            await middleware.InvokeAsync(blockedContext);

            blockedContext.Response.StatusCode.Should().Be(StatusCodes.Status429TooManyRequests);
            blockedContext.Response.Headers["X-RateLimit-Remaining"].ToString().Should().Be("0");
        }
    }
}
