
using LawyerConnect.Models;
using Microsoft.EntityFrameworkCore;

namespace LawyerConnect.Data
{
    public class LawyerConnectDbContext : DbContext
    {
        public LawyerConnectDbContext(DbContextOptions<LawyerConnectDbContext> options) : base(options) {}

        public DbSet<User> Users { get; set; }
        public DbSet<Lawyer> Lawyers { get; set; }
        public DbSet<Booking> Bookings { get; set; }
        public DbSet<PaymentSession> PaymentSessions { get; set; }
        public DbSet<RefreshToken> RefreshTokens { get; set; }
        public DbSet<Specialization> Specializations { get; set; }
        public DbSet<InteractionType> InteractionTypes { get; set; }
        public DbSet<LawyerSpecialization> LawyerSpecializations { get; set; }
        public DbSet<LawyerPricing> LawyerPricings { get; set; }
        public DbSet<Review> Reviews { get; set; }
        public DbSet<Notification> Notifications { get; set; }
        public DbSet<ChatRoom> ChatRooms { get; set; }
        public DbSet<ChatMessage> ChatMessages { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<User>()
                .HasIndex(u => u.Email)
                .IsUnique();

            modelBuilder.Entity<Lawyer>()
                .HasIndex(l => l.UserId)
                .IsUnique();

            modelBuilder.Entity<Lawyer>()
                .HasOne(l => l.User)
                .WithOne(u => u.LawyerProfile)
                .HasForeignKey<Lawyer>(l => l.UserId);

            modelBuilder.Entity<Booking>()
                .HasOne(b => b.User)
                .WithMany(u => u.Bookings)
                .HasForeignKey(b => b.UserId)
                .OnDelete(DeleteBehavior.Restrict); // prevent 2 cascade delete path , the logic even user delete keep the booking as a history 

            modelBuilder.Entity<Booking>()
                .HasOne(b => b.Lawyer)
                .WithMany(l => l.Bookings)
                .HasForeignKey(b => b.LawyerId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<PaymentSession>()
                .HasIndex(p => p.BookingId)
                .IsUnique();

            modelBuilder.Entity<PaymentSession>()
                .HasOne(p => p.Booking)
                .WithOne(b => b.PaymentSession)
                .HasForeignKey<PaymentSession>(p => p.BookingId);



                modelBuilder.Entity<Lawyer>()
                .Property(l => l.Latitude)
                .HasColumnType("decimal(10,8)");

                modelBuilder.Entity<Lawyer>()
                .Property(l => l.Longitude)
                .HasColumnType("decimal(10,8)");

                modelBuilder.Entity<PaymentSession>()
                .Property(p => p.Amount)
                .HasColumnType("decimal(18,2)");

                modelBuilder.Entity<RefreshToken>()
                .HasOne(r => r.User)                
                .WithMany(u => u.Refreshtokns)     
                .HasForeignKey(r => r.UserId)
                .OnDelete(DeleteBehavior.Cascade); 


                modelBuilder.Entity<RefreshToken>()
                .HasOne(r => r.Refreshtoken)     
                .WithOne()                        
                .HasForeignKey<RefreshToken>(r => r.ReplacedByTokenId)
                .OnDelete(DeleteBehavior.Restrict); // because protect chain 

                modelBuilder.Entity<RefreshToken>()
                .HasIndex(r => r.TokenHash)
                .IsUnique();


                modelBuilder.Entity<RefreshToken>()
                .Property(r => r.TokenHash)
                .HasMaxLength(512)
                .IsRequired();

                modelBuilder.Entity<RefreshToken>()
                .Property(r=>r.Revoked)
                .HasDefaultValue(false);

            // Specialization configuration
            modelBuilder.Entity<Specialization>()
                .HasMany(s => s.Lawyers)
                .WithOne(ls => ls.Specialization)
                .HasForeignKey(ls => ls.SpecializationId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Specialization>()
                .HasMany(s => s.Pricing)
                .WithOne(lp => lp.Specialization)
                .HasForeignKey(lp => lp.SpecializationId)
                .OnDelete(DeleteBehavior.Cascade);

            // InteractionType configuration
            modelBuilder.Entity<InteractionType>()
                .HasMany(it => it.Pricing)
                .WithOne(lp => lp.InteractionType)
                .HasForeignKey(lp => lp.InteractionTypeId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<InteractionType>()
                .HasMany(it => it.Bookings)
                .WithOne(b => b.InteractionType)
                .HasForeignKey(b => b.InteractionTypeId)
                .OnDelete(DeleteBehavior.Restrict);

            // LawyerSpecialization configuration (join table)
            modelBuilder.Entity<LawyerSpecialization>()
                .HasKey(ls => new { ls.LawyerId, ls.SpecializationId });

            modelBuilder.Entity<LawyerSpecialization>()
                .HasOne(ls => ls.Lawyer)
                .WithMany(l => l.Specializations)
                .HasForeignKey(ls => ls.LawyerId)
                .OnDelete(DeleteBehavior.Cascade);

            // LawyerPricing configuration (composite key)
            modelBuilder.Entity<LawyerPricing>()
                .HasKey(lp => new { lp.LawyerId, lp.SpecializationId, lp.InteractionTypeId });

            modelBuilder.Entity<LawyerPricing>()
                .HasOne(lp => lp.Lawyer)
                .WithMany(l => l.Pricing)
                .HasForeignKey(lp => lp.LawyerId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<LawyerPricing>()
                .Property(lp => lp.Price)
                .HasColumnType("decimal(18,2)");

            // Booking configuration - add Specialization and InteractionType relationships
            modelBuilder.Entity<Booking>()
                .HasOne(b => b.Specialization)
                .WithMany()
                .HasForeignKey(b => b.SpecializationId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Booking>()
                .HasOne(b => b.InteractionType)
                .WithMany(it => it.Bookings)
                .HasForeignKey(b => b.InteractionTypeId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Booking>()
                .Property(b => b.PriceSnapshot)
                .HasColumnType("decimal(18,2)");

            // Review configuration
            modelBuilder.Entity<Review>()
                .HasIndex(r => r.BookingId)
                .IsUnique();

            modelBuilder.Entity<Review>()
                .HasOne(r => r.Booking)
                .WithOne(b => b.Review)
                .HasForeignKey<Review>(r => r.BookingId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<Review>()
                .HasOne(r => r.User)
                .WithMany(u => u.Reviews)
                .HasForeignKey(r => r.UserId)
                .OnDelete(DeleteBehavior.Restrict);

            modelBuilder.Entity<Review>()
                .HasOne(r => r.Lawyer)
                .WithMany(l => l.Reviews)
                .HasForeignKey(r => r.LawyerId)
                .OnDelete(DeleteBehavior.Cascade);

            // Notification configuration
            modelBuilder.Entity<Notification>()
                .HasOne(n => n.User)
                .WithMany(u => u.Notifications)
                .HasForeignKey(n => n.UserId)
                .OnDelete(DeleteBehavior.Cascade);

            // ChatRoom configuration
            modelBuilder.Entity<ChatRoom>()
                .HasIndex(cr => cr.BookingId)
                .IsUnique();

            modelBuilder.Entity<ChatRoom>()
                .HasOne(cr => cr.Booking)
                .WithOne(b => b.ChatRoom)
                .HasForeignKey<ChatRoom>(cr => cr.BookingId)
                .OnDelete(DeleteBehavior.Cascade);

            // ChatMessage configuration
            modelBuilder.Entity<ChatMessage>()
                .HasOne(cm => cm.ChatRoom)
                .WithMany(cr => cr.Messages)
                .HasForeignKey(cm => cm.ChatRoomId)
                .OnDelete(DeleteBehavior.Cascade);

            modelBuilder.Entity<ChatMessage>()
                .HasOne(cm => cm.Sender)
                .WithMany(u => u.ChatMessages)
                .HasForeignKey(cm => cm.SenderId)
                .OnDelete(DeleteBehavior.Restrict);
        }
    }
}