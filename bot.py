"""Robô do RPA Challenge (rpachallenge.com) feito com o BotCity Framework Web.

Baixa a planilha do desafio e preenche o formulário uma vez por linha. A cada envio os campos trocam de lugar,
então o robô acha cada campo pelo rótulo, nunca pela posição.

Roda sozinho (python bot.py) ou pelo BotCity Maestro: se o Maestro passar os argumentos da tarefa,
o robô informa o resultado e envia o print como artefato; sem Maestro, só registra no console.
"""
import logging
import sys

import requests
from botcity.maestro import AutomationTaskFinishStatus
from botcity.web import Browser, By, WebBot
from selenium.webdriver.common.selenium_manager import SeleniumManager

import config
from desafio import CAMPOS, ler_planilha, ler_resultado

log = logging.getLogger("robo")


class Bot(WebBot):

    def configurar(self):
        self.headless = config.HEADLESS
        self.browser = Browser.EDGE if config.NAVEGADOR == "edge" else Browser.CHROME
        # O Selenium Manager acha (ou baixa) o driver certo para o navegador instalado.
        self.driver_path = SeleniumManager().binary_paths(["--browser", config.NAVEGADOR])["driver_path"]
        config.PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    def action(self, execution=None):
        # Bot.main() conecta ao Maestro quando ele passa servidor, tarefa e token na linha de comando.
        maestro = getattr(self, "maestro", None) if execution else None
        tarefa = execution.task_id if execution else None
        log.info("tarefa %s", tarefa or "local (sem Maestro)")

        self.configurar()
        try:
            self.browse(config.URL)
            registros = self.baixar_planilha()
            self.clicar(By.XPATH, "//button[contains(translate(normalize-space(.), 'start', 'START'), 'START')]")

            for i, registro in enumerate(registros, 1):
                for campo in CAMPOS:
                    self.preencher(campo, registro[campo])
                self.clicar(By.CSS_SELECTOR, "input[type='submit'][value='Submit']")
                log.info("rodada %d/%d enviada", i, len(registros))

            mensagem = self.esperar_texto("//div[contains(@class, 'message2')]")
            resultado = ler_resultado(mensagem)
            print_ = config.PASTA_SAIDA / "resultado.png"
            self.save_screenshot(str(print_))
            log.info("acerto %d%% (%d de %d campos) em %d ms",
                     resultado.acerto, resultado.campos_certos, resultado.campos_total, resultado.tempo_ms)

            if maestro:
                maestro.post_artifact(tarefa, "resultado.png", str(print_))
                maestro.finish_task(
                    tarefa,
                    AutomationTaskFinishStatus.SUCCESS if resultado.perfeito else AutomationTaskFinishStatus.PARTIALLY_COMPLETED,
                    message=f"{resultado.acerto}% em {resultado.tempo_ms} ms",
                    total_items=resultado.campos_total,
                    processed_items=resultado.campos_certos,
                    failed_items=resultado.campos_total - resultado.campos_certos,
                )
            return resultado

        except Exception as erro:
            self.save_screenshot(str(config.PASTA_SAIDA / "erro.png"))
            if maestro:
                maestro.error(tarefa, erro, screenshot=str(config.PASTA_SAIDA / "erro.png"))
                maestro.finish_task(tarefa, AutomationTaskFinishStatus.FAILED, message=str(erro))
            raise
        finally:
            self.stop_browser()

    # ---- passos ----

    def baixar_planilha(self):
        """Baixa a planilha pelo link da própria página (o endereço não fica fixo no código)."""
        link = self.find_element("//a[contains(@href, '.xlsx')]", By.XPATH, waiting_time=config.ESPERA_MS)
        if link is None:
            raise RuntimeError("link da planilha não encontrado na página")
        resposta = requests.get(link.get_attribute("href"), timeout=30)
        resposta.raise_for_status()
        destino = config.PASTA_SAIDA / "challenge.xlsx"
        destino.write_bytes(resposta.content)
        registros = ler_planilha(destino)
        log.info("planilha com %d registros", len(registros))
        return registros

    def preencher(self, rotulo, valor):
        """Acha o campo pelo rótulo visível; os campos mudam de posição a cada rodada."""
        campo = self.find_element(f"//label[normalize-space()='{rotulo}']/following-sibling::input[1]",
                                  By.XPATH, waiting_time=config.ESPERA_MS)
        if campo is None:
            raise RuntimeError(f"campo '{rotulo}' não encontrado")
        campo.clear()
        campo.send_keys(valor)

    def clicar(self, por, seletor):
        elemento = self.find_element(seletor, por, waiting_time=config.ESPERA_MS)
        if elemento is None:
            raise RuntimeError(f"elemento não encontrado: {seletor}")
        elemento.click()

    def esperar_texto(self, xpath):
        elemento = self.find_element(xpath, By.XPATH, waiting_time=config.ESPERA_MS)
        if elemento is None or not elemento.text.strip():
            raise RuntimeError("mensagem de resultado não apareceu")
        return elemento.text.strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")                  # acentos certos no console do Windows
    sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    try:
        Bot.main()
    except Exception:
        log.exception("o robô parou com erro (print em saida/erro.png)")
        sys.exit(1)
