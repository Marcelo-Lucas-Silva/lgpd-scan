"""
Testes da regra LGPD009 — número de cartão de pagamento.

Os números usados aqui são os de teste publicados pelas próprias
bandeiras. Eles passam no Luhn mas nenhuma adquirente os aceita em
produção, então não há cartão real neste arquivo.
"""

import pytest

from lgpdscan.rules import luhn_valido
from lgpdscan.scanner import varrer


class TestLuhn:
    @pytest.mark.parametrize(
        "numero,bandeira",
        [
            ("4111111111111111", "Visa, 16 dígitos"),
            ("4111 1111 1111 1111", "Visa com espaços"),
            ("4111-1111-1111-1111", "Visa com hífens"),
            ("5555555555554444", "Mastercard"),
            ("378282246310005", "Amex, 15 dígitos"),
        ],
    )
    def test_aceita_cartao_valido(self, numero, bandeira):
        assert luhn_valido(numero), bandeira

    @pytest.mark.parametrize(
        "numero,motivo",
        [
            ("4111111111111112", "último dígito trocado"),
            ("1111111111111111", "não começa com 3, 4, 5 ou 6"),
            ("4444444444444444", "todos os dígitos iguais"),
            ("411111111111", "12 dígitos, curto demais"),
            ("41111111111111111111", "20 dígitos, longo demais"),
            ("529.982.247-25", "é um CPF válido, não um cartão"),
            ("11.222.333/0001-81", "é um CNPJ válido, não um cartão"),
        ],
    )
    def test_rejeita_o_que_nao_e_cartao(self, numero, motivo):
        assert not luhn_valido(numero), motivo


class TestRegraNoScanner:
    def test_encontra_cartao_em_arquivo(self, tmp_path):
        arquivo = tmp_path / "pagamento.py"
        arquivo.write_text(
            'CARTAO_TESTE = "4111 1111 1111 1111"\n', encoding="utf-8"
        )
        achados = varrer(tmp_path)
        assert any(a.regra.codigo == "LGPD009" for a in achados)

    def test_nao_acusa_telefone_nem_data(self, tmp_path):
        arquivo = tmp_path / "config.py"
        arquivo.write_text(
            "TIMESTAMP = 1794836091952\n"
            "PROTOCOLO = '2026110012345678'\n",
            encoding="utf-8",
        )
        achados = [a for a in varrer(tmp_path) if a.regra.codigo == "LGPD009"]
        assert achados == []

    def test_cartao_e_critico(self, tmp_path):
        arquivo = tmp_path / "a.py"
        arquivo.write_text('c = "5555555555554444"\n', encoding="utf-8")
        achado = next(
            a for a in varrer(tmp_path) if a.regra.codigo == "LGPD009"
        )
        assert achado.severidade == "critico"
        assert achado.regra.artigo.numero == "Art. 46"

    def test_relatorio_mascara_o_numero(self, tmp_path):
        arquivo = tmp_path / "a.py"
        arquivo.write_text('c = "4111111111111111"\n', encoding="utf-8")
        achado = next(
            a for a in varrer(tmp_path) if a.regra.codigo == "LGPD009"
        )
        mascarado = achado.mascarado()
        assert "4111111111111111" not in mascarado
        assert mascarado.startswith("4111")
        assert mascarado.endswith("11")
