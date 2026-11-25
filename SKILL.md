---
name: ponte-entre-agentes
description: Instala e roda a ponte entre agentes (Claude, Grok, Codex) no computador da pessoa, abre o túnel da Cloudflare, liga cada agente e faz o primeiro teste de conversa. Use quando a pessoa pedir para pôr dois agentes de IA conversando entre si, ou para montar a ponte de teste.
---

# Ponte entre agentes: passo a passo

Você vai montar uma caixa de mensagens local entre agentes de IA. Este arquivo serve tanto para ser colado num chat (Claude Code, Codex ou outra IA) quanto para ser usado como skill. Siga as etapas na ordem e confirme cada uma antes de passar para a próxima.

## Regras que valem o tempo todo

1. **Segredos nunca vão para o chat, para o git nem para issues.** Tokens, a URL de webhook com chave e o segredo da ponte ficam só em `dados/ponte_config.json`. Se a pessoa colar um segredo no chat, avise que ele deve ser trocado depois do teste.
2. **Não suba `dados/` para lugar nenhum.** O `.gitignore` já ignora a pasta; não remova essa linha.
3. **Não mostre o link do MCP completo** (com o segredo) na conversa. Use-o só dentro dos comandos de configuração.
4. **Um comando por vez, e confira a saída** antes de seguir.
5. Se algum passo falhar, copie a mensagem de erro exata e pare ali.

## Etapa 0: perguntas iniciais

Pergunte só o que faltar:

- Qual sistema: **Mac** ou **Windows**?
- Quais agentes ligar agora: **Claude**, **Grok**, **Codex** ou alguma combinação? (Pode ser só Codex, que é o mais simples, para testar.)

Leia o guia do sistema: `docs/mac.md` ou `docs/windows.md`.

## Etapa 1: pré-requisitos

- **Python 3.10 ou mais novo.** Teste com `python3 --version` (Mac) ou `py --version` (Windows).
- **cloudflared** (o túnel). Teste com `cloudflared --version`.
- **git**, para baixar o projeto. Teste com `git --version`.

Se faltar algum, instale seguindo o guia do sistema. Não instale nada além disso.

## Etapa 2: baixar e preparar o projeto

Escolha uma pasta de trabalho (por exemplo, a pasta Documentos). Depois:

```bash
git clone https://github.com/williamsalathiel/ponte-entre-agentes.git
cd ponte-entre-agentes
python3 -m venv .venv            # Windows: py -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Os testes precisam passar (6 testes, todos "ok"). Se algum falhar, pare e mostre a saída.

## Etapa 3: subir a ponte

Numa aba de terminal dedicada, deixe rodando:

```bash
python ponte/ponte.py
```

A primeira execução cria `dados/ponte_config.json` com um segredo novo. A saída deve dizer `Ponte no ar em http://127.0.0.1:8790`. Confira com `curl http://127.0.0.1:8790/`, que deve responder `ponte ok`.

Não feche essa aba enquanto o teste estiver rodando.

## Etapa 4: abrir o túnel

Numa **segunda** aba de terminal:

```bash
cloudflared tunnel --url http://127.0.0.1:8790
```

Procure na saída a linha com `https://...trycloudflare.com` e guarde esse endereço (ele é o `url_publica`). Ele **muda** a cada vez que o túnel é reaberto; anote sempre o atual.

## Etapa 5: registrar o endereço público na config

Edite `dados/ponte_config.json` (com um editor de texto, ou com um comando que só troca esse campo) e preencha:

- `"url_publica"`: o endereço `https://...trycloudflare.com` da etapa 4, sem barra no final.

A ponte lê esse campo a cada mensagem, então não precisa reiniciar.

## Etapa 6: pegar o link do MCP (sem mostrar no chat)

```bash
python ponte/ponte.py --link
```

O comando imprime um link `http://127.0.0.1:8790/k/<segredo>/mcp`. Troque `http://127.0.0.1:8790` pelo endereço do túnel e use o resultado **só** dentro do comando de configuração do agente, sem exibi-lo na conversa.

## Etapa 7: ligar cada agente

Faça só os agentes escolhidos. Cada um tem seu guia:

- **Codex** (o mais simples, por MCP): `docs/codex.md`. Comando: `codex mcp add ponte --url <link-do-MCP>`.
- **Claude** (rotina na nuvem com gatilho de API): `docs/claude.md`. Preencha `agentes.claude.url` e `agentes.claude.token` em `dados/ponte_config.json`, e confira que o ambiente da rotina libera `*.trycloudflare.com`.
- **Grok** (automação com webhook): `docs/grok.md`. Preencha `agentes.grok.url` e `agentes.grok.whsec` em `dados/ponte_config.json`.

Os tokens e chaves vão direto no arquivo, colados pela própria pessoa no editor. Não peça que eles sejam colados no chat.

## Etapa 8: primeiro teste de conversa

Peça ao agente que você ligou primeiro (Codex, por exemplo) para enviar uma mensagem para outro agente, com um `conversa` de teste, por exemplo `teste-1`:

> Use a ferramenta `enviar` do servidor MCP `ponte` com de='codex', para='claude', conversa='teste-1' e texto='Oi, teste da ponte. Responda com a palavra AZUL-42 usando enviar com de=claude, para=codex, conversa=teste-1.'

Depois peça ao outro agente para ler a caixa (`caixa` com o próprio nome) e responder. Por fim, peça ao primeiro para ler a caixa de novo. Se a palavra voltar, a ponte funcionou.

Se o agente não tiver campainha (`sem campainha cadastrada`), ele só responde quando for consultado. Para Claude e Grok, a campainha acorda o agente sozinha quando a config estiver preenchida.

Confira o log com `dados/ponte.log` se algo não funcionar. Ele mostra as chamadas e o resultado de cada campainha.

## Etapa 9: desligar

Quando o teste terminar:

1. Na aba do túnel, pressione `Ctrl+C` (Windows e Mac).
2. Na aba da ponte, pressione `Ctrl+C`.
3. Confirme que nada ficou rodando: `curl http://127.0.0.1:8790/` deve falhar.
4. Se a pessoa quiser, remova o MCP do Codex: `codex mcp remove ponte`.

Lembre: a próxima vez o endereço do túnel será outro. Atualize `url_publica`, a rotina do Claude e o webhook do Grok.

## O que não fazer

- Não rodar a ponte em nenhum servidor público sem o túnel e o segredo.
- Não compartilhar `dados/`, nem colar seu conteúdo em lugar nenhum.
- Não criar uma conta, instalar outros programas, ou alterar outros projetos da pessoa só para este teste.
