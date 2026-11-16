"""
Testes da regra LGPD008 — telefone.

Escrita depois de uma varredura real no repositório
gestaogovbr/api-pgd acusar "telefone" dentro de uma lista de CPFs de
teste. A regra tinha padrão mas não tinha validador.
"""

import pytest

from lgpdscan.rules import telefone_valido
from lgpdscan.scanner import varrer


class TestAceita:
    @pytest.mark.parametrize(
        "numero,tipo",
        [
            ("(34) 99812-4477", "celular, formatado"),
            ("34998124477", "celular, sem formatação"),
            ("34 99812 4477", "celular, com espaços"),
            ("+55 11 98765-4321", "com código do país"),
            ("5511987654321", "código do país, tudo junto"),
            ("(11) 3254-7890", "fixo de São Paulo"),
            ("(21) 2512-3456", "fixo do Rio"),
            ("(71) 3333-4444", "fixo de Salvador"),
        ],
    )
    def test_telefone_brasileiro_valido(self, numero, tipo):
        assert telefone_valido(numero), tipo


class TestRejeita:
    @pytest.mark.parametrize(
        "numero,motivo",
        [
            ("(20) 99999-9999", "DDD 20 não está em uso"),
            ("(23) 99999-9999", "DDD 23 não está em uso"),
            ("(39) 99999-9999", "DDD 39 não está em uso"),
            ("(34) 19812-4477", "celular tem que começar com 9"),
            ("(11) 1254-7890", "fixo não começa com 1"),
            ("(11) 6254-7890", "fixo não começa com 6"),
            ("11111111111", "dígitos repetidos"),
            ("529.982.247-25", "é um CPF válido"),
            ("348765432", "9 dígitos, curto demais"),
            ("349981244771", "12 dígitos, longo demais"),
        ],
    )
    def test_sequencia_que_nao_e_telefone(self, numero, motivo):
        assert not telefone_valido(numero), motivo


class TestNoScanner:
    def test_encontra_telefone_real(self, tmp_path):
        arquivo = tmp_path / "contato.py"
        arquivo.write_text(
            'TELEFONE_CLIENTE = "(34) 99812-4477"\n', encoding="utf-8"
        )
        achados = varrer(tmp_path)
        assert any(a.regra.codigo == "LGPD008" for a in achados)

    def test_lista_de_cpfs_nao_vira_telefone(self, tmp_path):
        """
        O caso real que motivou esta regra: parâmetros de teste de um
        validador de CPF sendo acusados como telefone.
        """
        arquivo = tmp_path / "cpf_test.py"
        arquivo.write_text(
            "CASOS = [\n"
            '    "11111111111",\n'
            '    "22222222222",\n'
            '    "444-444-444.44",\n'
            '    "529.982.247-25",\n'
            "]\n",
            encoding="utf-8",
        )
        achados = [a for a in varrer(tmp_path) if a.regra.codigo == "LGPD008"]
        assert achados == []
