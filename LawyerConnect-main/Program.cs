using System.Text;
using LawyerConnect.Data;
using LawyerConnect.Middlewares;
using LawyerConnect.Repositories;
using LawyerConnect.Services;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

#region --- Create and intialize Builder --- 

// creat the builder from WebApplication 
var builder = WebApplication.CreateBuilder(args);

// Add Basic services into DIcontainer.
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
        options.JsonSerializerOptions.PropertyNameCaseInsensitive = true;
    }); // to map controllers 

builder.Services.AddEndpointsApiExplorer(); // to access end_point by swagger  
builder.Services.AddSwaggerGen(); // to add swagger service 

// Add CORS into DIcontainer
var configuredCorsOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()
    ?? ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"];

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        if (builder.Environment.IsDevelopment())
        {
            policy.SetIsOriginAllowed(origin =>
            {
                if (string.IsNullOrWhiteSpace(origin))
                    return false;

                if (configuredCorsOrigins.Contains(origin, StringComparer.OrdinalIgnoreCase))
                    return true;

                if (!Uri.TryCreate(origin, UriKind.Absolute, out var uri))
                    return false;

                if (uri.Host is "localhost" or "127.0.0.1")
                    return true;

                // Allow LAN devices to reach the API during local development
                return uri.Host.StartsWith("192.168.", StringComparison.Ordinal)
                    || uri.Host.StartsWith("10.", StringComparison.Ordinal);
            });
        }
        else
        {
            policy.WithOrigins(configuredCorsOrigins);
        }

        policy.AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});

// Add DbContext into DIcontainer
builder.Services.AddDbContext<LawyerConnectDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection"))
); // adding DBContext Service 

// Add Repos into DIcontainer 
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<ILawyerRepository, LawyerRepository>();
builder.Services.AddScoped<IBookingRepository, BookingRepository>();
builder.Services.AddScoped<IPaymentSessionRepository, PaymentSessionRepository>();
builder.Services.AddScoped<IRefreshTokenRepository, RefreshTokenRepository>();
builder.Services.AddScoped<ISpecializationRepository, SpecializationRepository>();
builder.Services.AddScoped<IPricingRepository, PricingRepository>();
builder.Services.AddScoped<IChatRoomRepository, ChatRoomRepository>();
builder.Services.AddScoped<IChatMessageRepository, ChatMessageRepository>();
builder.Services.AddScoped<INotificationRepository, NotificationRepository>();
builder.Services.AddScoped<IReviewRepository, ReviewRepository>();

// Add Services into DIcontainer 
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<ILawyerService, LawyerService>();
builder.Services.AddScoped<IBookingService, BookingService>();
builder.Services.AddScoped<IPaymentService, PaymentService>();
builder.Services.AddScoped<ISpecializationService, SpecializationService>();
builder.Services.AddScoped<IPricingService, PricingService>();
builder.Services.AddScoped<INotificationService, NotificationService>();
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<IReviewService, ReviewService>();
builder.Services.AddScoped<IAdminService, AdminService>();
builder.Services.AddScoped<IAIChatService, AIChatService>();
builder.Services.AddHostedService<TokenCleanupService>(); // back-ground-service

// Add HttpClient for AI Backend
builder.Services.AddHttpClient("AIBackend", client =>
{
    var aiBackendUrl = builder.Configuration["AIBackend:BaseUrl"] ?? "http://localhost:8000";
    client.BaseAddress = new Uri(aiBackendUrl);
    client.Timeout = TimeSpan.FromMinutes(5); // AI responses might take time
});

// Configure Stripe
Stripe.StripeConfiguration.ApiKey = builder.Configuration["Stripe:SecretKey"];

// Prepare  JWT
var jwtKey = builder.Configuration["Jwt:Key"] ?? string.Empty;
var jwtIssuer = builder.Configuration["Jwt:Issuer"];
var jwtAudience = builder.Configuration["Jwt:Audience"];
var signingKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtKey));

// Add Authentication Service into DIcontainer
    // we will add an authentication service 
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
        // specialy we will add JwtBearer and specify its configurations 
    .AddJwtBearer(options =>
    {
        //  validation rules هنا هنغير الاعدادت العامه بس مش البوليسي .. المرادي قواعد التحقق 
        options.TokenValidationParameters = new TokenValidationParameters
        {
            // validatoin Param will be checked 
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,

            // checked by these values 
            ValidIssuer = jwtIssuer,
            ValidAudience = jwtAudience,
            IssuerSigningKey = signingKey
        };
    });

// Add authorizaton into DIcontainer
builder.Services.AddAuthorization();


#endregion --- end builder intializtion ---


var app = builder.Build();

// Ensure database is created and migrations are applied
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<LawyerConnectDbContext>();
    var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
    var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
    
    try
    {
        // Extract database name from connection string and create it if it doesn't exist
        var builder2 = new SqlConnectionStringBuilder(connectionString);
        var databaseName = builder2.InitialCatalog;
        builder2.InitialCatalog = "master"; // Connect to master to create database
        
        using (var masterConnection = new SqlConnection(builder2.ConnectionString))
        {
            masterConnection.Open();
            var createDbCommand = new SqlCommand(
                $@"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{databaseName}') 
                CREATE DATABASE [{databaseName}]", masterConnection);
            createDbCommand.ExecuteNonQuery();
            logger.LogInformation($"Database '{databaseName}' ensured to exist.");
        }
        
        // Now migrate the database
        dbContext.Database.Migrate();
        logger.LogInformation("Database migrated successfully.");

        await DbSeeder.SeedAsync(dbContext, logger);
        logger.LogInformation("Database seed data ensured.");
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "An error occurred while creating/migrating the database. Please ensure SQL Server is running and accessible.");
        throw; // Re-throw to prevent app from starting with invalid database state
    }
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// middle ware pipeLine 

app.UseHttpsRedirection(); // Make the connection sequre 
app.UseCors("AllowFrontend"); // allow Front End interact with server 
app.UseMiddleware<RateLimitingMiddleware>(); // use rate limiting first to prevent any spam before any request (register/login) safe 
app.UseAuthentication(); // use authenteiation 
app.UseAuthorization(); // use autherization 

app.MapControllers(); // the end 

app.Run(); // run 
