"""Regras do RPA Challenge, separadas do navegador para poderem ser testadas sem abrir nada."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook

# Os cabeçalhos da planilha são os mesmos rótulos do formulário (a planilha traz "Last Name " com espaço no fim).
CAMPOS = ("First Name", "Last Name", "Company Name", "Role in Company", "Address", "Email", "Phone Number")


def ler_planilha(caminho: Path) -> list[dict[str, str]]:
    """Lê o challenge.xlsx e devolve uma lista de registros {rótulo: valor}, já com os cabeçalhos normalizados."""
    planilha = load_workbook(caminho, read_only=True, data_only=True).active
    linhas = planilha.iter_rows(values_only=True)
    cabecalho = [str(c).strip() if c is not None else "" for c in next(linhas)]
    faltando = set(CAMPOS) - set(cabecalho)
    if faltando:
        raise ValueError(f"planilha sem as colunas: {', '.join(sorted(faltando))}")

    registros = []
    for linha in linhas:
        if all(v is None or str(v).strip() == "" for v in linha):
            continue                                            # linhas vazias no fim da planilha
        registro = {nome: _texto(valor) for nome, valor in zip(cabecalho, linha) if nome in CAMPOS}
        registros.append(registro)
    return registros


def _texto(valor) -> str:
    """Telefone vem como número (ex.: 40716543298.0); o formulário espera o texto sem o ".0"."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


@dataclass
class Resultado:
    acerto: int          # porcentagem
    campos_certos: int
    campos_total: int
    tempo_ms: int

    @property
    def perfeito(self) -> bool:
        return self.acerto == 100


def ler_resultado(mensagem: str) -> Resultado:
    """Interpreta a mensagem final do site.

    Ex.: "Your success rate is 100% ( 70 out of 70 fields) in 1234 milliseconds"
    """
    m = re.search(r"(\d+)%\s*\(\s*(\d+)\s+out of\s+(\d+)\s+fields\)\s+in\s+(\d+)\s+milliseconds", mensagem)
    if not m:
        raise ValueError(f"mensagem de resultado inesperada: {mensagem!r}")
    return Resultado(*(int(g) for g in m.groups()))
