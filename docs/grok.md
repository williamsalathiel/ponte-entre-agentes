# Grok: automação com webhook

O Grok é ligado por uma **automação com gatilho de webhook**. Quando chega mensagem para o Grok, a ponte faz um POST na URL do webhook, assinado no padrão [Standard Webhooks](https://www.standardwebhooks.com), e a automação acorda o Grok com o texto.

Os nomes das telas do Grok mudam com o tempo. Os passos abaixo descrevem o que precisa existir; procure a opção equivalente no painel atual.

## 1. Criar a automação

1. No painel do Grok onde se criam automações (ou bots), crie uma automação nova.
2. Escolha o gatilho **webhook** e copie a **URL** que ele mostra.
3. Se o painel mostrar um **segredo de assinatura** (que começa com `whsec_`), copie. Ele serve para a ponte assinar as mensagens. Se não houver assinatura, a ponte envia sem ela (menos seguro; prefira ter o segredo).
4. Se o painel exigir um cabeçalho de autorização próprio (uma chave que vai num cabeçalho, por exemplo `Authorization`), anote o nome do cabeçalho e a chave. Eles entram como campos opcionais na config (ver abaixo).
5. Nas instruções da automação, diga ao Grok como agir. Exemplo:

> Você é o agente `grok` da ponte. Quando receber um webhook com `tipo: mensagem_ponte`, leia o campo `instrucao` e siga: leia a caixa com a ferramenta `caixa` do servidor MCP `ponte` (agente='grok') e responda com `enviar` (de='grok', para o remetente, mesma conversa). Se não houver o conector MCP, responda com POST em `<url_publica>/k/<segredo>/enviar`.

Coloque o segredo da ponte só nas instruções da automação, no seu painel.

## 2. Preencher a config da ponte

Em `dados/ponte_config.json`, dentro de `agentes`, em `grok`:

```json
"grok": {
  "tipo": "grok_webhook",
  "url": "<URL do webhook>",
  "whsec": "<segredo whsec_... da assinatura>"
}
```

Se o painel exigir cabeçalho próprio, acrescente:

```json
"cabecalho": "Authorization",
"chave": "<valor da chave>"
```

Não reinicie a ponte: a config é lida a cada mensagem.

## 3. Testar

1. Com a ponte e o túnel de pé, envie uma mensagem para o Grok: `enviar` com `para='grok'`.
2. Em `dados/ponte.log`, a linha `campainha grok: HTTP 200 ...` mostra que o webhook aceitou.
3. Se aparecer 401 ou 403, a assinatura, o `whsec` ou o cabeçalho estão errados. Confira o valor copiado, sem espaços extras.

## Problemas comuns

- **HTTP 404 no webhook**: a URL está errada ou a automação foi recriada (a URL muda).
- **HTTP 401 ou 403**: revise `whsec` (tem de começar com `whsec_`) e, se houver, o cabeçalho e a chave.
- **Grok acorda, mas não responde**: o ambiente da automação precisa alcançar o seu túnel. Confira se o endereço do túnel é o atual e se o conector MCP ou o POST estão nas instruções.
