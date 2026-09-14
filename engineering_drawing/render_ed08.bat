@echo off
REM ---------------------------------------------------------------------------
REM  Engineering Drawing I - Episode 08: The True Angle Between Two Planes
REM  Renders the four scenes in running order at 1080p60.
REM
REM    render_ed08.bat            all four scenes
REM    render_ed08.bat S03        just the one whose name starts with S03
REM
REM  Run it once with EFS_SILENT=1 set if you want to check the timing and the
REM  layout without waiting on the text-to-speech.
REM ---------------------------------------------------------------------------
setlocal
set FILE=ed08_dihedral_angle.py
set FLAGS=-qh

if not "%~1"=="" goto :one

for %%S in (S01_Dihedral S02_Strategy S03_Construction S04_Recap) do (
    echo.
    echo === %%S ===
    py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
)
echo.
echo All four scenes rendered. They are under media\videos\ed08_dihedral_angle\1080p60\.
goto :eof

:one
for %%S in (S01_Dihedral S02_Strategy S03_Construction S04_Recap) do (
    echo %%S | findstr /b /c:"%~1" >nul && (
        py -3.11 -m manim %FLAGS% %FILE% %%S || goto :failed
    )
)
goto :eof

:failed
echo.
echo Render FAILED - see the message above.
exit /b 1
