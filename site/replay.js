// Player do replay: lê replay/execucao.json (gravado pelo robô) e mostra os quadros em ordem.
"use strict";

const $ = (id) => document.getElementById(id);
let dados = null;
let atual = 0;
let relogio = null;
const PASSO_MS = 1600;

function quando(iso) {
  return new Date(iso).toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  }) + " (Brasília)";
}

function link(href, texto) {
  const a = document.createElement("a");
  a.href = href;
  a.textContent = texto;
  return a;
}

function montarStatus() {
  const s = $("status");
  s.textContent = "";
  const selo = document.createElement("span");
  const r = dados.resultado;
  selo.className = "selo " + (dados.ok ? "ok" : "erro");
  selo.textContent = r ? `${dados.ok ? "✓" : "✗"} ${r.acerto}% · ${r.campos_certos} de ${r.campos_total} campos` : "✗ falhou";
  s.append(selo);
  const item = (conteudo) => { const sp = document.createElement("span"); sp.append(conteudo); s.append(sp); };
  if (r) item(`${(r.tempo_ms / 1000).toLocaleString("pt-BR")} s no cronômetro do desafio`);
  if (dados.erro) item(`erro: ${dados.erro}`);
  item(`executado em ${quando(dados.iniciado_em)}`);
  const o = dados.origem || {};
  if (o.run) {
    item(link(o.run, `run no ${o.onde}`));
    item(link(o.commit_url, `commit ${o.commit}`));
  } else {
    item("execução local");
  }
}

function montarTrilha() {
  const t = $("trilha");
  dados.quadros.forEach((q, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.setAttribute("aria-label", `Quadro ${i + 1}: ${q.legenda}`);
    b.addEventListener("click", () => { pausar(); mostrar(i); });
    t.append(b);
    new Image().src = "replay/" + q.arquivo;            // pré-carrega para o play não piscar
  });
}

function montarLog() {
  const l = $("log");
  for (const linha of dados.log) {
    const li = document.createElement("li");
    li.dataset.t = linha.t;
    const tempo = document.createElement("time");
    tempo.textContent = linha.t.toFixed(1) + "s";
    li.append(tempo, linha.texto);
    l.append(li);
  }
}

function mostrar(i) {
  atual = Math.max(0, Math.min(i, dados.quadros.length - 1));
  const q = dados.quadros[atual];
  $("quadro").src = "replay/" + q.arquivo;
  $("quadro").alt = q.legenda;
  $("legenda").textContent = q.pessoa ? `${q.legenda} · ${q.pessoa}` : q.legenda;
  $("contador").textContent = `${atual + 1}/${dados.quadros.length}`;

  const ordem = $("ordem");
  ordem.hidden = !q.ordem;
  if (q.ordem) {
    const lista = $("ordem-lista");
    lista.textContent = "";
    for (const rotulo of q.ordem) {
      const li = document.createElement("li");
      li.textContent = rotulo;
      lista.append(li);
    }
  }

  [...$("trilha").children].forEach((b, j) => b.setAttribute("aria-selected", String(j === atual)));
  let ultimaFeita = null;
  for (const li of $("log").children) {
    const feito = Number(li.dataset.t) <= q.t + 0.05;
    li.classList.toggle("feito", feito);
    li.classList.remove("atual");
    if (feito) ultimaFeita = li;
  }
  if (ultimaFeita) {
    ultimaFeita.classList.add("atual");
    const caixa = $("log");
    caixa.scrollTop = ultimaFeita.offsetTop - caixa.offsetTop - caixa.clientHeight / 2;
  }
}

function tocar() {
  if (atual >= dados.quadros.length - 1) mostrar(0);
  $("tocar").textContent = "❚❚ Pausar";
  $("tocar").setAttribute("aria-label", "Pausar");
  relogio = setInterval(() => {
    if (atual >= dados.quadros.length - 1) return pausar();
    mostrar(atual + 1);
  }, PASSO_MS);
}

function pausar() {
  clearInterval(relogio);
  relogio = null;
  $("tocar").textContent = "▶ Tocar";
  $("tocar").setAttribute("aria-label", "Tocar");
}

function ligarControles() {
  $("tocar").addEventListener("click", () => (relogio ? pausar() : tocar()));
  $("anterior").addEventListener("click", () => { pausar(); mostrar(atual - 1); });
  $("proximo").addEventListener("click", () => { pausar(); mostrar(atual + 1); });
  $("primeiro").addEventListener("click", () => { pausar(); mostrar(0); });
  $("ultimo").addEventListener("click", () => { pausar(); mostrar(dados.quadros.length - 1); });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("button") && e.key === " ") return;   // espaço num botão já é clique
    if (e.key === "ArrowRight") { pausar(); mostrar(atual + 1); }
    else if (e.key === "ArrowLeft") { pausar(); mostrar(atual - 1); }
    else if (e.key === " ") { e.preventDefault(); relogio ? pausar() : tocar(); }
  });
}

async function iniciar() {
  try {
    const r = await fetch("replay/execucao.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(r.status);
    dados = await r.json();
  } catch (erro) {
    $("status").textContent = "Não foi possível carregar a execução gravada.";
    return;
  }
  montarStatus();
  montarTrilha();
  montarLog();
  ligarControles();
  mostrar(0);
}

iniciar();
