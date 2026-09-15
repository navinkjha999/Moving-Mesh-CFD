@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 13: Points on the Surface of a Solid
REM  Renders the four scenes in running order at 1080p60.
REM
REM    render_ed13.bat            all four scenes
REM    render_ed13.bat S02        just the one whose name starts with S02
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed13_points.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_OnTheSurface S02_Cylinder S03_Pyramid S04_Recap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All four scenes rendered. They are under media\videos\ed13_points\1080p60\.
goto :eof

:one
for %%S in (S01_OnTheSurface S02_Cylinder S03_Pyramid S04_Recap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
