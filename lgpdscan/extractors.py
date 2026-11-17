# lgpd-scan - analisador de exposicao de dados pessoais, com mapeamento a LGPD.
# Copyright (C) 2026 Marcelo Lucas Silva
#
# SPDX-License-Identifier: AGPL-3.0-only
# Software livre sob a GNU Affero General Public License v3 (veja LICENSE).
# Licenca comercial alternativa disponivel - veja LICENSING.md.

"""
Extração de texto de documentos.

Um scanner que lê só código encontra pouco. O dado pessoal das
empresas vive em planilha, contrato e laudo — .xlsx, .docx, .pdf.
Este módulo abre cada um desses formatos e devolve o texto em
unidades localizáveis, para que o relatório possa dizer onde o
achado está: a célula da planilha, o parágrafo do documento, a
página do PDF.

As bibliotecas de leitura são importadas só quando o formato aparece.
Assim o scanner continua funcionando mesmo que uma delas não esteja
instalada: o arquivo é pulado com um aviso, em vez de derrubar a
varredura inteira.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


@dataclass(frozen=True)
class Trecho:
    """Uma unidade de texto extraída, com onde ela fica no arquivo."""

    numero: int       #: ordem de leitura, para ordenar o relatório
    texto: str        #: o conteúdo a ser analisado
    local: str        #: descrição legível, ex. "Planilha 'Clientes' linha 42"


#: Formatos de documento que este módulo sabe abrir.
EXTENSOES_DOCUMENTO = {".xlsx", ".xlsm", ".docx", ".pdf"}


class BibliotecaFaltando(RuntimeError):
    """A biblioteca para ler um formato não está instalada."""


# --------------------------------------------------------------------------
# Cada extrator é um gerador de Trecho. Importam a biblioteca por dentro,
# para que a ausência de uma não impeça as outras.
# --------------------------------------------------------------------------


def _extrair_xlsx(caminho: Path) -> Iterator[Trecho]:
    try:
        from openpyxl import load_workbook
    except ImportError as erro:
        raise BibliotecaFaltando("openpyxl") from erro

    # read_only poupa memória; data_only lê o valor calculado das
    # fórmulas, não a fórmula em si — é o valor que pode ser dado pessoal.
    livro = load_workbook(caminho, read_only=True, data_only=True)
    numero = 0
    try:
        for aba in livro.worksheets:
            for i, linha in enumerate(aba.iter_rows(values_only=True), start=1):
                celulas = [str(c) for c in linha if c is not None]
                if not celulas:
                    continue
                numero += 1
                yield Trecho(
                    numero=numero,
                    texto=" ".join(celulas),
                    local=f"Planilha '{aba.title}' linha {i}",
                )
    finally:
        livro.close()


def _extrair_docx(caminho: Path) -> Iterator[Trecho]:
    try:
        from docx import Document
    except ImportError as erro:
        raise BibliotecaFaltando("python-docx") from erro

    documento = Document(str(caminho))

    numero = 0
    for i, paragrafo in enumerate(documento.paragraphs, start=1):
        texto = paragrafo.text.strip()
        if not texto:
            continue
        numero += 1
        yield Trecho(numero=numero, texto=texto, local=f"parágrafo {i}")

    # Tabelas são onde a planilha disfarçada de documento guarda dado.
    for t, tabela in enumerate(documento.tables, start=1):
        for l, linha in enumerate(tabela.rows, start=1):
            celulas = [c.text.strip() for c in linha.cells if c.text.strip()]
            if not celulas:
                continue
            numero += 1
            yield Trecho(
                numero=numero,
                texto=" ".join(celulas),
                local=f"tabela {t} linha {l}",
            )


def _extrair_pdf(caminho: Path) -> Iterator[Trecho]:
    try:
        import pdfplumber
    except ImportError as erro:
        raise BibliotecaFaltando("pdfplumber") from erro

    numero = 0
    with pdfplumber.open(caminho) as pdf:
        for p, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text() or ""
            for linha in texto.splitlines():
                if not linha.strip():
                    continue
                numero += 1
                yield Trecho(numero=numero, texto=linha, local=f"página {p}")


_EXTRATORES = {
    ".xlsx": _extrair_xlsx,
    ".xlsm": _extrair_xlsx,
    ".docx": _extrair_docx,
    ".pdf": _extrair_pdf,
}


def extrair(caminho: Path) -> Iterator[Trecho]:
    """
    Devolve os trechos de texto de um documento.

    Levanta BibliotecaFaltando se o formato é conhecido mas a biblioteca
    não está instalada — quem chama decide se avisa e segue ou para.
    """
    extrator = _EXTRATORES.get(caminho.suffix.lower())
    if extrator is None:
        return iter(())
    return extrator(caminho)


def biblioteca_de(extensao: str) -> Optional[str]:
    """Nome do pacote pip necessário para ler esta extensão, se houver."""
    return {
        ".xlsx": "openpyxl",
        ".xlsm": "openpyxl",
        ".docx": "python-docx",
        ".pdf": "pdfplumber",
    }.get(extensao.lower())
