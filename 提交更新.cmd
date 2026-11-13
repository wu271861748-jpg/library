@echo off
setlocal
set RC=1
cd /d "%~dp0"
for /f "delims=" %%U in ('git config --get remote.origin.url') do set "ORIGIN=%%U"
if /I not "%ORIGIN%"=="https://github.com/wu271861748-jpg/library.git" goto wrongrepo
git pull --ff-only origin main
if errorlevel 1 goto failed
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" goto bundled
py -3 tools\build_release.py --validate
goto validated
:bundled
"%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\build_release.py --validate
:validated
if errorlevel 1 goto failed
git add -- fixtures
if errorlevel 1 goto failed
git diff --cached --quiet -- fixtures
if errorlevel 2 goto failed
if not errorlevel 1 goto pending
git -c user.name=wu271861748-jpg -c user.email=344054577+wu271861748-jpg@users.noreply.github.com commit -m "Update fixture files" -- fixtures
if errorlevel 1 goto failed
:pending
for /f %%C in ('git rev-list --count origin/main..HEAD') do set "AHEAD=%%C"
if "%AHEAD%"=="0" goto unchanged
git push origin main
if errorlevel 1 goto failed
echo Upload complete. Check GitHub Actions for the release.
set RC=0
goto done
:unchanged
echo No fixture changes. Nothing uploaded.
set RC=0
goto done
:wrongrepo
echo This is not the configured update repository. Nothing uploaded.
goto done
:failed
echo Not completed. See the error above. No force-push or overwrite.
:done
pause
exit /b %RC%
