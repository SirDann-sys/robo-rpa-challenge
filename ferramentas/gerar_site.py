"""Monta o site do replay: site/ (página fixa) + saida/replay/ (a execução gravada) → site_publicado/.

Uso: python ferramentas/gerar_site.py   (depois de rodar o robô com ROBO_GRAVAR=1)
"""
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM_SITE = RAIZ / "site"
REPLAY = RAIZ / "saida" / "replay"
DESTINO = RAIZ / "site_publicado"


def gerar(replay: Path = REPLAY, destino: Path = DESTINO) -> Path:
    execucao = replay / "execucao.json"
    if not execucao.exists():
        raise SystemExit("saida/replay/execucao.json não existe: rode o robô com ROBO_GRAVAR=1 antes")
    dados = json.loads(execucao.read_text(encoding="utf-8"))
    faltando = [q["arquivo"] for q in dados["quadros"] if not (replay / q["arquivo"]).exists()]
    if faltando:
        raise SystemExit(f"quadros citados no JSON e ausentes: {faltando}")

    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(ORIGEM_SITE, destino)
    (destino / "replay").mkdir()
    shutil.copy2(execucao, destino / "replay" / "execucao.json")
    for q in dados["quadros"]:
        shutil.copy2(replay / q["arquivo"], destino / "replay" / q["arquivo"])
    (destino / ".nojekyll").write_text("", encoding="utf-8")       # GitHub Pages serve os arquivos como estão
    return destino


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pasta = gerar()
    print(f"site pronto em {pasta.relative_to(RAIZ)} ({sum(1 for _ in pasta.rglob('*') if _.is_file())} arquivos)")
