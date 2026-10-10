@echo off
chcp 65001 >nul
title CheXiaoZhi API Server
setlocal
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYEXE="
set "PYARGS="

rem ============================================================
rem  NOTE: the interpreter check must verify real OUTPUT,
rem  not just ERRORLEVEL. The 'py' launcher on this machine
rem  prints "Python 3 not found!" yet still returns 0, which
rem  silently hijacked the old detection and made the server
rem  never start. Order is also changed to prefer known-good
rem  interpreters before probing PATH.
rem ============================================================

rem ---- 1) portable python shipped next to this script ----
if exist "%~dp0python\python.exe" (
    set "PYEXE=%~dp0python\python.exe"
    goto run
)

rem ---- 2) DSH bundled runtime (user profile, known good) ----
if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" (
    set "PYEXE=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    goto run
)

rem ---- 3) DSH bundled runtime (portable install dirs) ----
for /d %%D in ("E:\dsh\*") do (
    if exist "%%~fD\resources\runtime\primary-runtime\dependencies\python\python.exe" (
        set "PYEXE=%%~fD\resources\runtime\primary-runtime\dependencies\python\python.exe"
        goto run
    )
)

rem ---- 4) python on PATH -- validated by real output ----
for /f "delims=" %%V in ('python -c "print(987654)" 2^>nul') do (
    if "%%V"=="987654" (
        set "PYEXE=python"
        goto run
    )
)

rem ---- 5) py launcher -- same output validation ----
for /f "delims=" %%V in ('py -3 -c "print(987654)" 2^>nul') do (
    if "%%V"=="987654" (
        set "PYEXE=py"
        set "PYARGS=-3"
        goto run
    )
)

echo.
echo   [ERROR] No working Python interpreter found.
echo   Tried : python\python.exe  /  DSH runtime  /  python on PATH  /  py -3
echo   Hint  : a "python" that prints nothing is a Microsoft Store stub.
echo.
if exist "%~dp0no-python.txt" type "%~dp0no-python.txt"
echo.
pause
exit /b 1

:run
echo   Python : %PYEXE% %PYARGS%
echo   Server : %~dp0server.py
echo.
%PYEXE% %PYARGS% "%~dp0server.py" %* --open
if errorlevel 1 pause
endlocal
