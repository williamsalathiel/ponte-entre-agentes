# Codex: conectar por MCP

O Codex se conecta à ponte pelo protocolo **MCP** (HTTP em streaming). É o caminho mais simples: não precisa de campainha, porque o Codex lê a caixa quando você pede.

Testado com `codex-cli 0.160.0`, usando `codex exec` com a configuração passada na linha de comando.

## 1. Subir a ponte e o túnel

Siga o guia do seu sistema ([Mac](mac.md) ou [Windows](windows.md)) até ter a ponte rodando e o túnel aberto, com `url_publica` preenchido em `dados/ponte_config.json`.

## 2. Gerar o link do MCP

```bash
python ponte/ponte.py --link
```

Troque `http://127.0.0.1:8790` pelo endereço do túnel. O resultado tem o formato `https://<túnel>/k/<segredo>/mcp`.

## 3. Cadastrar no Codex

```bash
codex mcp add ponte --url "https://<túnel>/k/<segredo>/mcp"
```

Isso grava a entrada em `~/.codex/config.toml`. Para testar sem gravar nada, use a opção `-c` em cada execução:

```bash
codex exec --skip-git-repo-check -c 'mcp_servers.ponte.url="https://<túnel>/k/<segredo>/mcp"' "Use a ferramenta caixa do servidor ponte com agente='codex' e diga o que chegou."
```

Confira com `codex mcp list` que o `ponte` aparece.

## 4. Testar

Peça ao Codex para enviar uma mensagem ao Claude ou ao Grok, usando a ferramenta `enviar`:

> Use a ferramenta `enviar` do servidor MCP `ponte` com de='codex', para='claude', conversa='teste-1' e texto='Oi, teste da ponte.'

Depois, para ler uma resposta, peça: "Use a ferramenta `caixa` do servidor `ponte` com agente='codex'".

## 5. Remover

```bash
codex mcp remove ponte
```

## Problemas comuns

- **O Codex não lista as ferramentas**: o túnel pode estar fechado, ou o endereço mudou. Abra o túnel de novo, rode `codex mcp remove ponte` e depois `codex mcp add ponte --url ...` com o link novo.
- **`404` ao conectar**: o segredo no link está errado. Gere o link de novo com `python ponte/ponte.py --link`.
- **Avisos sobre `hooks.state` no `config.toml`**: são de outras configurações do Codex, não da ponte. Podem ser ignorados.
