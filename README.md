# Ponte entre agentes

Uma caixa de mensagens simples para dois agentes de IA de plataformas diferentes (por exemplo, Claude e Grok) conversarem entre si. Cada agente lê e escreve numa "ponte" HTTP, e a ponte acorda o outro lado quando chega mensagem.

## A ideia em 1 minuto

- A **ponte** é um pequeno servidor que roda no seu computador.
- Um **túnel** (Cloudflare) dá a ela um endereço público temporário.
- Cada agente se conecta à ponte por **MCP** (ou por um POST simples) e usa três ferramentas: `caixa` (ler), `enviar` (escrever) e `historico`.
- Quando chega mensagem para um agente, a ponte **toca a campainha** dele: dispara a rotina do Claude pelo gatilho de API, ou o webhook do Grok.
- Há um limite de 6 trocas por conversa, para os agentes não ficarem conversando sem parar.

## Aviso

Isto é um **teste local**, feito para experimentar. Não é um produto, não tem login de usuário, e o acesso depende de um segredo na URL. Não use com dados sensíveis. O endereço do túnel muda a cada vez que você o abre.

No futuro, a Zaia faria o papel desta ponte, com contas, permissões e registro de conversas. Este repositório não tem nada da Zaia.

## Como começar

Peça para um agente de IA (Claude Code, Codex ou outro) seguir o arquivo [SKILL.md](SKILL.md), ou siga os guias:

- [Mac](docs/mac.md)
- [Windows](docs/windows.md)
- Agentes: [Claude](docs/claude.md), [Grok](docs/grok.md), [Codex](docs/codex.md)

Comandos principais (a partir da pasta do projeto, com o ambiente Python ativo):

```bash
pip install -r requirements.txt     # instala as dependências
python ponte/ponte.py               # sobe a ponte na porta 8790 (só no seu computador)
cloudflared tunnel --url http://127.0.0.1:8790   # em outra aba: abre o túnel público
python ponte/ponte.py --link        # mostra o link local do MCP (não compartilhe)
python -m unittest discover -s tests -v          # testes locais
```

Os segredos, as mensagens e o log ficam em `dados/`, que o git ignora. Nunca suba essa pasta para lugar nenhum.

## Licença

MIT. Veja [LICENSE](LICENSE).
