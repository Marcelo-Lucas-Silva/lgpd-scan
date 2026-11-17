@echo off
REM ===================================================================
REM  Gera o lgpd-scan.exe — um programa unico, sem Python, que roda
REM  em qualquer Windows. Rode este arquivo UMA vez, na sua maquina.
REM  O resultado fica em  dist\lgpd-scan.exe
REM ===================================================================

echo Instalando o empacotador (PyInstaller)...
pip install pyinstaller openpyxl python-docx pdfplumber platformdirs

echo.
echo Gerando o executavel. Isso leva alguns minutos...
echo.

pyinstaller --onefile --name lgpd-scan ^
  --collect-submodules pdfplumber ^
  --collect-submodules pdfminer ^
  --collect-submodules openpyxl ^
  --collect-submodules docx ^
  --hidden-import platformdirs ^
  --hidden-import pkg_resources ^
  --copy-metadata pdfplumber ^
  --copy-metadata pdfminer.six ^
  lgpd_scan_app.py --clean --noconfirm

echo.
echo ===================================================================
echo  Pronto. O programa esta em:  dist\lgpd-scan.exe
echo  Copie esse arquivo para o seu pen drive.
echo ===================================================================
pause
