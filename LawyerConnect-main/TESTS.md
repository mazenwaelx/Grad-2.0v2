# LawyerConnect — Automated Test Documentation

Backend automated tests for the LawyerConnect API. **180 tests** across **22 test classes**, all targeting **.NET 8**.

---

## Quick start

```powershell
cd LawyerConnect

# Recommended — verbose banner, per-test names, TRX report
.\run-tests.ps1

# Standard (minimal output)
dotnet test

# Standard while API is running (avoids bin/ lock)
dotnet test LawyerConnect.Tests/LawyerConnect.Tests.csproj -o $env:TEMP\lawyerconnect-test-run

# Filter one area
.\run-tests.ps1 -Filter "FullyQualifiedName~AuthServiceTests"
dotnet test --filter "FullyQualifiedName~DbSeederTests"
```

> **Tip:** If `dotnet test` fails with *"file is locked by LawyerConnect"*, stop `dotnet run` first **or** use `.\run-tests.ps1` (builds to a temp folder).

---

## Stack

| Tool | Purpose |
|------|---------|
| **xUnit** 2.5 | Test framework |
| **Moq** 4.20 | Mock repositories & services |
| **FluentAssertions** 8.9 | Readable assertions |
| **EF Core InMemory** 8.0 | Real DbContext without SQL Server |
| **coverlet.collector** | Code coverage collection |

---

## Project layout

```
LawyerConnect.Tests/
├── TestHelpers/           # Shared DB factory, config, password hashing
├── Data/                  # DbSeeder tests
├── Services/              # Business logic (largest suite)
├── Repositories/          # Data access integration-style tests
├── Mappers/               # DTO ↔ entity mapping
├── Controllers/           # API controller unit tests
└── Middlewares/           # Rate limiting
```

---

## Test inventory (180 tests)

### Data (3 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Data/DbSeederTests.cs` | 3 | Seeds 7 specializations + 4 interaction types; idempotent; stable IDs |

### Services (123 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Services/AuthServiceTests.cs` | 9 | Register (user/lawyer), login, refresh token rotation, replay detection, logout |
| `Services/AdminServiceTests.cs` | 13 | User/lawyer admin actions, verify/reject, suspend, pagination |
| `Services/BookingServiceTests.cs` | 14 | Create, status transitions, cancel, complete, validation |
| `Services/ChatServiceTests.cs` | 12 | Rooms, messages, archive, authorization |
| `Services/LawyerServiceTests.cs` | 18 | Register, search, verify, pagination, **featured lawyers** |
| `Services/NotificationServiceTests.cs` | 9 | Create, list, mark read, unread count |
| `Services/PaymentServiceTests.cs` | 9 | Confirm, refund, get sessions (Stripe skipped when not configured) |
| `Services/PricingServiceTests.cs` | 13 | CRUD, validation, duplicate detection |
| `Services/ReviewServiceTests.cs` | 12 | Create, list, average rating, admin delete |
| `Services/SpecializationServiceTests.cs` | 12 | Full CRUD + duplicate name guards |
| `Services/UserServiceTests.cs` | 14 | Register, role update, pagination |
| `Services/TokenCleanupServiceTests.cs` | 1 | Background token cleanup job runs |
| `Services/ServiceCoverageGapTests.cs` | 5 | Delete/mark-all notifications, featured reviews, user bookings, unsuspend |

### Repositories (20 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Repositories/UserRepositoryTests.cs` | 3 | CRUD, email lookup, pagination |
| `Repositories/LawyerRepositoryTests.cs` | 4 | Includes (user, specializations), paging |
| `Repositories/BookingRepositoryTests.cs` | 4 | User/lawyer bookings, date overlap |
| `Repositories/RefreshTokenRepositoryTests.cs` | 3 | Add, revoke, revoke-all, delete old |
| `Repositories/RemainingRepositoryTests.cs` | 6 | Specialization, Pricing, Review, Notification, PaymentSession, Chat repos |

### Mappers (9 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Mappers/MapperTests.cs` | 9 | User, Lawyer, Booking, Pricing, Specialization, Review, Notification, Payment, Chat mappers |

### Controllers (5 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Controllers/ControllerTests.cs` | 5 | Auth register, InteractionTypes GET, Lawyers featured, Specializations GET |

### Middlewares (2 tests)

| File | Tests | What it verifies |
|------|-------|------------------|
| `Middlewares/RateLimitingMiddlewareTests.cs` | 2 | Exempt paths, 429 when auth limit exceeded |

---

## Coverage map

```
┌─────────────────────────────────────────────────────────────┐
│  COVERED                                                    │
├─────────────────────────────────────────────────────────────┤
│  ✅ All 12 services (incl. Auth + TokenCleanup)             │
│  ✅ All 11 repositories                                     │
│  ✅ All 9 mappers                                           │
│  ✅ DbSeeder                                                │
│  ✅ RateLimitingMiddleware                                  │
│  ⚠️  4 of 11 controllers (smoke/delegation tests)           │
├─────────────────────────────────────────────────────────────┤
│  NOT COVERED YET                                            │
├─────────────────────────────────────────────────────────────┤
│  ❌ Full controller suite (Bookings, Chat, Payments, etc.)  │
│  ❌ Stripe CreateSession / Webhook (needs abstraction)      │
│  ❌ API integration tests (WebApplicationFactory)           │
│  ❌ Frontend (React / Vitest)                               │
│  ❌ CI pipeline (GitHub Actions)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Conventions

- **Naming:** `MethodName_Scenario_ExpectedOutcome`
- **Structure:** Arrange → Act → Assert
- **DB tests:** Fresh InMemory database per test class (`Guid.NewGuid()`)
- **Seeded data:** `TestDbContextFactory.Create()` runs `DbSeeder` by default

---

## Test helpers

| Helper | Location | Purpose |
|--------|----------|---------|
| `TestDbContextFactory` | `TestHelpers/TestDbContextFactory.cs` | InMemory `LawyerConnectDbContext` + optional seed |
| `TestConfigurationFactory` | `TestHelpers/TestConfigurationFactory.cs` | JWT, Stripe, rate-limit config for tests |
| `PasswordHasher` | `TestHelpers/PasswordHasher.cs` | SHA256 hash matching `AuthService` |

---

## Output & reports

| Command | Console detail | Report file |
|---------|----------------|-------------|
| `dotnet test` | Minimal (pass/fail count) | — |
| `.\run-tests.ps1` | **Detailed** — every test name | `%TEMP%\lawyerconnect-test-run\results\TestResults.trx` |
| `dotnet test --logger "console;verbosity=detailed"` | Per-test lines | — |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `LawyerConnect.exe` locked | Stop `dotnet run` or use `.\run-tests.ps1` |
| Tests pass locally but DB fails in app | Tests use InMemory DB, not SQL Server |
| Pricing tests need interaction types | `PricingServiceTests` seeds `LawyerSpecializations` in setup |

---

## Related files

- `LawyerConnect.Tests/LawyerConnect.Tests.csproj` — test project definition
- `LawyerConnect.Tests/xunit.runner.json` — xUnit runner display options
- `run-tests.ps1` — verbose test runner script
- `LawyerConnect.postman_collection.json` — manual API testing (not automated)
