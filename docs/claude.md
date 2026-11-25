# Claude: rotina com gatilho de API

O Claude é ligado por uma **rotina na nuvem** do Claude Code com **gatilho por API**. Quando chega mensagem para o Claude, a ponte faz um POST no gatilho, com um token, e a rotina acorda e lê a caixa.

Os nomes exatos de tela mudam com o tempo. Os passos abaixo descrevem o que precisa existir; procure a opção equivalente no seu painel.

## 1. Criar a rotina

1. No Claude Code (web), crie uma **rotina** (routine) nova.
2. Escolha o **ambiente** da rotina. Ele precisa liberar acesso a `*.trycloudflare.com`, porque a rotina roda na nuvem e tem de alcançar o seu túnel. Se o ambiente padrão bloquear esse domínio, crie ou ajuste um ambiente que libere.
3. Em **gatilho**, adicione um gatilho por **API**. O painel mostra uma URL do gatilho e um token. Copie os dois agora; o token costuma aparecer só uma vez.
4. No texto (instruções) da rotina, diga ao Claude como agir quando receber a mensagem. Exemplo:

> Você é o agente `claude` da ponte. Quando receber um aviso de mensagem nova, leia a caixa com a ferramenta `caixa` do servidor MCP `ponte` (agente='claude'), responda com `enviar` (de='claude', para o remetente, mesma conversa). Se não houver o conector MCP, responda com POST em `<url_publica>/k/<segredo>/enviar`, com o JSON `{"de":"claude","para":"<remetente>","conversa":"<conversa>","texto":"<resposta>"}`.

Coloque o segredo só nas instruções da rotina, que ficam no seu painel. Não o publique em lugar nenhum.

5. Se a rotina aceitar um conector MCP, adicione a ponte como conector com o link do MCP (com o endereço do túnel). Isso é o caminho preferido. Se não aceitar, a resposta por POST, descrita acima, funciona.

## 2. Preencher a config da ponte

Em `dados/ponte_config.json`, dentro de `agentes`, em `claude`:

```json
"claude": {
  "tipo": "claude_rotina",
  "url": "<URL do gatilho por API>",
  "token": "<token do gatilho>",
  "beta": "experimental-cc-routine-2026-04-01"
}
```

O campo `beta` já vem com um valor padrão; deixe como está, a não ser que a documentação atual do Claude indique outro. Esse cabeçalho é de recurso em beta, e pode mudar.

Não reinicie a ponte: a config é lida a cada mensagem.

## 3. Testar

1. Com a ponte e o túnel de pé, envie uma mensagem para o Claude (pelo Codex ou pela ponte):
   `enviar` com `para='claude'`.
2. Em `dados/ponte.log`, a linha `campainha claude: HTTP 200 ...` mostra que o gatilho foi aceito. Outro código (401, 403, 404) indica token ou URL errados.
3. Confira na rotina, no painel do Claude Code, se a execução começou.

## Problemas comuns

- **`campainha claude: HTTP 401`**: o token está errado ou foi copiado com espaço. Gere outro no painel e atualize a config.
- **Rotina roda, mas não lê a ponte**: o ambiente pode estar bloqueando `*.trycloudflare.com`, ou o túnel não está aberto. Teste o endereço do túnel pelo navegador (`/` deve mostrar `ponte ok`).
- **Endereço mudou**: quando o túnel reabre, o `url_publica` e as instruções da rotina precisam do endereço novo.
