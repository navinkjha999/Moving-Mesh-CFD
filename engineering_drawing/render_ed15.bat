@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 15: Points on the Surface of an Oblique Solid
REM  Renders the four scenes in running order at 1080p60.
REM
REM    render_ed15.bat            all four scenes
REM    render_ed15.bat S02        just the one whose name starts with S02
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed15_surface_points.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_WhatMoves S02_ObliqueCylinder S03_ConeAndPyramid S04_Recap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All four scenes rendered. They are under media\videos\ed15_surface_points\1080p60\.
goto :eof

:one
for %%S in (S01_WhatMoves S02_ObliqueCylinder S03_ConeAndPyramid S04_Recap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
