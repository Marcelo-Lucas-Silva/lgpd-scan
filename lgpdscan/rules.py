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


def luhn_valido(texto: str) -> bool:
    """
    Confere um número de cartão pelo algoritmo de Luhn.

    Três filtros em sequência, do mais barato ao mais caro:

    1. Comprimento entre 13 e 19 dígitos. Abaixo disso não é cartão;
       acima, também não. Isso já descarta CPF, que tem 11.
    2. Primeiro dígito entre 3 e 6. As bandeiras reais ocupam essa
       faixa: 3 (Amex, Diners), 4 (Visa), 5 (Mastercard), 6 (Elo,
       Discover, Hipercard). Qualquer outra coisa é número solto.
    3. O próprio Luhn: dobra cada segundo dígito a partir da direita,
       subtrai 9 do resultado quando passa de 9, e o total tem que
       ser múltiplo de 10.

    Um CNPJ válido é recusado de propósito. Ele tem 14 dígitos, cabe
    na faixa, e um em cada dez passa no Luhn por acaso. Como o
    projeto já tem uma regra própria para CNPJ, acusar o mesmo número
    duas vezes só gera ruído.
    """
    numero = _digitos(texto)
    if not 13 <= len(numero) <= 19:
        return False
    if numero[0] not in "3456":
        return False
    if numero == numero[0] * len(numero):
        return False
    if len(numero) == 14 and cnpj_valido(numero):
        return False

    total = 0
    for posicao, caractere in enumerate(reversed(numero)):
        digito = int(caractere)
        if posicao % 2 == 1:
            digito *= 2
            if digito > 9:
                digito -= 9
        total += digito
    return total % 10 == 0


#: Nomes de caixa que não pertencem a uma pessoa: contas de serviço,
#: espaços reservados de documentação e nomes genéricos de fixture.
#: Comparados por prefixo, para pegar test1, test_2, johndoe2 etc.
_CAIXAS_IMPESSOAIS = (
    # contas de serviço e automação
    "git", "noreply", "no-reply", "no_reply", "donotreply",
    "postmaster", "webmaster", "mailer-daemon", "abuse", "admin",
    "root", "suporte", "support", "contato", "contact", "info",
    # espaços reservados de documentação
    "exemplo", "example", "nome", "name", "seu", "sua", "your",
    "eu", "me", "fulano", "ciclano", "beltrano",
    # nomes de fixture
    "test", "teste", "user", "usuario", "foo", "bar", "baz",
    "john", "jane", "doe", "fake", "dummy", "naoexiste",
    "qwerty", "asdf",
)

#: Domínios que nunca hospedam caixa de pessoa real.
_DOMINIOS_FICTICIOS = (
    "example.com", "example.org", "example.net",
    "exemplo.com", "exemplo.com.br",
    "test.com", "teste.com", "test.local",
    "dominio.com", "domain.com",
    "foo.com", "foo.org", "bar.com",
    "naoexiste.com", "email.com",
    "localhost", "invalid", "local",
)


def _nao_e_exemplo(texto: str) -> bool:
    """
    Decide se um endereço de e-mail pertence mesmo a uma pessoa.

    Um endereço com formato válido não é, por si só, dado pessoal. Três
    categorias casam com o formato e não identificam ninguém:

    1. Contas de serviço: ``git@github.com`` é URL de clone por SSH,
       ``noreply@`` é caixa que não recebe resposta. Não há titular.
    2. Espaços reservados de documentação: ``nome@dominio.com``,
       ``seu@email.com``.
    3. Fixtures de teste: ``test1@api.com``, ``johndoe@oi.com``.

    O custo desta função é conhecido e aceito: um endereço real cujo
    nome de caixa comece por algo desta lista — ``testani@``,
    ``usuario.silva@`` — passa despercebido. É um falso negativo em
    troca de uma queda grande no ruído. Varredura com ruído alto
    simplesmente deixa de ser lida, e aí a taxa de detecção real cai
    a zero.
    """
    endereco = texto.strip().lower()
    if "@" not in endereco:
        return True

    caixa, _, dominio = endereco.rpartition("@")

    if any(dominio == d or dominio.endswith("." + d) for d in _DOMINIOS_FICTICIOS):
        return False
    if any(caixa.startswith(c) for c in _CAIXAS_IMPESSOAIS):
        return False
    return True


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
    Regra(
        codigo="LGPD009",
        nome="Número de cartão no código-fonte",
        descricao=(
            "Número de cartão de pagamento válido escrito no código. Além "
            "da LGPD, isso viola o PCI DSS, norma contratual que todo "
            "estabelecimento aceitante assina com a adquirente. A sanção "
            "contratual costuma chegar antes da administrativa."
        ),
        padrao=re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)"),
        artigo=lgpd.ART_46,
        severidade="critico",
        confirma=luhn_valido,
    ),
]


def regra_por_codigo(codigo: str) -> Optional[Regra]:
    for regra in REGRAS:
        if regra.codigo == codigo.upper():
            return regra
    return None
