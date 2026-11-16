"""
As regras de detecção.

Cada regra sabe três coisas: como se reconhecer em uma linha de código,
qual artigo da LGPD ela toca, e quão grave é. Uma regra nova é uma
entrada nova em REGRAS — nada mais precisa mudar no projeto.
"""

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import lgpd


@dataclass(frozen=True)
class Regra:
    codigo: str
    nome: str
    descricao: str
    padrao: re.Pattern
    artigo: lgpd.Artigo
    severidade: str
    #: Filtro extra para reduzir falso positivo. Recebe o texto casado
    #: e devolve True se o achado é real.
    confirma: Optional[Callable[[str], bool]] = field(default=None, repr=False)

    def achados_em(self, linha: str):
        """Devolve cada trecho da linha que dispara esta regra."""
        for casamento in self.padrao.finditer(linha):
            trecho = casamento.group(0)
            if self.confirma is not None and not self.confirma(trecho):
                continue
            yield casamento.start(), trecho


# --------------------------------------------------------------------------
# Validadores — é o que separa um scanner útil de um gerador de ruído.
# Qualquer sequência de 11 dígitos parece CPF; só uma fração realmente é.
# --------------------------------------------------------------------------


def _digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def cpf_valido(texto: str) -> bool:
    """Confere os dois dígitos verificadores do CPF (módulo 11)."""
    numero = _digitos(texto)
    if len(numero) != 11 or numero == numero[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(
            int(numero[i]) * (tamanho + 1 - i) for i in range(tamanho)
        )
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(numero[tamanho]):
            return False
    return True


def cnpj_valido(texto: str) -> bool:
    """Confere os dois dígitos verificadores do CNPJ."""
    numero = _digitos(texto)
    if len(numero) != 14 or numero == numero[0] * 14:
        return False
    pesos_primeiro = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_segundo = [6] + pesos_primeiro
    for pesos, posicao in ((pesos_primeiro, 12), (pesos_segundo, 13)):
        soma = sum(int(numero[i]) * pesos[i] for i in range(posicao))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(numero[posicao]):
            return False
    return True


def _nao_e_exemplo(texto: str) -> bool:
    """Ignora endereços obviamente fictícios usados em documentação."""
    descartaveis = (
        "example.com",
        "example.org",
        "exemplo.com",
        "test.com",
        "localhost",
        "@email.com",
        "seu@email",
        "user@domain",
    )
    minusculo = texto.lower()
    return not any(d in minusculo for d in descartaveis)


# --------------------------------------------------------------------------
# As regras
# --------------------------------------------------------------------------

REGRAS = [
    Regra(
        codigo="LGPD001",
        nome="CPF no código-fonte",
        descricao=(
            "Um CPF válido aparece escrito diretamente no código. Código vai "
            "para repositório, backup e máquina de quem entra na equipe; o "
            "dado viaja junto e ninguém registra esse acesso."
        ),
        padrao=re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
        artigo=lgpd.ART_46,
        severidade="critico",
        confirma=cpf_valido,
    ),
    Regra(
        codigo="LGPD002",
        nome="CNPJ no código-fonte",
        descricao=(
            "CNPJ não é dado pessoal de pessoa jurídica, mas o de MEI e "
            "empresário individual identifica pessoa natural. Trate como "
            "dado pessoal até provar o contrário."
        ),
        padrao=re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
        artigo=lgpd.ART_46,
        severidade="medio",
        confirma=cnpj_valido,
    ),
    Regra(
        codigo="LGPD003",
        nome="E-mail pessoal no código-fonte",
        descricao=(
            "Endereço de e-mail real escrito no código. É dado pessoal pelo "
            "Art. 5º, I, porque identifica pessoa natural."
        ),
        padrao=re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        artigo=lgpd.ART_46,
        severidade="medio",
        confirma=_nao_e_exemplo,
    ),
    Regra(
        codigo="LGPD004",
        nome="Dado pessoal gravado em log",
        descricao=(
            "Chamada de log imprimindo variável que carrega dado pessoal. "
            "Logs costumam ir para serviço de terceiro, ficam meses e "
            "raramente têm controle de acesso próprio."
        ),
        padrao=re.compile(
            r"(?:console\.(?:log|info|warn|error)|print|printf|logger?\."
            r"(?:info|debug|warn|error))\s*\([^)]*\b"
            r"(?:cpf|cnpj|rg|email|e_mail|senha|password|telefone|phone|"
            r"endereco|address|nome_completo|full_?name|cartao|card|"
            r"nascimento|birth)\b",
            re.IGNORECASE,
        ),
        artigo=lgpd.ART_6_VIII,
        severidade="alto",
    ),
    Regra(
        codigo="LGPD005",
        nome="Dado pessoal sensível tratado",
        descricao=(
            "Campo que sugere dado sensível do Art. 5º, II: origem racial, "
            "convicção religiosa, opinião política, saúde, vida sexual, "
            "genético ou biométrico. Exige base legal específica."
        ),
        padrao=re.compile(
            r"\b(?:raca|etnia|religiao|religiosa|orientacao_sexual|"
            r"biometri[ao]|impressao_digital|prontuario|diagnostico|"
            r"exame_medico|cid10|filiacao_sindical|filiacao_partidaria|"
            r"opiniao_politica|dados?_geneticos?)\b",
            re.IGNORECASE,
        ),
        artigo=lgpd.ART_11,
        severidade="alto",
    ),
    Regra(
        codigo="LGPD006",
        nome="Credencial no código-fonte",
        descricao=(
            "Chave de API, token ou senha escrita no código. Quem obtém a "
            "credencial obtém os dados que ela protege — a exposição não é "
            "do segredo, é de tudo que está atrás dele."
        ),
        padrao=re.compile(
            r"(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|"
            r"password|senha|client[_-]?secret|private[_-]?key)"
            r"\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            re.IGNORECASE,
        ),
        artigo=lgpd.ART_46,
        severidade="critico",
    ),
    Regra(
        codigo="LGPD007",
        nome="Dado pessoal em URL",
        descricao=(
            "Dado pessoal passado como parâmetro de URL. Fica no histórico "
            "do navegador, no log do servidor, no cabeçalho Referer enviado "
            "a terceiros e em qualquer proxy no caminho."
        ),
        padrao=re.compile(
            r"[?&](?:cpf|cnpj|email|senha|password|telefone|rg|token)=",
            re.IGNORECASE,
        ),
        artigo=lgpd.ART_46,
        severidade="alto",
    ),
    Regra(
        codigo="LGPD008",
        nome="Telefone no código-fonte",
        descricao=(
            "Número de telefone brasileiro escrito no código. Dado pessoal "
            "quando vinculável a pessoa natural."
        ),
        padrao=re.compile(
            r"(?<![\d.])(?:\+55\s?)?\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}"
            r"(?![\d.])"
        ),
        artigo=lgpd.ART_46,
        severidade="baixo",
    ),
]


def regra_por_codigo(codigo: str) -> Optional[Regra]:
    for regra in REGRAS:
        if regra.codigo == codigo.upper():
            return regra
    return None
