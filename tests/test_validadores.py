"""
Testes dos validadores de documento.

Estes são os testes que mais importam no projeto. A diferença entre um
scanner que as pessoas usam e um que elas desinstalam no primeiro dia
é a taxa de falso positivo — e ela vive aqui.
"""

import pytest

from lgpdscan.rules import cnpj_valido, cpf_valido


class TestCPF:
    @pytest.mark.parametrize(
        "valor",
        [
            "529.982.247-25",
            "52998224725",
            "529982247-25",
        ],
    )
    def test_aceita_cpf_valido_em_qualquer_formatacao(self, valor):
        assert cpf_valido(valor)

    @pytest.mark.parametrize(
        "valor",
        [
            "529.982.247-26",  # dígito verificador errado
            "123.456.789-00",  # sequência comum em exemplo
            "111.111.111-11",  # todos os dígitos iguais
            "000.000.000-00",
            "5299822472",      # curto demais
            "529982247255",    # longo demais
        ],
    )
    def test_rejeita_cpf_invalido(self, valor):
        assert not cpf_valido(valor)

    def test_rejeita_sequencia_que_so_parece_cpf(self):
        # Timestamp em milissegundos: 13 dígitos, mas 11 deles casariam
        # com um regex ingênuo.
        assert not cpf_valido("17948293604")


class TestCNPJ:
    @pytest.mark.parametrize(
        "valor",
        ["11.222.333/0001-81", "11222333000181"],
    )
    def test_aceita_cnpj_valido(self, valor):
        assert cnpj_valido(valor)

    @pytest.mark.parametrize(
        "valor",
        [
            "11.222.333/0001-82",
            "00.000.000/0000-00",
            "11222333000",
        ],
    )
    def test_rejeita_cnpj_invalido(self, valor):
        assert not cnpj_valido(valor)
