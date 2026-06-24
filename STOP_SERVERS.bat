@echo off
color 0C
echo ================================================================================
echo                    Stopping All LawyerConnect Servers
echo ================================================================================
echo.

echo Stopping servers...
echo.

REM Kill Python AI Backend (port 8000)
echo [1/4] Stopping AI Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill .NET Backend (port 5128)
echo [2/4] Stopping .NET Backend (port 5128)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5128 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill Standalone AI Chat (port 3000)
echo [3/4] Stopping Standalone AI Chat (port 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill Website Frontend (port 3002)
echo [4/4] Stopping Website Frontend (port 3002)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3002 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ================================================================================
echo                          All Servers Stopped!
echo ================================================================================
echo.
pause
