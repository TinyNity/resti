@echo off
setlocal

for /F "delims=#" %%E in ('"prompt #$E# & for %%A in (1) do rem"') do set "ESC=%%E"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "CYAN=%ESC%[36m"
set "RESET=%ESC%[0m"

set "ROOT=%~dp0"
set "DIST=%ROOT%dist"

echo(
echo  %BOLD%%CYAN%RESTI%RESET%  %DIM%build%RESET%
echo(

echo  %CYAN%^>%RESET% installing dependencies
py -m pip install --quiet pyinstaller customtkinter
if errorlevel 1 goto :deps_failed
echo    %GREEN%ok%RESET%
echo(

echo  %CYAN%^>%RESET% compiling Resti.exe
py -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --clean ^
  --name "Resti" ^
  --icon "%ROOT%icon.ico" ^
  --paths "%ROOT%src" ^
  --collect-data customtkinter ^
  --distpath "%DIST%" ^
  --workpath "%ROOT%build" ^
  --specpath "%ROOT%build" ^
  "%ROOT%src\resti\__main__.py"
if errorlevel 1 goto :build_failed
if not exist "%DIST%\Resti.exe" goto :build_failed
echo    %GREEN%ok%RESET%
echo(

echo  %GREEN%%BOLD%[OK]%RESET%%GREEN% build succeeded%RESET%
echo    %DIM%executable%RESET%  %DIST%\Resti.exe
echo    %DIM%snapshots %RESET%  %APPDATA%\Resti\snapshots.json
echo(
pause
exit /b 0

:deps_failed
echo    %RED%%BOLD%[FAILED]%RESET%%RED% could not install pyinstaller / customtkinter%RESET%
echo    %DIM%check that 'py' is on PATH and that pip can reach the network%RESET%
echo(
pause
exit /b 1

:build_failed
echo    %RED%%BOLD%[FAILED]%RESET%%RED% PyInstaller did not produce Resti.exe%RESET%
echo    %DIM%scroll up for the compiler output%RESET%
echo(
pause
exit /b 1
