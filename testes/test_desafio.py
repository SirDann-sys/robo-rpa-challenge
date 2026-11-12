"""Testes das regras do desafio, sem navegador nem internet."""
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from desafio import CAMPOS, ler_planilha, ler_resultado  # noqa: E402


def criar_planilha(caminho, cabecalho, linhas):
    livro = Workbook()
    folha = livro.active
    folha.append(cabecalho)
    for linha in linhas:
        folha.append(linha)
    livro.save(caminho)
    return caminho


def test_normaliza_cabecalho_com_espaco_e_telefone_numerico(tmp_path):
    # igual à planilha real: "Last Name " com espaço e telefone salvo como número
    cabecalho = ["First Name", "Last Name ", "Company Name", "Role in Company", "Address", "Email", "Phone Number"]
    arq = criar_planilha(tmp_path / "c.xlsx", cabecalho,
                         [["John", "Smith", "IT Solutions", "Analyst", "98 North Road", "jsmith@itsolutions.co.uk", 40716543298.0],
                          [None] * 7])
    registros = ler_planilha(arq)
    assert len(registros) == 1                                   # a linha vazia é ignorada
    assert set(registros[0]) == set(CAMPOS)
    assert registros[0]["Last Name"] == "Smith"
    assert registros[0]["Phone Number"] == "40716543298"


def test_coluna_faltando_avisa(tmp_path):
    arq = criar_planilha(tmp_path / "c.xlsx", ["First Name", "Email"], [["Ana", "a@b.c"]])
    with pytest.raises(ValueError, match="Last Name"):
        ler_planilha(arq)


def test_le_mensagem_de_resultado():
    r = ler_resultado("Congratulations!\nYour success rate is 100% ( 70 out of 70 fields) in 812 milliseconds")
    assert (r.acerto, r.campos_certos, r.campos_total, r.tempo_ms) == (100, 70, 70, 812)
    assert r.perfeito


def test_resultado_parcial_nao_e_perfeito():
    assert not ler_resultado("Your success rate is 90% ( 63 out of 70 fields) in 1500 milliseconds").perfeito


def test_mensagem_estranha_vira_erro():
    with pytest.raises(ValueError):
        ler_resultado("Something went wrong")
