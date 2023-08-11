@echo off
setlocal enabledelayedexpansion

:: 定义Python解释器和脚本的路径
set PYTHON_EXE_PATH="python_lib/python-3.9.6-embed-amd64/python.exe"
set PYTHON_SCRIPT_PATH="code/npc_engine/src/engine.py"

:: 检查Python解释器是否存在
if not exist %PYTHON_EXE_PATH% (
    echo Python interpreter not found at %PYTHON_EXE_PATH%.
    goto waitForExit
)

:: 检查Python脚本是否存在
if not exist %PYTHON_SCRIPT_PATH% (
    echo Python script not found at %PYTHON_SCRIPT_PATH%.
    goto waitForExit
)

:: 启动Python脚本
echo Starting Python script...
%PYTHON_EXE_PATH% %PYTHON_SCRIPT_PATH%
if !ERRORLEVEL! NEQ 0 goto waitForExit

:: 获取Python进程的PID
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do set PID=%%i
if !ERRORLEVEL! NEQ 0 goto waitForExit

:: 等待用户输入q来结束Python进程
:loop
set "key="
for /F "delims=" %%I in ('xcopy /L /W "%~f0" "%~f0" 2^>nul') do if not defined key set "key=%%I"
if /I "%key:~-1%" NEQ "q" goto loop

:: 检查Python进程是否存在
tasklist /FI "PID eq %PID%" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping Python script...
    taskkill /F /PID %PID%
    if !ERRORLEVEL! NEQ 0 goto waitForExit
) else (
    echo Python script already stopped.
)

:: 结束脚本
endlocal
echo Script finished.
goto end

:waitForExit
echo An error occurred. Press 'q' to exit...
goto loop

:end
