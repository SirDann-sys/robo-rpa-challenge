"""Gravação da execução para o replay na web: quadros (prints) com legenda, log e resultado em execucao.json.

Desligada (padrão), todas as chamadas são vazias e o robô roda como sempre.
"""
from __future__ import annotations

import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

LARGURA_QUADRO = 1280


class Gravador(logging.Handler):

    def __init__(self, pasta: Path, ativo: bool):
        super().__init__(level=logging.INFO)
        self.ativo = ativo
        self.pasta = Path(pasta)
        self.quadros: list[dict] = []
        self.linhas: list[dict] = []
        self.inicio = time.monotonic()
        self.iniciado_em = datetime.now(timezone.utc)
        if ativo:
            self.pasta.mkdir(parents=True, exist_ok=True)
            for velho in self.pasta.glob("*"):
                velho.unlink()
            logging.getLogger("robo").addHandler(self)

    def _segundos(self) -> float:
        return round(time.monotonic() - self.inicio, 2)

    # logging.Handler: cada linha do log do robô entra no replay
    def emit(self, registro: logging.LogRecord):
        self.linhas.append({"t": self._segundos(), "nivel": registro.levelname, "texto": registro.getMessage()})

    def quadro(self, png: bytes, legenda: str, **extra):
        """Guarda um print (PNG do navegador) como JPEG leve, com legenda e dados extras para o player."""
        if not self.ativo:
            return
        n = len(self.quadros) + 1
        nome = f"quadro_{n:02d}.jpg"
        imagem = Image.open(io.BytesIO(png)).convert("RGB")
        if imagem.width > LARGURA_QUADRO:
            imagem = imagem.resize((LARGURA_QUADRO, round(imagem.height * LARGURA_QUADRO / imagem.width)), Image.LANCZOS)
        imagem.save(self.pasta / nome, "JPEG", quality=80, optimize=True)
        self.quadros.append({"arquivo": nome, "t": self._segundos(), "legenda": legenda, **extra})

    def salvar(self, resultado=None, erro: str | None = None) -> Path | None:
        if not self.ativo:
            return None
        dados = {
            "iniciado_em": self.iniciado_em.isoformat(timespec="seconds"),
            "duracao_s": self._segundos(),
            "ok": erro is None and resultado is not None and resultado.perfeito,
            "erro": erro,
            "resultado": None if resultado is None else {
                "acerto": resultado.acerto, "campos_certos": resultado.campos_certos,
                "campos_total": resultado.campos_total, "tempo_ms": resultado.tempo_ms,
            },
            "origem": origem(),
            "quadros": self.quadros,
            "log": self.linhas,
        }
        destino = self.pasta / "execucao.json"
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        logging.getLogger("robo").removeHandler(self)
        return destino


def origem() -> dict:
    """Onde rodou: no GitHub Actions traz o commit e o link do run; na máquina, só "local"."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return {"onde": "local"}
    base = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
    sha = os.environ.get("GITHUB_SHA", "")
    return {
        "onde": "GitHub Actions",
        "evento": os.environ.get("GITHUB_EVENT_NAME", ""),
        "run": f"{base}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
        "commit": sha[:7],
        "commit_url": f"{base}/commit/{sha}",
        "sistema": os.environ.get("RUNNER_OS", ""),
    }
