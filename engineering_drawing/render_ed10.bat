@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 10: Section, True Shape and Development
REM  Renders the five scenes in running order at 1080p60.
REM
REM    render_ed10.bat            all five scenes
REM    render_ed10.bat S03        just the one whose name starts with S03
REM
REM  Run it once with EFS_SILENT=1 set if you want to check the timing and the
REM  layout without waiting on the text-to-speech.
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed10_development.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_Unroll S02_TheCut S03_TrueShape S04_Development S05_Recap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All five scenes rendered. They are under media\videos\ed10_development\1080p60\.
goto :eof

:one
for %%S in (S01_Unroll S02_TheCut S03_TrueShape S04_Development S05_Recap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
