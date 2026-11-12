"""Configuração do robô. Tudo pode ser trocado por variável de ambiente, sem mexer no código."""
import os
from pathlib import Path

URL = os.environ.get("ROBO_URL", "https://rpachallenge.com/")
HEADLESS = os.environ.get("ROBO_HEADLESS", "0") == "1"
NAVEGADOR = os.environ.get("ROBO_NAVEGADOR", "chrome").lower()   # chrome | edge
PASTA_SAIDA = Path(os.environ.get("ROBO_SAIDA", Path(__file__).parent / "saida"))
ESPERA_MS = int(os.environ.get("ROBO_ESPERA_MS", "10000"))       # tempo máximo para achar cada elemento
