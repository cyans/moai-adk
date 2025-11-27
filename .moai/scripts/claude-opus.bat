@echo off
setlocal

REM Claude Opus Model Switcher
REM Reverts Claude to use standard Opus models by removing GLM settings

REM Try to find project-specific setup-opus.py first, then fall back to global
set SCRIPT_PATH=
if exist ".moai\scripts\setup-opus.py" (
    set SCRIPT_PATH=.moai\scripts\setup-opus.py
) else if exist "%USERPROFILE%\.local\share\moai-adk\scripts\setup-opus.py" (
    set SCRIPT_PATH=%USERPROFILE%\.local\share\moai-adk\scripts\setup-opus.py
) else (
    echo Error: setup-opus.py not found
    exit /b 1
)

python "%SCRIPT_PATH%"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Starting Claude with Opus models...
claude
