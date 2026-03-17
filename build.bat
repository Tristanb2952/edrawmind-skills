@echo off
REM Build script for Windows — packages edrawmind-mindmap skill into a zip.
REM Usage: build.bat [options]
REM   build.bat              Build dist/edrawmind-mindmap.zip
REM   build.bat --list       List files only (dry run)
REM   build.bat -o out.zip   Custom output path

cd /d "%~dp0"
python scripts\build.py %*
