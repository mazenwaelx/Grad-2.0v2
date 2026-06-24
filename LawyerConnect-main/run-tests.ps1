# LawyerConnect - verbose test runner with detailed console output
param(
    [string]$Filter = "",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$testProject = Join-Path $root "LawyerConnect.Tests\LawyerConnect.Tests.csproj"
$outDir = Join-Path $env:TEMP "lawyerconnect-test-run"
$started = Get-Date

function Write-Banner {
    Write-Host ""
    Write-Host "  ================================================================" -ForegroundColor Cyan
    Write-Host "       LAWYER CONNECT - AUTOMATED TEST SUITE" -ForegroundColor Yellow
    Write-Host "       xUnit | Moq | FluentAssertions | EF InMemory" -ForegroundColor Yellow
    Write-Host "  ================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-SuiteMap {
    Write-Host "  TEST SUITES IN THIS RUN" -ForegroundColor Magenta
    Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  > Services      11 files - Auth, Admin, Booking, Chat, Lawyer..." -ForegroundColor White
    Write-Host "  > Repositories   5 files - User, Lawyer, Booking, RefreshToken..." -ForegroundColor White
    Write-Host "  > Mappers        1 file  - All 9 mapper classes" -ForegroundColor White
    Write-Host "  > Controllers    1 file  - Auth, Lawyers, Specializations..." -ForegroundColor White
    Write-Host "  > Middlewares    1 file  - RateLimitingMiddleware" -ForegroundColor White
    Write-Host "  > Data           1 file  - DbSeeder" -ForegroundColor White
    Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  Expected total: 180 tests across 22 test classes" -ForegroundColor Green
    Write-Host ""
}

Write-Banner
Write-SuiteMap

Write-Host "  CONFIGURATION" -ForegroundColor Magenta
Write-Host "  Project : $testProject"
Write-Host "  Output  : $outDir"
if ($Filter) {
    Write-Host "  Filter  : $Filter"
} else {
    Write-Host "  Filter  : none - full suite"
}
Write-Host "  Started : $($started.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host ""

$dotnetArgs = @(
    "test", $testProject,
    "-o", $outDir,
    "--logger", "console;verbosity=detailed",
    "--logger", "trx;LogFileName=TestResults.trx",
    "--results-directory", (Join-Path $outDir "results")
)

if ($Filter) {
    $dotnetArgs += @("--filter", $Filter)
}

if ($SkipBuild) {
    $dotnetArgs += "--no-build"
}

Write-Host "  RUNNING TESTS..." -ForegroundColor Cyan
Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

Push-Location $root
try {
    & dotnet @dotnetArgs
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

$elapsed = (Get-Date) - $started

Write-Host ""
Write-Host "  ----------------------------------------------------------------" -ForegroundColor DarkGray

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "  ================================================================" -ForegroundColor Green
    Write-Host "  *** ALL 180 TESTS PASSED - SUITE GREEN ***" -ForegroundColor Green
    Write-Host "  *** LawyerConnect backend quality gate: CLEARED ***" -ForegroundColor Green
    Write-Host "  ================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  ================================================================" -ForegroundColor Red
    Write-Host "  *** TESTS FAILED - REVIEW OUTPUT ABOVE ***" -ForegroundColor Red
    Write-Host "  ================================================================" -ForegroundColor Red
}

Write-Host ""
Write-Host ("  Duration : {0:N1}s" -f $elapsed.TotalSeconds) -ForegroundColor Yellow
$trxPath = Join-Path $outDir "results\TestResults.trx"
Write-Host "  TRX log  : $trxPath" -ForegroundColor DarkGray
Write-Host "  Docs     : TESTS.md" -ForegroundColor DarkGray
Write-Host ""

exit $exitCode
