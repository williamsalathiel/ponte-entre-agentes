# Guia para Mac

Testado no macOS com Python 3.13 (Homebrew) e cloudflared 2026.x.

## 1. Instalar o que falta

Confira o que já existe:

```bash
python3 --version     # precisa ser 3.10 ou mais novo
git --version
cloudflared --version
```

Se faltar algo, use o [Homebrew](https://brew.sh):

```bash
brew install python git cloudflared
```

## 2. Baixar o projeto

```bash
cd ~/Documents
git clone https://github.com/williamsalathiel/ponte-entre-agentes.git
cd ponte-entre-agentes
```

## 3. Preparar o ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Os 6 testes precisam dar `ok`.

## 4. Rodar a ponte

Numa aba do Terminal:

```bash
cd ~/Documents/ponte-entre-agentes
source .venv/bin/activate
python ponte/ponte.py
```

Deve aparecer `Ponte no ar em http://127.0.0.1:8790`. Em outra aba, `curl http://127.0.0.1:8790/` responde `ponte ok`.

A primeira execução cria `dados/ponte_config.json` com o segredo. Essa pasta fica fora do git.

## 5. Abrir o túnel

Numa segunda aba do Terminal:

```bash
cloudflared tunnel --url http://127.0.0.1:8790
```

Procure a linha com `https://...trycloudflare.com`. Esse é o endereço público. Ele muda a cada vez.

Coloque esse endereço em `url_publica` dentro de `dados/ponte_config.json`, sem barra no final.

## 6. Pegar o link do MCP

Numa terceira aba (com o venv ativo):

```bash
python ponte/ponte.py --link
```

Troque `http://127.0.0.1:8790` pelo endereço do túnel. Esse link tem o segredo: use só na configuração do agente.

## 7. Desligar

1. Aba do túnel: `Ctrl+C`.
2. Aba da ponte: `Ctrl+C`.
3. Confira: `curl http://127.0.0.1:8790/` deve falhar com "connection refused".

## Problemas comuns

- **`command not found: cloudflared`**: rode `brew install cloudflared` e abra uma aba nova.
- **`Address already in use`**: outra coisa está usando a porta 8790. Descubra com `lsof -nP -iTCP:8790 -sTCP:LISTEN` e encerre aquele processo, ou use outra porta com `PONTE_PORTA=8791 python ponte/ponte.py` (lembre de usar a mesma porta no túnel).
- **O túnel abre mas o agente não conecta**: confira que o endereço do túnel é o atual (ele muda a cada reabertura) e que o link do MCP começa com `https://`.
- **Campainha com erro**: veja `dados/ponte.log`.
