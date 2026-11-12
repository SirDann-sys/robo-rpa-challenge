@echo off
rem Empacota o robô em robo-rpa-challenge.zip para subir no BotCity Maestro (Easy Deploy).
cd /d "%~dp0"
if exist robo-rpa-challenge.zip del robo-rpa-challenge.zip
powershell -NoProfile -Command "Compress-Archive -Path bot.py, desafio.py, config.py, requirements.txt -DestinationPath robo-rpa-challenge.zip"
echo Pronto: robo-rpa-challenge.zip
