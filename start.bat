@echo off
cls
echo.
echo ================================================================================
echo                    Bussiness Contract Search System
echo                Production-Ready AI Contract Analysis
echo ================================================================================
echo.
echo         Built with Gemini AI, FAISS, and FastAPI
echo.
echo ================================================================================
echo.
echo What would you like to do?
echo.
echo   [1] Setup Environment (First time only)
echo   [2] Run Application
echo   [3] Open Documentation
echo   [4] Run Tests
echo   [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto run
if "%choice%"=="3" goto docs
if "%choice%"=="4" goto test
if "%choice%"=="5" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto start

:setup
echo.
echo ========================================
echo Setting up environment...
echo ========================================
call setup.bat
pause
goto start

:run
echo.
echo ========================================
echo Starting application...
echo ========================================
echo.
if not exist .env (
    echo ERROR: .env file not found!
    echo Please run Setup first and configure your API key.
    echo.
    pause
    goto start
)
call run.bat
goto end

:docs
echo.
echo ========================================
echo Opening documentation...
echo ========================================
echo.
echo Available documentation:
echo   - README.md (Project overview)
echo   - QUICKSTART.md (5-minute setup)
echo   - API.md (API reference)
echo   - DEPLOYMENT.md (Deployment guide)
echo   - ARCHITECTURE.md (Technical details)
echo   - PROJECT_SUMMARY.md (Complete guide)
echo.
start README.md
pause
goto start

:test
echo.
echo ========================================
echo Running tests...
echo ========================================
call venv\Scripts\activate
pytest tests/ -v
pause
goto start

:end
echo.
echo Goodbye!
timeout /t 1 >nul
