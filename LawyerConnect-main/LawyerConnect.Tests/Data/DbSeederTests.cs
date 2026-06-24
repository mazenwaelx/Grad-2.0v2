using FluentAssertions;
using LawyerConnect.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace LawyerConnect.Tests.Data
{
    public class DbSeederTests : IDisposable
    {
        private readonly LawyerConnectDbContext _context;
        private readonly ILogger _logger = NullLogger.Instance;

        public DbSeederTests()
        {
            var options = new DbContextOptionsBuilder<LawyerConnectDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .ConfigureWarnings(x => x.Ignore(Microsoft.EntityFrameworkCore.Diagnostics.InMemoryEventId.TransactionIgnoredWarning))
                .Options;

            _context = new LawyerConnectDbContext(options);
        }

        [Fact]
        public async Task SeedAsync_WhenDatabaseIsEmpty_SeedsSpecializationsAndInteractionTypes()
        {
            await DbSeeder.SeedAsync(_context, _logger);

            var specializations = await _context.Specializations.OrderBy(s => s.Id).ToListAsync();
            var interactionTypes = await _context.InteractionTypes.OrderBy(i => i.Id).ToListAsync();

            specializations.Should().HaveCount(DbSeeder.DefaultSpecializations.Count);
            interactionTypes.Should().HaveCount(DbSeeder.DefaultInteractionTypes.Count);

            specializations.Select(s => s.Name).Should().ContainInOrder(
                "Criminal Law",
                "Corporate Law",
                "Family Law",
                "Real Estate",
                "Immigration",
                "Tax Law",
                "Employment Law");

            interactionTypes.Select(i => i.Name).Should().ContainInOrder(
                "Consultation",
                "Court Representation",
                "Phone Consultation",
                "Chat");
        }

        [Fact]
        public async Task SeedAsync_WhenCalledTwice_DoesNotDuplicateRows()
        {
            await DbSeeder.SeedAsync(_context, _logger);
            await DbSeeder.SeedAsync(_context, _logger);

            (await _context.Specializations.CountAsync()).Should().Be(DbSeeder.DefaultSpecializations.Count);
            (await _context.InteractionTypes.CountAsync()).Should().Be(DbSeeder.DefaultInteractionTypes.Count);
        }

        [Fact]
        public async Task SeedAsync_PreservesStableSpecializationIds()
        {
            await DbSeeder.SeedAsync(_context, _logger);

            var criminalLaw = await _context.Specializations.SingleAsync(s => s.Name == "Criminal Law");
            criminalLaw.Id.Should().Be(1);
        }

        public void Dispose()
        {
            _context.Dispose();
        }
    }
}
