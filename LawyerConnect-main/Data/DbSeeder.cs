using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace LawyerConnect.Data
{
    public static class DbSeeder
    {
        public static readonly IReadOnlyList<(int Id, string Name, string Description)> DefaultSpecializations =
        [
            (1, "Criminal Law", "Defense, prosecution, and criminal proceedings"),
            (2, "Corporate Law", "Business formation, contracts, and compliance"),
            (3, "Family Law", "Divorce, custody, and family matters"),
            (4, "Real Estate", "Property transactions, leases, and disputes"),
            (5, "Immigration", "Visas, residency, and citizenship"),
            (6, "Tax Law", "Tax planning, disputes, and compliance"),
            (7, "Employment Law", "Workplace rights, contracts, and disputes"),
        ];

        public static readonly IReadOnlyList<(int Id, string Name)> DefaultInteractionTypes =
        [
            (1, "Consultation"),
            (2, "Court Representation"),
            (3, "Phone Consultation"),
            (4, "Chat"),
        ];

        public static async Task SeedAsync(
            LawyerConnectDbContext context,
            ILogger logger,
            CancellationToken cancellationToken = default)
        {
            await SeedSpecializationsAsync(context, logger, cancellationToken);
            await SeedInteractionTypesAsync(context, logger, cancellationToken);
        }

        private static async Task SeedSpecializationsAsync(
            LawyerConnectDbContext context,
            ILogger logger,
            CancellationToken cancellationToken)
        {
            if (await context.Specializations.AnyAsync(cancellationToken))
            {
                logger.LogInformation("Specializations already present, skipping seed.");
                return;
            }

            if (context.Database.IsSqlServer())
            {
                await context.Database.ExecuteSqlRawAsync(
                    """
                    SET IDENTITY_INSERT Specializations ON;
                    INSERT INTO Specializations (Id, Name, Description) VALUES
                    (1, N'Criminal Law', N'Defense, prosecution, and criminal proceedings'),
                    (2, N'Corporate Law', N'Business formation, contracts, and compliance'),
                    (3, N'Family Law', N'Divorce, custody, and family matters'),
                    (4, N'Real Estate', N'Property transactions, leases, and disputes'),
                    (5, N'Immigration', N'Visas, residency, and citizenship'),
                    (6, N'Tax Law', N'Tax planning, disputes, and compliance'),
                    (7, N'Employment Law', N'Workplace rights, contracts, and disputes');
                    SET IDENTITY_INSERT Specializations OFF;
                    """,
                    cancellationToken);
            }
            else
            {
                foreach (var (id, name, description) in DefaultSpecializations)
                {
                    context.Specializations.Add(new Specialization
                    {
                        Id = id,
                        Name = name,
                        Description = description
                    });
                }

                await context.SaveChangesAsync(cancellationToken);
            }

            logger.LogInformation("Seeded {Count} specializations.", DefaultSpecializations.Count);
        }

        private static async Task SeedInteractionTypesAsync(
            LawyerConnectDbContext context,
            ILogger logger,
            CancellationToken cancellationToken)
        {
            if (await context.InteractionTypes.AnyAsync(cancellationToken))
            {
                logger.LogInformation("Interaction types already present, skipping seed.");
                return;
            }

            if (context.Database.IsSqlServer())
            {
                await context.Database.ExecuteSqlRawAsync(
                    """
                    SET IDENTITY_INSERT InteractionTypes ON;
                    INSERT INTO InteractionTypes (Id, Name) VALUES
                    (1, N'Consultation'),
                    (2, N'Court Representation'),
                    (3, N'Phone Consultation'),
                    (4, N'Chat');
                    SET IDENTITY_INSERT InteractionTypes OFF;
                    """,
                    cancellationToken);
            }
            else
            {
                foreach (var (id, name) in DefaultInteractionTypes)
                {
                    context.InteractionTypes.Add(new InteractionType
                    {
                        Id = id,
                        Name = name
                    });
                }

                await context.SaveChangesAsync(cancellationToken);
            }

            logger.LogInformation("Seeded {Count} interaction types.", DefaultInteractionTypes.Count);
        }
    }
}
