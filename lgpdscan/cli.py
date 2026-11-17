"""
Interface de linha de comando.

    python -m lgpdscan caminho/do/projeto
    python -m lgpdscan . --formato markdown --saida relatorio.md
    python -m lgpdscan . --severidade alto --falhar
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import report
from .lgpd import SEVERIDADES
from .rules import REGRAS
from .scanner import varrer

VERSAO = "0.1.0"


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lgpd-scan",
        description=(
            "Varre código-fonte, planilhas (.xlsx), documentos (.docx) e "
            "PDFs em busca de dado pessoal exposto, e mapeia cada achado ao "
            "artigo da LGPD correspondente."
        ),
    )
    parser.add_argument(
        "caminho",
        nargs="?",
        default=".",
        help="pasta ou arquivo a analisar (padrão: pasta atual)",
    )
    parser.add_argument(
        "--formato",
        choices=["terminal", "markdown"],
        default="terminal",
        help="formato do relatório",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        help="grava o relatório neste arquivo em vez de imprimir",
    )
    parser.add_argument(
        "--severidade",
        choices=list(SEVERIDADES),
        default="baixo",
        help="mostra apenas achados desta severidade para cima",
    )
    parser.add_argument(
        "--falhar",
        action="store_true",
        help=(
            "encerra com código 1 se houver achado — para usar em "
            "integração contínua e barrar o merge"
        ),
    )
    parser.add_argument(
        "--sem-cor",
        action="store_true",
        help="desliga as cores do terminal",
    )
    parser.add_argument(
        "--listar-regras",
        action="store_true",
        help="mostra as regras disponíveis e sai",
    )
    parser.add_argument("--versao", action="version", version=VERSAO)
    return parser


def listar_regras() -> str:
    linhas = ["Regras disponíveis:", ""]
    for regra in REGRAS:
        linhas.append(
            f"  {regra.codigo}  {regra.nome}  "
            f"({regra.severidade})  →  {regra.artigo.numero}"
        )
    linhas.append("")
    linhas.append(
        "Para ignorar uma linha específica, escreva o comentário "
        "'lgpd-scan: ignorar' nela."
    )
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    if args.listar_regras:
        print(listar_regras())
        return 0

    raiz = Path(args.caminho).resolve()
    if not raiz.exists():
        print(f"Caminho não encontrado: {raiz}", file=sys.stderr)
        return 2

    achados = varrer(raiz)

    minimo = SEVERIDADES[args.severidade]
    achados = [a for a in achados if a.peso >= minimo]

    if args.formato == "markdown":
        texto = report.markdown(achados, raiz)
    else:
        usar_cor = not args.sem_cor and args.saida is None and sys.stdout.isatty()
        texto = report.terminal(achados, raiz, cor=usar_cor)

    if args.saida:
        args.saida.write_text(texto, encoding="utf-8")
        print(f"Relatório gravado em {args.saida}")
    else:
        print(texto)

    if args.falhar and achados:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
