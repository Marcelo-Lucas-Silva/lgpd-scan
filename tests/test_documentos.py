"""
Testes da leitura de documento — .xlsx, .docx, .pdf.

É o que transforma o scanner de "scanner de código" em "scanner de
dado pessoal": o CPF das empresas vive em planilha e contrato, não em
código.
"""

import pytest

from lgpdscan.scanner import avisos, varrer

openpyxl = pytest.importorskip("openpyxl")
docx = pytest.importorskip("docx")


def _acha(achados, codigo):
    return [a for a in achados if a.regra.codigo == codigo]


class TestXlsx:
    @pytest.fixture
    def planilha(self, tmp_path):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Clientes"
        ws.append(["Nome", "CPF", "Telefone"])
        ws.append(["Fulano de Tal", "529.982.247-25", "(34) 99812-4477"])
        ws.append(["Total", 1, ""])
        caminho = tmp_path / "clientes.xlsx"
        wb.save(caminho)
        return tmp_path

    def test_encontra_cpf_em_celula(self, planilha):
        achados = varrer(planilha)
        assert _acha(achados, "LGPD001")

    def test_localizador_aponta_planilha_e_linha(self, planilha):
        achado = _acha(varrer(planilha), "LGPD001")[0]
        assert "Clientes" in achado.local
        assert "linha" in achado.local

    def test_numero_puro_nao_vira_cpf(self, planilha):
        # a célula "Total, 1" não tem documento válido
        achados = _acha(varrer(planilha), "LGPD001")
        assert len(achados) == 1


class TestDocx:
    @pytest.fixture
    def contrato(self, tmp_path):
        from docx import Document
        doc = Document()
        doc.add_paragraph("CONTRATANTE: inscrito no CPF 529.982.247-25.")
        doc.add_paragraph("Cláusula primeira, sem dado pessoal.")
        caminho = tmp_path / "contrato.docx"
        doc.save(caminho)
        return tmp_path

    def test_encontra_cpf_em_paragrafo(self, contrato):
        achado = _acha(varrer(contrato), "LGPD001")[0]
        assert "parágrafo" in achado.local

    def test_encontra_cpf_em_tabela(self, tmp_path):
        from docx import Document
        doc = Document()
        t = doc.add_table(rows=2, cols=2)
        t.rows[0].cells[0].text = "Nome"
        t.rows[0].cells[1].text = "CPF"
        t.rows[1].cells[0].text = "Fulano"
        t.rows[1].cells[1].text = "529.982.247-25"
        doc.save(tmp_path / "ficha.docx")
        achado = _acha(varrer(tmp_path), "LGPD001")[0]
        assert "tabela" in achado.local


class TestMascaramento:
    def test_relatorio_de_documento_tambem_mascara(self, tmp_path):
        from openpyxl import Workbook
        wb = Workbook()
        wb.active.append(["529.982.247-25"])
        wb.save(tmp_path / "x.xlsx")
        achado = _acha(varrer(tmp_path), "LGPD001")[0]
        assert "529.982.247-25" not in achado.mascarado()


class TestDegradacao:
    def test_arquivo_corrompido_nao_derruba_varredura(self, tmp_path):
        # um .xlsx que não é um zip válido
        (tmp_path / "quebrado.xlsx").write_text("isto nao e um xlsx")
        (tmp_path / "ok.py").write_text('cpf = "529.982.247-25"\n')
        achados = varrer(tmp_path)
        # o .py ainda é varrido, apesar do .xlsx quebrado
        assert _acha(achados, "LGPD001")
        # e o problema foi registrado, não engolido
        assert any("quebrado.xlsx" in a for a in avisos)
