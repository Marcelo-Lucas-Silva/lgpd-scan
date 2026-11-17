"""
Ponto de entrada para gerar o executável (.exe) com PyInstaller.

É só uma casca: chama a mesma função de linha de comando que o
`python -m lgpdscan` usa. Toda a lógica continua no pacote lgpdscan.
"""

from lgpdscan.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
