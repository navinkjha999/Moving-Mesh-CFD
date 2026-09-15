@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 14: Oblique Solids - development by triangulation
REM  Renders the five scenes in running order at 1080p60.
REM
REM    render_ed14.bat            all five scenes
REM    render_ed14.bat S02        just the one whose name starts with S02
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed14_oblique.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_WhatIsOblique S02_Triangulation S03_SheetB S04_DevelopmentB S05_ConeAndRecap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All five scenes rendered. They are under media\videos\ed14_oblique\1080p60\.
goto :eof

:one
for %%S in (S01_WhatIsOblique S02_Triangulation S03_SheetB S04_DevelopmentB S05_ConeAndRecap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
