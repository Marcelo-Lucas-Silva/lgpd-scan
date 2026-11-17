"""
O varredor: percorre arquivos, aplica as regras, devolve achados.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .extractors import BibliotecaFaltando, EXTENSOES_DOCUMENTO, biblioteca_de, extrair
from .lgpd import SEVERIDADES
from .rules import REGRAS, Regra

#: Pastas que nunca valem a pena varrer: código de terceiros, artefato
#: de build, histórico do git. Varrer isso gera milhares de achados que
#: não são seus para corrigir.
PASTAS_IGNORADAS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    ".next", ".nuxt", "out", "target", "__pycache__", ".venv", "venv",
    "env", ".tox", ".mypy_cache", ".pytest_cache", "coverage",
    ".idea", ".vscode", "bower_components", ".terraform",
}

#: Só arquivos de texto que plausivelmente carregam código ou config.
EXTENSOES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt",
    ".rb", ".php", ".go", ".rs", ".cs", ".c", ".cpp", ".h", ".swift",
    ".sql", ".sh", ".bash", ".ps1", ".yml", ".yaml", ".json", ".toml",
    ".ini", ".cfg", ".conf", ".env", ".properties", ".xml", ".html",
    ".vue", ".svelte", ".md", ".txt", ".csv",
} | EXTENSOES_DOCUMENTO

#: Linha mais longa que isso é quase sempre arquivo minificado ou dado
#: embutido em base64. Varrer custa caro e o achado é inútil.
LIMITE_LINHA = 2000

MAX_BYTES = 5 * 1024 * 1024          # 5 MB, para texto e código
MAX_BYTES_DOC = 50 * 1024 * 1024     # 50 MB, documentos são maiores


@dataclass(frozen=True)
class Achado:
    arquivo: Path
    linha: int
    coluna: int
    trecho: str
    regra: Regra
    #: Para documento, onde o achado está em linguagem de pessoa:
    #: "Planilha 'Clientes' linha 42", "página 3". Vazio para código,
    #: onde o próprio número da linha já localiza.
    local: str = ""

    @property
    def severidade(self) -> str:
        return self.regra.severidade

    @property
    def peso(self) -> int:
        return SEVERIDADES[self.regra.severidade]

    def mascarado(self) -> str:
        """
        Versão do trecho segura para colocar em relatório.

        Um relatório de LGPD que imprime o CPF encontrado por inteiro
        acaba de criar uma segunda cópia do vazamento. Preserva-se só o
        suficiente para localizar o dado no arquivo.
        """
        texto = self.trecho.strip()
        if len(texto) <= 8:
            return texto[:2] + "*" * max(0, len(texto) - 2)
        return f"{texto[:4]}{'*' * 6}{texto[-2:]}"


def _deve_varrer(caminho: Path, extensoes: Iterable[str]) -> bool:
    if caminho.suffix.lower() not in extensoes:
        # arquivos sem extensão com nome conhecido ainda interessam
        if caminho.name not in {".env", "Dockerfile", "Makefile"}:
            return False
    limite = MAX_BYTES_DOC if caminho.suffix.lower() in EXTENSOES_DOCUMENTO else MAX_BYTES
    try:
        if caminho.stat().st_size > limite:
            return False
    except OSError:
        return False
    return True


def listar_arquivos(
    raiz: Path,
    extensoes: Iterable[str] = EXTENSOES,
    ignorar: Iterable[str] = PASTAS_IGNORADAS,
) -> Iterator[Path]:
    """Caminha a árvore devolvendo só os arquivos que valem varredura."""
    ignorar = set(ignorar)
    if raiz.is_file():
        if _deve_varrer(raiz, extensoes):
            yield raiz
        return

    for pasta_atual, subpastas, arquivos in os.walk(raiz):
        # poda in-place: impede o os.walk de descer em node_modules
        subpastas[:] = [p for p in subpastas if p not in ignorar]
        for nome in arquivos:
            caminho = Path(pasta_atual) / nome
            if _deve_varrer(caminho, extensoes):
                yield caminho


#: Avisos acumulados durante a última varredura (documento que não pôde
#: ser lido). Quem chama lê isto depois, para informar o usuário.
avisos: list[str] = []


def _linhas_do_arquivo(caminho: Path):
    """
    Devolve (numero, texto, local) para cada unidade analisável.

    Para código e texto, uma linha é uma linha e `local` fica vazio.
    Para documento, delega ao extrator, que já traz o localizador em
    linguagem de pessoa (célula, parágrafo, página).
    """
    if caminho.suffix.lower() in EXTENSOES_DOCUMENTO:
        try:
            for trecho in extrair(caminho):
                yield trecho.numero, trecho.texto, trecho.local
        except BibliotecaFaltando as erro:
            pacote = biblioteca_de(caminho.suffix) or str(erro)
            avisos.append(
                f"{caminho}: não lido — instale a biblioteca com "
                f"'pip install {pacote}'"
            )
        except Exception as erro:  # arquivo corrompido, protegido por senha
            avisos.append(f"{caminho}: não lido ({type(erro).__name__})")
        return

    try:
        texto = caminho.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for numero, linha in enumerate(texto.splitlines(), start=1):
        yield numero, linha, ""


def varrer_arquivo(caminho: Path, regras: Sequence[Regra] = REGRAS):
    """Aplica cada regra a cada unidade de texto do arquivo."""
    for numero, linha, local in _linhas_do_arquivo(caminho):
        if len(linha) > LIMITE_LINHA:
            continue
        if "lgpd-scan: ignorar" in linha:
            continue
        for regra in regras:
            for coluna, trecho in regra.achados_em(linha):
                yield Achado(
                    arquivo=caminho,
                    linha=numero,
                    coluna=coluna + 1,
                    trecho=trecho,
                    regra=regra,
                    local=local,
                )


def varrer(
    raiz: Path,
    regras: Sequence[Regra] = REGRAS,
    extensoes: Iterable[str] = EXTENSOES,
    ignorar: Iterable[str] = PASTAS_IGNORADAS,
) -> list[Achado]:
    """Varre uma pasta ou arquivo e devolve os achados ordenados."""
    avisos.clear()
    achados: list[Achado] = []
    for caminho in listar_arquivos(raiz, extensoes, ignorar):
        achados.extend(varrer_arquivo(caminho, regras))

    achados.sort(key=lambda a: (-a.peso, str(a.arquivo), a.linha))
    return achados
