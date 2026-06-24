using LawyerConnect.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;
using Microsoft.Extensions.Logging.Abstractions;

namespace LawyerConnect.Tests.TestHelpers
{
    public static class TestDbContextFactory
    {
        public static LawyerConnectDbContext Create(bool seed = true)
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(Guid.NewGuid().ToString())
                .ConfigureWarnings(w => w.Ignore(InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            var context = new LawyerConnectDbContext(options);

            if (seed)
            {
                DbSeeder.SeedAsync(context, NullLogger.Instance).GetAwaiter().GetResult();
            }

            return context;
        }
    }
}
