@echo off

start pythonw -m text_game_map_maker
IF ERRORLEVEL 0 (goto :end)

start pyw -m text_game_map_maker
IF ERRORLEVEL 0 (goto :end)

python -m text_game_map_maker

:end
