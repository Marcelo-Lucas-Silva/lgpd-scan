"""
Arquivo propositalmente inseguro, usado como demonstração do lgpd-scan.

NÃO use nada daqui como referência de código. Cada linha abaixo é um
erro real que já causou multa ou vazamento em algum lugar.
"""

import logging

logger = logging.getLogger(__name__)

# Erro 1: dado de cliente real deixado no código depois de um teste.
CLIENTE_PILOTO = {
    "nome": "Joana Ribeiro",
    "cpf": "529.982.247-25",
    "email": "joana.ribeiro@contabilidadesilva.com.br",
    "telefone": "(34) 99812-4477",
}

# Erro 2: credencial escrita direto no código.
# As duas abaixo são inventadas e não imitam o formato de nenhum
# provedor real, de propósito: um arquivo de demonstração não deve
# disparar o varredor de segredos de quem o hospeda.
GATEWAY_API_KEY = "chave-ficticia-de-demonstracao-0000"
BANCO_PASSWORD = "Prod@2026!central"


def cadastrar(usuario):
    # Erro 3: dado pessoal indo para o log.
    logger.info("cadastrando cpf: %s", usuario.cpf)
    print("email do titular:", usuario.email)

    # Erro 4: dado sensível tratado sem base legal destacada.
    perfil = {
        "raca": usuario.raca,
        "religiao": usuario.religiao,
        "diagnostico": usuario.prontuario_resumo,
    }
    salvar(perfil)


def link_segunda_via(usuario):
    # Erro 5: dado pessoal em parâmetro de URL.
    return f"https://loja.exemplo/boleto?cpf={usuario.cpf}&email={usuario.email}"


def salvar(perfil):
    raise NotImplementedError
