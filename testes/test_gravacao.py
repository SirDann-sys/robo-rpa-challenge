"""Gravador do replay, sem navegador: quadros, log e execucao.json."""
import io
import json
import logging
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from desafio import Resultado, ordem_na_tela  # noqa: E402
from gravacao import Gravador  # noqa: E402


def png(largura=1600, altura=900):
    saida = io.BytesIO()
    Image.new("RGB", (largura, altura), "white").save(saida, "PNG")
    return saida.getvalue()


def test_grava_quadros_log_e_resultado(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    logging.getLogger("robo").setLevel(logging.INFO)
    g = Gravador(tmp_path / "replay", ativo=True)
    logging.getLogger("robo").info("rodada %d/%d enviada", 1, 10)
    g.quadro(png(), "Rodada 1/10", passo="rodada", rodada=1, ordem=["Email", "Address"])
    destino = g.salvar(Resultado(100, 70, 70, 900))

    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["ok"] and dados["resultado"]["tempo_ms"] == 900
    assert dados["origem"] == {"onde": "local"}
    assert dados["quadros"][0]["arquivo"] == "quadro_01.jpg" and dados["quadros"][0]["ordem"] == ["Email", "Address"]
    assert Image.open(tmp_path / "replay" / "quadro_01.jpg").width == 1280      # reduzido
    assert any("rodada 1/10" in linha["texto"] for linha in dados["log"])


def test_erro_fica_registrado_e_nao_e_ok(tmp_path):
    g = Gravador(tmp_path / "replay", ativo=True)
    dados = json.loads(g.salvar(None, erro="campo sumiu").read_text(encoding="utf-8"))
    assert not dados["ok"] and dados["erro"] == "campo sumiu"


def test_desligado_nao_grava_nada(tmp_path):
    g = Gravador(tmp_path / "replay", ativo=False)
    g.quadro(png(), "x")
    assert g.salvar(None) is None
    assert not (tmp_path / "replay").exists()


def test_origem_no_github_actions(tmp_path, monkeypatch):
    for k, v in {"GITHUB_ACTIONS": "true", "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "dono/repo",
                 "GITHUB_SHA": "abcdef1234567", "GITHUB_RUN_ID": "42", "GITHUB_EVENT_NAME": "push", "RUNNER_OS": "Linux"}.items():
        monkeypatch.setenv(k, v)
    dados = json.loads(Gravador(tmp_path / "r", ativo=True).salvar(None).read_text(encoding="utf-8"))
    assert dados["origem"]["run"] == "https://github.com/dono/repo/actions/runs/42"
    assert dados["origem"]["commit"] == "abcdef1"


def test_ordem_na_tela_de_cima_para_baixo_e_da_esquerda_para_a_direita():
    posicoes = {"Email": (500, 100), "Address": (10, 100), "Phone Number": (10, 300)}
    assert ordem_na_tela(posicoes) == ["Address", "Email", "Phone Number"]
