@echo off
color 0A
echo ================================================================================
echo                    LawyerConnect with AI Integration
echo ================================================================================
echo.
echo Starting all servers in optimal sequence...
echo.

REM 1. Start Python AI Backend (FIRST - other services depend on it)
echo [1/4] Starting Python AI Backend on port 8000...
start "AI Backend (Port 8000)" cmd /k "cd /d "%~dp0" && python main.py"
echo      ^> AI Backend initializing...
timeout /t 5 /nobreak > nul

REM 2. Start .NET Backend (SECOND - website depends on it)
echo [2/4] Starting .NET Backend on port 5128...
start ".NET Backend (Port 5128)" cmd /k "cd /d "%~dp0LawyerConnect-main" && dotnet run"
echo      ^> .NET Backend initializing...
timeout /t 8 /nobreak > nul

REM 3. Start Standalone AI Chat Frontend (THIRD - independent React app)
echo [3/4] Starting Standalone AI Chat on port 3000...
start "Standalone AI Chat (Port 3000)" cmd /k "cd /d "%~dp0react-frontend" && npm start"
echo      ^> Standalone AI Chat starting...
timeout /t 3 /nobreak > nul

REM 4. Start Website Frontend (LAST - main website)
echo [4/4] Starting Website Frontend on port 3002...
start "Website Frontend (Port 3002)" cmd /k "cd /d "%~dp0LawyerConnect-main\FrontEnd" && npm run dev"
echo      ^> Website Frontend starting...

echo.
echo ================================================================================
echo                          All Servers Started!
echo ================================================================================
echo.
echo  Backend Services:
echo  ─────────────────────────────────────────────────────────────────────────────
echo    • AI Backend (Python):        http://localhost:8000
echo    • API Docs (Swagger):         http://localhost:8000/docs
echo    • .NET Backend (C#):          http://localhost:5128
echo.
echo  Frontend Applications:
echo  ─────────────────────────────────────────────────────────────────────────────
echo    • Main Website:               http://localhost:3002
echo    • Standalone AI Chat:         http://localhost:3000
echo.
echo ================================================================================
echo.
echo  Tips:
echo    - Wait 30-60 seconds for all servers to fully initialize
echo    - Open http://localhost:3002 in your browser for the main website
echo    - The AI chat modal in the website connects to the standalone app
echo    - Close individual terminal windows to stop specific servers
echo    - Press any key here to close this launcher (servers will keep running)
echo.
echo ================================================================================
echo.
pause
