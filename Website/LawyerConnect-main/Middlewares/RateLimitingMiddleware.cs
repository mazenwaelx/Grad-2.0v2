using System.Collections.Concurrent;

namespace LawyerConnect.Middlewares
{
    public class RateLimitingMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly int _limit;
        private readonly TimeSpan _window;
        private static readonly ConcurrentDictionary<string, List<DateTime>> Requests = new();

        public RateLimitingMiddleware(RequestDelegate next, IConfiguration config)
        {
            _next = next;
            _limit = config.GetValue<int>("RateLimiting:Limit", 5);
            var windowSeconds = config.GetValue<int>("RateLimiting:WindowSeconds", 60);
            _window = TimeSpan.FromSeconds(windowSeconds);
        }

        public async Task InvokeAsync(HttpContext context)
        {
            var path = context.Request.Path.Value?.ToLowerInvariant() ?? "";
            var method = context.Request.Method.ToUpperInvariant();

            // Exempt endpoints from rate limiting
            if (path.Contains("/api/chat") || 
                path.Contains("/api/specializations") || 
                path.Contains("/api/interactiontypes"))
            {
                await _next(context);
                return;
            }

            // Determine rate limit based on endpoint type
            int effectiveLimit = _limit;
            
            // Higher limit for pricing endpoints (20 requests/60s)
            if (path.Contains("/api/lawyers") && path.Contains("/pricing"))
            {
                effectiveLimit = 20;
            }
            // Higher limit for GET requests to lawyers (30 requests/60s)
            else if (path.Contains("/api/lawyers") && method == "GET")
            {
                effectiveLimit = 30;
            }
            // Standard limit for auth endpoints (5 requests/60s)
            else if (path.Contains("/api/auth"))
            {
                effectiveLimit = 5;
            }
            // Medium limit for other endpoints (10 requests/60s)
            else
            {
                effectiveLimit = 10;
            }

            var key = $"{context.Connection.RemoteIpAddress}-{context.Request.Path.Value}".ToLowerInvariant();
            var now = DateTime.UtcNow;

            var entries = Requests.GetOrAdd(key, _ => new List<DateTime>());

            lock (entries)
            {
                entries.RemoveAll(t => t <= now - _window);
                if (entries.Count >= effectiveLimit)
                {
                    var reset = entries.First() + _window;
                    context.Response.StatusCode = StatusCodes.Status429TooManyRequests;
                    context.Response.Headers["X-RateLimit-Limit"] = effectiveLimit.ToString();
                    context.Response.Headers["X-RateLimit-Remaining"] = "0";
                    context.Response.Headers["X-RateLimit-Reset"] = ((long)(reset - now).TotalSeconds).ToString();
                    return;
                }
                entries.Add(now);
                context.Response.Headers["X-RateLimit-Limit"] = effectiveLimit.ToString();
                context.Response.Headers["X-RateLimit-Remaining"] = (effectiveLimit - entries.Count).ToString();
                context.Response.Headers["X-RateLimit-Reset"] = ((long)_window.TotalSeconds).ToString();
            }

            await _next(context);
        }
    }
}

