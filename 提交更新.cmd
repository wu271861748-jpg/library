@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
for /f "delims=" %%U in ('git remote get-url origin') do set "ORIGIN=%%U"
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
if not errorlevel 1 goto unchanged
git -c user.name=wu271861748-jpg -c user.email=344054577+wu271861748-jpg@users.noreply.github.com commit -m "Update fixture files" -- fixtures
if errorlevel 1 goto failed
git push origin main
if errorlevel 1 goto failed
echo 上传完成。请在仓库 Actions 查看自动打包结果。
goto done
:unchanged
echo 没有新增或修改的灯库，无需上传。
goto done
:wrongrepo
echo 当前目录不是指定的灯库更新仓库，未上传。
goto done
:failed
echo 操作未完成，请查看上方错误。不会自动覆盖或强制推送。
:done
pause
