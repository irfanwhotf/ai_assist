@echo off
title Neura AI Assistant
color 0B

echo.
echo  =======================================
echo    NEURA AI ASSISTANT WITH MEMORY
echo  =======================================
echo.
echo  Starting Neura Voice Assistant...
echo  Press Shift+Spacebar to speak to Neura
echo.
echo  Commands:
echo  - Say "my name is [name]" to set your name
echo  - Say "remember [info]" to store a memory
echo  - Say "list memories" to see what Neura remembers
echo.

:: Change to the correct directory
cd /d C:\ttsopenai

:: Run the assistant
python -m ai_assist.run

echo.
echo  Neura AI Assistant has been closed.
echo.
pause
