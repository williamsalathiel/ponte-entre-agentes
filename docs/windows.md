# Guia para Windows

**Atenção:** este guia foi escrito a partir do teste no Mac. Os comandos de Windows ainda não foram testados ponta a ponta. Se algo falhar, copie a mensagem de erro e siga a partir dela.

## 1. Instalar o que falta

Abra o **PowerShell** e confira:

```powershell
py --version        # precisa ser 3.10 ou mais novo
git --version
cloudflared --version
```

Se faltar Python, instale pelo site oficial (python.org) e marque **"Add python.exe to PATH"** na instalação. Para o cloudflared, use o pacote oficial da Cloudflare (`winget install --id Cloudflare.cloudflared`) ou baixe o executável no site da Cloudflare e coloque a pasta dele no PATH.

## 2. Baixar o projeto

```powershell
cd $HOME\Documents
git clone https://github.com/williamsalathiel/ponte-entre-agentes.git
cd ponte-entre-agentes
```

## 3. Preparar o ambiente Python

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Se o PowerShell bloquear a ativação do venv, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.

## 4. Rodar a ponte

Numa janela do PowerShell:

```powershell
cd $HOME\Documents\ponte-entre-agentes
.venv\Scripts\activate
python ponte\ponte.py
```

Deve aparecer `Ponte no ar em http://127.0.0.1:8790`. Em outra janela, `curl.exe http://127.0.0.1:8790/` responde `ponte ok`.

A primeira execução cria `dados\ponte_config.json`. A pasta `dados` fica fora do git.

## 5. Abrir o túnel

Em outra janela do PowerShell:

```powershell
cloudflared tunnel --url http://127.0.0.1:8790
```

Procure a linha com `https://...trycloudflare.com`. Esse é o endereço público, e ele muda a cada vez. Coloque-o em `url_publica` dentro de `dados\ponte_config.json`, sem barra no final.

## 6. Pegar o link do MCP

Com o venv ativo:

```powershell
python ponte\ponte.py --link
```

Troque `http://127.0.0.1:8790` pelo endereço do túnel. O link tem o segredo: use só na configuração do agente.

## 7. Desligar

1. Janela do túnel: `Ctrl+C`.
2. Janela da ponte: `Ctrl+C`.

## Problemas comuns

- **`'python' não é reconhecido`**: use `py` no lugar de `python` nos comandos de criação do venv, e reabra o terminal depois de instalar o Python.
- **Porta em uso**: `netstat -ano | findstr :8790` mostra o PID; encerre com `taskkill /PID <número> /F`, ou use outra porta com `set PONTE_PORTA=8791` antes de rodar a ponte (use a mesma porta no túnel).
- **Campainha com erro**: veja `dados\ponte.log`.
