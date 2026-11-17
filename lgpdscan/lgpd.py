# lgpd-scan - analisador de exposicao de dados pessoais, com mapeamento a LGPD.
# Copyright (C) 2026 Marcelo Lucas Silva
#
# SPDX-License-Identifier: AGPL-3.0-only
# Software livre sob a GNU Affero General Public License v3 (veja LICENSE).
# Licenca comercial alternativa disponivel - veja LICENSING.md.

"""
Mapeamento entre achados técnicos e a Lei Geral de Proteção de Dados
(Lei 13.709/2018).

Este módulo é o coração jurídico do projeto. Um scanner comum diz
"você tem um CPF escrito no código". Este diz qual artigo da lei isso
toca e o que o encarregado precisa fazer a respeito.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Artigo:
    """Um dispositivo da LGPD que um achado pode violar."""

    numero: str
    titulo: str
    texto: str
    acao: str

    def __str__(self) -> str:
        return f"{self.numero} — {self.titulo}"


ART_6_VII = Artigo(
    numero="Art. 6º, VII",
    titulo="Princípio da segurança",
    texto=(
        "Utilização de medidas técnicas e administrativas aptas a proteger "
        "os dados pessoais de acessos não autorizados e de situações "
        "acidentais ou ilícitas de destruição, perda, alteração, "
        "comunicação ou difusão."
    ),
    acao=(
        "Remover o dado do código-fonte e movê-lo para armazenamento "
        "controlado, com acesso registrado."
    ),
)

ART_6_VIII = Artigo(
    numero="Art. 6º, VIII",
    titulo="Princípio da prevenção",
    texto=(
        "Adoção de medidas para prevenir a ocorrência de danos em razão do "
        "tratamento de dados pessoais."
    ),
    acao=(
        "Revisar o fluxo antes de ir a produção; o dano aqui é previsível e "
        "evitável, o que agrava a responsabilidade."
    ),
)

ART_11 = Artigo(
    numero="Art. 11",
    titulo="Dado pessoal sensível",
    texto=(
        "O tratamento de dados pessoais sensíveis somente poderá ocorrer "
        "mediante consentimento específico e destacado do titular, para "
        "finalidades específicas, ou nas hipóteses legais do inciso II."
    ),
    acao=(
        "Confirmar a base legal específica para esta categoria. Consentimento "
        "genérico de cadastro não serve: tem que ser específico e destacado."
    ),
)

ART_37 = Artigo(
    numero="Art. 37",
    titulo="Registro das operações de tratamento",
    texto=(
        "O controlador e o operador devem manter registro das operações de "
        "tratamento de dados pessoais que realizarem."
    ),
    acao=(
        "Garantir que esta operação conste do registro (ROPA) da organização."
    ),
)

ART_46 = Artigo(
    numero="Art. 46",
    titulo="Segurança e sigilo dos dados",
    texto=(
        "Os agentes de tratamento devem adotar medidas de segurança, técnicas "
        "e administrativas aptas a proteger os dados pessoais de acessos não "
        "autorizados e de situações acidentais ou ilícitas."
    ),
    acao=(
        "Corrigir a exposição e documentar a correção. A ANPD considera a "
        "adoção de boas práticas na dosimetria da sanção (Art. 52, §1º, IX)."
    ),
)

ART_48 = Artigo(
    numero="Art. 48",
    titulo="Comunicação de incidente",
    texto=(
        "O controlador deverá comunicar à autoridade nacional e ao titular a "
        "ocorrência de incidente de segurança que possa acarretar risco ou "
        "dano relevante aos titulares."
    ),
    acao=(
        "Se este dado já esteve em repositório público ou em log acessível a "
        "terceiros, avaliar dever de comunicação. O prazo corre."
    ),
)


#: Quanto maior, mais urgente. Usado para ordenar o relatório.
SEVERIDADES = {
    "critico": 3,
    "alto": 2,
    "medio": 1,
    "baixo": 0,
}

ROTULO_SEVERIDADE = {
    "critico": "CRÍTICO",
    "alto": "ALTO",
    "medio": "MÉDIO",
    "baixo": "BAIXO",
}
