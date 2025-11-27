@echo off
setlocal

REM GLM Model Switcher for Claude
REM Switches Claude to use GLM models by updating global settings

python "%USERPROFILE%\.local\share\moai-adk\scripts\setup-glm.py" %*
if errorlevel 1 exit /b %errorlevel%

echo.
echo Starting Claude with GLM models...
claude
