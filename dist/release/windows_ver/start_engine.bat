@echo off
setlocal

:: 定义Python解释器和脚本的路径
set PYTHON_EXE_PATH="python_lib/python-3.9.6-embed-amd64/python.exe"
set PYTHON_SCRIPT_PATH="code/npc_engine/src/engine.py"

:: 检查Python解释器是否存在
if not exist %PYTHON_EXE_PATH% (
    echo Python interpreter not found at %PYTHON_EXE_PATH%.
    exit /b 1
)

:: 检查Python脚本是否存在
if not exist %PYTHON_SCRIPT_PATH% (
    echo Python script not found at %PYTHON_SCRIPT_PATH%.
    exit /b 1
)

:: 启动Python脚本
echo Starting Python script...
start /b %PYTHON_EXE_PATH% %PYTHON_SCRIPT_PATH%

:: 获取Python进程的PID
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do set PID=%%i

:: 等待用户输入任何字符来结束Python进程
echo Press any key to stop the Python script...
pause >nul

:: 结束Python进程
echo Stopping Python script...
taskkill /F /PID %PID%

:: 结束脚本
endlocal
echo Script finished.

