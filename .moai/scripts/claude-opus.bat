@echo off
setlocal

REM Claude Opus Model Switcher
REM Reverts Claude to use standard Opus models by removing GLM settings

python "%USERPROFILE%\.local\share\moai-adk\scripts\setup-opus.py"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Starting Claude with Opus models...
claude
