"""Testes da varredura e do mascaramento."""

from pathlib import Path

import pytest

from lgpdscan.rules import regra_por_codigo
from lgpdscan.scanner import PASTAS_IGNORADAS, listar_arquivos, varrer


@pytest.fixture
def projeto(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(
        "CLIENTE_CPF = '529.982.247-25'\n"
        "API_KEY = 'sk_live_51H8xQ2KdefghiJKL'\n"
        "print('dados do cpf:', cpf)\n"
        "versao = '1.2.3'\n",
        encoding="utf-8",
    )
    (tmp_path / "modelo.sql").write_text(
        "CREATE TABLE paciente (\n"
        "  id serial,\n"
        "  diagnostico text,\n"
        "  biometria bytea\n"
        ");\n",
        encoding="utf-8",
    )
    ruido = tmp_path / "node_modules" / "lib"
    ruido.mkdir(parents=True)
    (ruido / "vendor.js").write_text(
        "const cpf = '529.982.247-25';\n", encoding="utf-8"
    )
    return tmp_path


def test_ignora_dependencias_de_terceiros(projeto):
    arquivos = [p.name for p in listar_arquivos(projeto)]
    assert "vendor.js" not in arquivos
    assert "app.py" in arquivos


def test_pastas_ignoradas_cobrem_os_suspeitos_de_sempre():
    for pasta in ("node_modules", ".git", "dist", "__pycache__", ".venv"):
        assert pasta in PASTAS_IGNORADAS


def test_encontra_cpf_credencial_log_e_dado_sensivel(projeto):
    codigos = {a.regra.codigo for a in varrer(projeto)}
    assert "LGPD001" in codigos  # CPF
    assert "LGPD006" in codigos  # credencial
    assert "LGPD004" in codigos  # log de dado pessoal
    assert "LGPD005" in codigos  # dado sensível


def test_nao_confunde_numero_de_versao_com_documento(projeto):
    achados = [
        a
        for a in varrer(projeto)
        if a.arquivo.name == "app.py" and a.linha == 4
    ]
    assert achados == []


def test_ordena_do_mais_grave_para_o_menos(projeto):
    pesos = [a.peso for a in varrer(projeto)]
    assert pesos == sorted(pesos, reverse=True)


def test_relatorio_nunca_imprime_o_dado_inteiro(projeto):
    for achado in varrer(projeto):
        mascarado = achado.mascarado()
        assert mascarado != achado.trecho.strip() or len(achado.trecho) <= 2
        assert "*" in mascarado


def test_comentario_de_excecao_silencia_a_linha(tmp_path):
    arquivo = tmp_path / "legado.py"
    arquivo.write_text(
        "CPF_TESTE = '529.982.247-25'  # lgpd-scan: ignorar\n",
        encoding="utf-8",
    )
    assert varrer(tmp_path) == []


def test_email_de_documentacao_nao_vira_achado(tmp_path):
    arquivo = tmp_path / "README.md"
    arquivo.write_text(
        "Escreva para voce@example.com para testar.\n", encoding="utf-8"
    )
    assert varrer(tmp_path) == []


def test_toda_regra_aponta_para_um_artigo():
    for codigo in ("LGPD001", "LGPD005", "LGPD006"):
        regra = regra_por_codigo(codigo)
        assert regra is not None
        assert regra.artigo.numero.startswith("Art.")
        assert regra.artigo.acao
