"""Testes locais da ponte (sem rede externa, sem segredos reais).

Rodar: python -m unittest discover -s tests -v   (com o venv ativo e as dependências instaladas)
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PASTA_TESTE = tempfile.mkdtemp(prefix="ponte-teste-")
os.environ["PONTE_DADOS"] = PASTA_TESTE  # antes do import: a ponte lê o caminho da pasta de dados ao carregar
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ponte"))

import ponte  # noqa: E402


def _zerar_dados():
    for p in (ponte.CONFIG, ponte.MSGS, ponte.LOG):
        if p.exists():
            p.unlink()


class Campainha(BaseHTTPRequestHandler):
    recebidos = []

    def do_POST(self):
        tam = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tam).decode()
        Campainha.recebidos.append((self.headers, corpo))  # cabeçalhos sem diferenciar maiúsculas
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):  # silencia o log do servidor de teste
        pass


class TestesPonte(unittest.TestCase):
    def setUp(self):
        _zerar_dados()
        Campainha.recebidos.clear()

    def test_primeira_execucao_cria_segredo_sem_dado_real(self):
        c = ponte.config()
        self.assertGreaterEqual(len(c["segredo"]), 30)
        self.assertEqual(c["limite_trocas"], 6)
        self.assertEqual(c["agentes"]["claude"]["url"], "")
        self.assertEqual(c["agentes"]["claude"]["token"], "")
        self.assertEqual(c["agentes"]["grok"]["whsec"], "")
        self.assertEqual(ponte.config()["segredo"], c["segredo"], "o segredo não pode mudar a cada leitura")

    def test_limite_de_trocas_guarda_sem_acordar(self):
        conversa = "teste01"
        resultados = [ponte.enviar_msg("claude", "codex", f"msg {i}", conversa) for i in range(1, 8)]
        self.assertEqual([r["troca"] for r in resultados[:6]], [1, 2, 3, 4, 5, 6])
        self.assertIn("limite", resultados[6]["campainha"])

    def test_caixa_marca_como_lida(self):
        ponte.enviar_msg("codex", "claude", "oi", "teste02")
        self.assertEqual(len(ponte.ler_caixa("claude")), 1)
        self.assertEqual(ponte.ler_caixa("claude"), [])

    def test_assinatura_standard_webhooks(self):
        chave = b"chave-de-teste-nao-e-segredo"
        whsec = "whsec_" + base64.b64encode(chave).decode()
        corpo = '{"oi": 1}'
        assinatura = ponte._assinar_standard_webhooks(whsec, "msg_1", "1700000000", corpo)
        esperado = hmac.new(chave, b"msg_1.1700000000." + corpo.encode(), hashlib.sha256).digest()
        self.assertEqual(assinatura, "v1," + base64.b64encode(esperado).decode())

    def _subir_receptor(self):
        servidor = HTTPServer(("127.0.0.1", 0), Campainha)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        self.addCleanup(servidor.server_close)
        self.addCleanup(servidor.shutdown)
        return f"http://127.0.0.1:{servidor.server_port}/gatilho"

    def test_campainha_grok_webhook_assinada(self):
        url = self._subir_receptor()
        chave = b"chave-de-teste"
        whsec = "whsec_" + base64.b64encode(chave).decode()
        ponte.config()
        c = json.loads(ponte.CONFIG.read_text(encoding="utf-8"))
        c["agentes"]["grok"] = {"tipo": "grok_webhook", "url": url, "whsec": whsec}
        ponte._gravar(ponte.CONFIG, c)
        ponte.tocar_campainha("grok", {"de": "claude", "conversa": "teste03", "troca": 1, "texto": "olá grok"})
        headers, corpo = Campainha.recebidos[-1]
        mid, ts, sig = headers["webhook-id"], headers["webhook-timestamp"], headers["webhook-signature"]
        esperado = hmac.new(chave, f"{mid}.{ts}.{corpo}".encode(), hashlib.sha256).digest()
        self.assertEqual(sig, "v1," + base64.b64encode(esperado).decode())
        self.assertEqual(json.loads(corpo)["texto"], "olá grok")

    def test_campainha_claude_leva_bearer(self):
        url = self._subir_receptor()
        ponte.config()
        c = json.loads(ponte.CONFIG.read_text(encoding="utf-8"))
        c["agentes"]["claude"] = {"tipo": "claude_rotina", "url": url, "token": "token-de-teste"}
        ponte._gravar(ponte.CONFIG, c)
        ponte.tocar_campainha("claude", {"de": "grok", "conversa": "teste04", "troca": 1, "texto": "oi"})
        headers, corpo = Campainha.recebidos[-1]
        self.assertEqual(headers["Authorization"], "Bearer token-de-teste")
        self.assertIn('"text"', corpo)


if __name__ == "__main__":
    unittest.main()
