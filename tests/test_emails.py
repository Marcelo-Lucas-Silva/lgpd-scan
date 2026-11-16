"""
Testes do filtro de e-mail.

Os endereços descartados abaixo vieram de uma varredura real no
repositório gestaogovbr/api-pgd, em 16/11/2026: os catorze endereços
distintos do projeto eram todos sintéticos, e a versão anterior do
filtro acusou todos eles.
"""

import pytest

from lgpdscan.rules import _nao_e_exemplo


class TestDescarta:
    @pytest.mark.parametrize(
        "endereco,categoria",
        [
            ("git@github.com", "URL de clone por SSH, não é caixa"),
            ("noreply@banco.com.br", "caixa que não recebe resposta"),
            ("no-reply@loja.com", "idem, com hífen"),
            ("admin@api-pgd.gov.br", "conta de papel, não de pessoa"),
            ("suporte@empresa.com.br", "conta de equipe"),
            ("nome@dominio.com", "espaço reservado de documentação"),
            ("seu@email.com", "idem"),
            ("fulano@empresa.com", "idem, em português"),
            ("user1@example.com", "domínio reservado pela RFC 2606"),
            ("test1@api.com", "fixture de teste"),
            ("user_test_0@api.com", "fixture com sufixo"),
            ("johndoe@oi.com", "nome de fixture em inglês"),
            ("foo@oi.com", "idem"),
            ("eu@foo.org", "domínio fictício"),
            ("naoexiste@naoexiste.com", "o nome já avisa"),
        ],
    )
    def test_endereco_sintetico_nao_vira_achado(self, endereco, categoria):
        assert not _nao_e_exemplo(endereco), categoria


class TestMantem:
    @pytest.mark.parametrize(
        "endereco",
        [
            "marcelo.silva@escritorio.adv.br",
            "ana.paula@clinica.com.br",
            "j.ribeiro@contabilidade.net",
            "carlos@gmail.com",
            "m.oliveira@uniube.br",
        ],
    )
    def test_endereco_plausivel_continua_sendo_achado(self, endereco):
        assert _nao_e_exemplo(endereco)


class TestLimites:
    def test_falso_negativo_conhecido_e_aceito(self):
        """
        Documenta o custo da decisão: um endereço real cujo nome de
        caixa comece por um termo da lista escapa do filtro.

        Se este teste um dia incomodar, a saída não é apertar o
        filtro — é rebaixar a severidade em vez de descartar.
        """
        assert not _nao_e_exemplo("testani.costa@empresa.com.br")

    def test_subdominio_ficticio_tambem_e_descartado(self):
        assert not _nao_e_exemplo("alguem@mail.example.com")

    def test_texto_sem_arroba_passa_direto(self):
        assert _nao_e_exemplo("isto nao e um email")
