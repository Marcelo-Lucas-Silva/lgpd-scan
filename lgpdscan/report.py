# lgpd-scan - analisador de exposicao de dados pessoais, com mapeamento a LGPD.
# Copyright (C) 2026 Marcelo Lucas Silva
#
# SPDX-License-Identifier: AGPL-3.0-only
# Software livre sob a GNU Affero General Public License v3 (veja LICENSE).
# Licenca comercial alternativa disponivel - veja LICENSING.md.

"""
Os relatórios.

Dois públicos, dois formatos. O terminal é para quem está corrigindo
agora. O Markdown é para anexar a um parecer, a um relatório de
adequação ou a um processo — e esse precisa citar artigo.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Sequence

from .lgpd import ROTULO_SEVERIDADE, SEVERIDADES
from .scanner import Achado

CORES = {
    "critico": "\033[91m",
    "alto": "\033[93m",
    "medio": "\033[96m",
    "baixo": "\033[90m",
}
RESET = "\033[0m"
NEGRITO = "\033[1m"


def _contagem(achados: Sequence[Achado]) -> Counter:
    return Counter(a.severidade for a in achados)


def _relativo(caminho: Path, raiz: Path) -> str:
    try:
        return str(caminho.relative_to(raiz))
    except ValueError:
        return str(caminho)


def terminal(achados: Sequence[Achado], raiz: Path, cor: bool = True) -> str:
    """Relatório curto, para ler enquanto se corrige."""

    def pinta(texto: str, chave: str) -> str:
        if not cor:
            return texto
        return f"{CORES.get(chave, '')}{texto}{RESET}"

    if not achados:
        return "Nenhum achado. Isso não é um atestado de conformidade — veja o README."

    linhas = []
    por_arquivo: dict[Path, list[Achado]] = defaultdict(list)
    for achado in achados:
        por_arquivo[achado.arquivo].append(achado)

    for arquivo in sorted(por_arquivo, key=lambda p: str(p)):
        linhas.append("")
        titulo = _relativo(arquivo, raiz)
        linhas.append(f"{NEGRITO if cor else ''}{titulo}{RESET if cor else ''}")
        for achado in sorted(por_arquivo[arquivo], key=lambda a: a.linha):
            etiqueta = ROTULO_SEVERIDADE[achado.severidade].ljust(7)
            onde = achado.local if achado.local else f"linha {achado.linha}:{achado.coluna}"
            linhas.append(
                f"  {pinta(etiqueta, achado.severidade)} "
                f"{onde}  "
                f"{achado.regra.codigo}  {achado.regra.nome}  "
                f"[{achado.mascarado()}]  →  {achado.regra.artigo.numero}"
            )

    contagem = _contagem(achados)
    resumo = "  ".join(
        f"{pinta(ROTULO_SEVERIDADE[s], s)} {contagem[s]}"
        for s in sorted(SEVERIDADES, key=SEVERIDADES.get, reverse=True)
        if contagem[s]
    )
    linhas.append("")
    linhas.append(f"{len(achados)} achado(s) em {len(por_arquivo)} arquivo(s)")
    linhas.append(resumo)

    from .scanner import avisos
    if avisos:
        linhas.append("")
        linhas.append(f"{len(avisos)} arquivo(s) não lido(s):")
        for aviso in avisos:
            linhas.append(f"  {aviso}")

    return "\n".join(linhas)


def markdown(achados: Sequence[Achado], raiz: Path) -> str:
    """Relatório longo, com fundamentação legal, para anexar a parecer."""
    contagem = _contagem(achados)
    hoje = date.today().strftime("%d/%m/%Y")

    partes = [
        "# Relatório de exposição de dados pessoais",
        "",
        f"**Alvo analisado:** `{raiz}`  ",
        f"**Data da análise:** {hoje}  ",
        f"**Ferramenta:** lgpd-scan  ",
        f"**Base legal de referência:** Lei 13.709/2018 (LGPD)",
        "",
        "## Resumo",
        "",
        "| Severidade | Achados |",
        "| --- | --- |",
    ]
    for chave in sorted(SEVERIDADES, key=SEVERIDADES.get, reverse=True):
        partes.append(f"| {ROTULO_SEVERIDADE[chave]} | {contagem[chave]} |")
    partes.append(f"| **Total** | **{len(achados)}** |")
    partes.append("")

    if not achados:
        partes += [
            "Nenhuma ocorrência detectada pelas regras aplicadas.",
            "",
            "Esta ausência **não constitui atestado de conformidade**. "
            "A análise é estática e cobre apenas exposição de dado em "
            "código-fonte. Base legal, finalidade, prazo de retenção e "
            "direitos do titular não são verificáveis por varredura.",
        ]
        return "\n".join(partes)

    # Agrupa por regra: o leitor jurídico quer ver por tipo de violação,
    # não por arquivo.
    por_regra: dict[str, list[Achado]] = defaultdict(list)
    for achado in achados:
        por_regra[achado.regra.codigo].append(achado)

    ordenadas = sorted(
        por_regra.items(),
        key=lambda item: (-SEVERIDADES[item[1][0].severidade], item[0]),
    )

    partes.append("## Achados")
    for codigo, grupo in ordenadas:
        regra = grupo[0].regra
        partes += [
            "",
            f"### {codigo} — {regra.nome}",
            "",
            f"**Severidade:** {ROTULO_SEVERIDADE[regra.severidade]}  ",
            f"**Ocorrências:** {len(grupo)}  ",
            f"**Dispositivo:** {regra.artigo}",
            "",
            regra.descricao,
            "",
            f"> {regra.artigo.texto}",
            "",
            f"**Providência:** {regra.artigo.acao}",
            "",
            "| Arquivo | Localização | Trecho (mascarado) |",
            "| --- | --- | --- |",
        ]
        for achado in grupo[:50]:
            caminho = _relativo(achado.arquivo, raiz)
            onde = achado.local if achado.local else f"linha {achado.linha}"
            partes.append(
                f"| `{caminho}` | {onde} | `{achado.mascarado()}` |"
            )
        if len(grupo) > 50:
            partes.append(f"| … | | mais {len(grupo) - 50} ocorrência(s) |")

    partes += [
        "",
        "## Limites desta análise",
        "",
        "A varredura é estática: lê o código como texto, sem executá-lo. "
        "Ela encontra dado pessoal exposto em código-fonte e configuração. "
        "Ela **não** verifica base legal do tratamento, finalidade, "
        "necessidade, prazo de retenção, atendimento a direitos do titular "
        "nem transferência internacional. Esses pontos exigem análise "
        "documental e entrevista com as áreas.",
        "",
        "Trechos foram mascarados para que este relatório não se torne, "
        "ele próprio, uma nova cópia do dado exposto.",
    ]
    return "\n".join(partes)
