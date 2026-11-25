"""Ponte entre agentes: uma caixa de mensagens por HTTP que acorda cada agente.

Para cada agente cadastrado, a ponte expõe:
- MCP (streamable HTTP) em /k/<segredo>/mcp, com as ferramentas caixa, enviar e historico;
- REST (plano B) em /k/<segredo>/enviar (POST) e /k/<segredo>/caixa?agente=... (GET).

Quando chega mensagem, a ponte "toca a campainha" do destinatário:
- claude_rotina: POST no gatilho por API de uma rotina do Claude Code, com Bearer token;
- grok_webhook: POST no webhook de uma automação, assinado no padrão Standard Webhooks (whsec_...);
- manual: sem campainha; o agente lê a caixa quando for consultado.

Há um limite de trocas por conversa (padrão 6), para os agentes não ficarem conversando sem parar.

Segredos, mensagens e log ficam na pasta dados/ (na raiz do projeto), ignorada pelo git.
Rodar: python ponte/ponte.py   (escuta só em 127.0.0.1; um túnel expõe a porta, ver o README).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import uvicorn
from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(os.environ.get("PONTE_DADOS", RAIZ / "dados"))
CONFIG = DADOS / "ponte_config.json"
MSGS = DADOS / "ponte_msgs.json"
LOG = DADOS / "ponte.log"
PORTA = int(os.environ.get("PONTE_PORTA", "8790"))
_trava = threading.Lock()


def _ler(p: Path, padrao):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - arquivo ausente ou inválido vira o padrão
        return padrao


def _gravar(p: Path, dado) -> None:
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(dado, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _log(txt: str) -> None:
    DADOS.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%d/%m %H:%M:%S} {txt}\n")


def config() -> dict:
    """Lê a config. Na primeira execução, cria o segredo e um modelo de config com campos vazios."""
    DADOS.mkdir(parents=True, exist_ok=True)
    c = _ler(CONFIG, {})
    if not c.get("segredo"):
        c.setdefault("segredo", secrets.token_urlsafe(24))
        c.setdefault("limite_trocas", 6)
        c.setdefault("url_publica", "")  # endereço do túnel, ex.: https://xyz.trycloudflare.com
        c.setdefault("agentes", {
            "claude": {"tipo": "claude_rotina", "url": "", "token": ""},
            "grok": {"tipo": "grok_webhook", "url": "", "whsec": ""},
            "codex": {"tipo": "manual", "url": ""},
        })
        _gravar(CONFIG, c)
    return c


# ---------------- campainha ----------------

def _assinar_standard_webhooks(whsec: str, msg_id: str, ts: str, corpo: str) -> str:
    segredo = whsec.split("_", 1)[1] if whsec.startswith("whsec_") else whsec
    chave = base64.b64decode(segredo)
    mac = hmac.new(chave, f"{msg_id}.{ts}.{corpo}".encode(), hashlib.sha256).digest()
    return "v1," + base64.b64encode(mac).decode()


def _post(url: str, corpo: bytes, headers: dict) -> tuple[int, str]:
    req = urllib.request.Request(url, data=corpo, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def tocar_campainha(para: str, msg: dict) -> str:
    c = config()
    ag = c["agentes"].get(para)
    if not ag or not ag.get("url"):
        return f"sem campainha cadastrada para {para}"
    aviso = (f"Mensagem nova na Ponte de {msg['de']} para {para} (conversa {msg['conversa']}, troca "
             f"{msg['troca']}/{c['limite_trocas']}):\n\n{msg['texto']}\n\n"
             f"Leia a caixa na Ponte (ferramenta caixa, agente='{para}') e responda com a ferramenta enviar "
             f"(de='{para}', para='{msg['de']}', conversa='{msg['conversa']}'). Se não tiver a Ponte como MCP, "
             f"responda com POST em {c.get('url_publica') or '<url>'}/k/<segredo>/enviar.")
    try:
        if ag["tipo"] == "claude_rotina":
            st, tx = _post(ag["url"], json.dumps({"text": aviso}).encode(), {
                "Authorization": f"Bearer {ag.get('token', '')}",
                "anthropic-version": "2023-06-01",
                "anthropic-beta": ag.get("beta", "experimental-cc-routine-2026-04-01"),
                "Content-Type": "application/json"})
        elif ag["tipo"] == "grok_webhook":
            corpo = json.dumps({"tipo": "mensagem_ponte", "de": msg["de"], "para": para,
                                "conversa": msg["conversa"], "texto": msg["texto"], "instrucao": aviso},
                               ensure_ascii=False)
            mid, ts = f"msg_{uuid.uuid4().hex}", str(int(time.time()))
            h = {"Content-Type": "application/json", "webhook-id": mid, "webhook-timestamp": ts}
            if ag.get("cabecalho") and ag.get("chave"):  # opcional: chave num cabeçalho próprio
                h[ag["cabecalho"]] = ag["chave"]
            if ag.get("whsec"):
                h["webhook-signature"] = _assinar_standard_webhooks(ag["whsec"], mid, ts, corpo)
            st, tx = _post(ag["url"], corpo.encode(), h)
        else:
            return f"tipo desconhecido: {ag['tipo']}"
        res = f"campainha {para}: HTTP {st} {tx[:200]}"
    except Exception as e:  # noqa: BLE001
        res = f"campainha {para}: erro {e!r}"[:300]
    _log(res)
    return res


# ---------------- núcleo ----------------

def enviar_msg(de: str, para: str, texto: str, conversa: str = "") -> dict:
    c = config()
    with _trava:
        db = _ler(MSGS, {"msgs": []})
        conversa = conversa or uuid.uuid4().hex[:8]
        troca = 1 + sum(1 for m in db["msgs"] if m["conversa"] == conversa)
        msg = {"id": uuid.uuid4().hex[:10], "conversa": conversa, "troca": troca, "de": de, "para": para,
               "texto": texto, "hora": datetime.now().isoformat(timespec="seconds"), "lida": False}
        db["msgs"].append(msg)
        _gravar(MSGS, db)
    _log(f"msg {de}->{para} conversa {conversa} troca {troca}: {texto[:120]!r}")
    if troca > c["limite_trocas"]:
        return {"ok": True, "id": msg["id"], "conversa": conversa,
                "campainha": f"limite de {c['limite_trocas']} trocas atingido: guardei, mas não acordei {para}"}
    # A campainha pode demorar (até 30 s); ela roda em segundo plano e o resultado vai para o log.
    threading.Thread(target=tocar_campainha, args=(para, msg), daemon=True).start()
    return {"ok": True, "id": msg["id"], "conversa": conversa, "troca": troca,
            "campainha": f"tocando em segundo plano (resultado em {LOG.name})"}


def ler_caixa(agente: str) -> list[dict]:
    with _trava:
        db = _ler(MSGS, {"msgs": []})
        novas = [m for m in db["msgs"] if m["para"] == agente and not m["lida"]]
        for m in novas:
            m["lida"] = True
        _gravar(MSGS, db)
    return novas


# ---------------- MCP ----------------

mcp = MCPServer("ponte", instructions=(
    "Ponte de conversa entre agentes de plataformas diferentes (ex.: Claude, Grok, Codex). Use 'caixa' para ler "
    "as mensagens novas para você e 'enviar' para responder. Sempre passe o mesmo 'conversa' da mensagem recebida."))


@mcp.tool()
def caixa(agente: str) -> str:
    """Lê (e marca como lidas) as mensagens novas para este agente. agente: o seu nome, ex.: 'claude', 'grok', 'codex'."""
    novas = ler_caixa(agente)
    return json.dumps(novas, ensure_ascii=False) if novas else "Nenhuma mensagem nova."


@mcp.tool()
def enviar(de: str, para: str, texto: str, conversa: str = "") -> str:
    """Envia uma mensagem a outro agente e o acorda. Deixe 'conversa' vazio só para começar uma conversa nova."""
    return json.dumps(enviar_msg(de, para, texto, conversa), ensure_ascii=False)


@mcp.tool()
def historico(conversa: str = "", n: int = 20) -> str:
    """Mostra as últimas n mensagens (de uma conversa, se informada)."""
    msgs = _ler(MSGS, {"msgs": []})["msgs"]
    if conversa:
        msgs = [m for m in msgs if m["conversa"] == conversa]
    return json.dumps(msgs[-n:], ensure_ascii=False)


# ---------------- HTTP ----------------

def _ok(req: Request) -> bool:
    return hmac.compare_digest(req.path_params.get("seg", ""), config()["segredo"])


async def rota_enviar(req: Request):
    if not _ok(req):
        return PlainTextResponse("não", status_code=404)
    try:
        d = await req.json()
    except Exception:  # noqa: BLE001
        d = dict(req.query_params)
    if not all(d.get(k) for k in ("de", "para", "texto")):
        return JSONResponse({"erro": "faltam de, para, texto"}, status_code=400)
    return JSONResponse(enviar_msg(d["de"], d["para"], d["texto"], d.get("conversa", "")))


async def rota_caixa(req: Request):
    if not _ok(req):
        return PlainTextResponse("não", status_code=404)
    return JSONResponse(ler_caixa(req.query_params.get("agente", "")))


async def rota_saude(_req: Request):
    return PlainTextResponse("ponte ok")


def app() -> Starlette:
    seg = config()["segredo"]
    mcp_app = mcp.streamable_http_app(streamable_http_path="/mcp", stateless_http=True, json_response=True,
                                      host="0.0.0.0")
    return Starlette(
        routes=[Route("/", rota_saude),
                Route("/k/{seg}/enviar", rota_enviar, methods=["POST", "GET"]),
                Route("/k/{seg}/caixa", rota_caixa),
                Mount(f"/k/{seg}", app=mcp_app)],
        lifespan=lambda _a: mcp_app.router.lifespan_context(mcp_app))


if __name__ == "__main__":
    if "--link" in sys.argv:
        # Imprime só o caminho do MCP local. Quem usa é você: não cole isso em chats nem em issues.
        print(f"http://127.0.0.1:{PORTA}/k/{config()['segredo']}/mcp")
        sys.exit(0)
    config()
    _log("ponte iniciada")
    print(f"Ponte no ar em http://127.0.0.1:{PORTA} (config em {CONFIG}). Ctrl+C para parar.")
    uvicorn.run(app(), host="127.0.0.1", port=PORTA, log_level="warning")
