@echo off
REM ===================================================================
REM  Lancador amigavel do lgpd-scan.exe, para usar no cliente.
REM  Deixe este arquivo na MESMA pasta do lgpd-scan.exe (no pen drive).
REM  Clique duas vezes e responda as perguntas.
REM ===================================================================
title lgpd-scan

echo.
echo  === Varredura de dados pessoais (LGPD) ===
echo.
set /p ALVO="Arraste aqui a pasta a analisar e tecle Enter: "

REM tira aspas que o Windows coloca ao arrastar
set ALVO=%ALVO:"=%

echo.
set /p NIVEL="Nivel minimo (baixo / medio / alto / critico) [medio]: "
if "%NIVEL%"=="" set NIVEL=medio

echo.
echo  Gerando relatorio mascarado...
echo.

"%~dp0lgpd-scan.exe" "%ALVO%" --severidade %NIVEL% --formato markdown --saida "%ALVO%\relatorio-lgpd.md"

echo.
echo ===================================================================
echo  Relatorio salvo em:  %ALVO%\relatorio-lgpd.md
echo  Ele e CONFIDENCIAL: entregue ao responsavel e nao leve copia.
echo ===================================================================
echo.
pause
