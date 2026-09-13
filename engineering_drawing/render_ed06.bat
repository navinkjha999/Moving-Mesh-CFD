@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 06: True Shape of an Oblique Plane
REM  Renders the five scenes in running order at 1080p60.
REM
REM    render_ed06.bat            all five scenes
REM    render_ed06.bat S04        just the one whose name starts with S04
REM
REM  Run it once with EFS_SILENT=1 set if you want to check the timing and the
REM  layout without waiting on the text-to-speech.
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed06_true_shape.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_WhyBothViewsLie S02_EdgeViewIdea S03_Strategy S04_Construction S05_Recap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All five scenes rendered. They are under media\videos\ed06_true_shape\1080p60\.
goto :eof

:one
for %%S in (S01_WhyBothViewsLie S02_EdgeViewIdea S03_Strategy S04_Construction S05_Recap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
