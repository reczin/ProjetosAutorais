# APIFacta V2 — Playwright + 2Captcha

Automação em **Playwright** para o fluxo do sistema Facta, com resolução automática de **reCAPTCHA v2 / Enterprise** via **2Captcha**. \
Agora, além de `CODIGO_AF` e `TWO_CAPTCHA_API_KEY`, o **USUÁRIO** e a **SENHA** do site também são definidos **em tempo de execução** por **argumentos**, **variáveis de ambiente** ou **prompts interativos** (fallback).

---

## Requisitos

- Windows (PowerShell/CMD)
- Python **3.11** (o projeto usa `.venv311` já criado)
- Navegador Playwright Chromium instalado via:  
  `python -m playwright install chromium`

Dependências estão em `requirements.txt`.

---

## Como executar

Você pode passar valores por **parâmetros**, por **variáveis de ambiente**, ou deixar o script perguntar (**interativo**).

### A) Parâmetros (recomendado)
```powershell
.\.venv311\Scripts\Activate.ps1
python .\main.py -c CODIGO_AF -k SUA_CHAVE_2CAPTCHA -u SEU_EMAIL -p SUA_SENHA
```

### B) Variáveis de ambiente
```powershell
.\.venv311\Scripts\Activate.ps1
$env:CODIGO_AF="CODIGO_AF"
$env:TWO_CAPTCHA_API_KEY="SUA_CHAVE_2CAPTCHA"
$env:USUARIO="SEU_EMAIL"
$env:SENHA="SUA_SENHA"
python .\main.py
```

### C) Interativo (fallback)
```powershell
.\.venv311\Scripts\Activate.ps1
python .\main.py
# → Informe CODIGO_AF: ...
# → Informe TWO_CAPTCHA_API_KEY: ...
# → Informe USUÁRIO (login/e-mail): ...
# → Informe SENHA: ...
```

### D) Via `run.bat`
- Com argumentos (na ordem):  
  `run.bat CODIGO_AF TWO_CAPTCHA_API_KEY USUARIO SENHA`
- Sem argumentos: o `.bat` pergunta e chama o Python com `-c -k -u -p`.

---

## O que mudou no código

- `main.py` passou a aceitar `--usuario` e `--senha`, além de `--codigo-af` e `--captcha-key`.
- Ordem de prioridade: **args** → **env** → **prompt**.
- O login usa os valores recebidos, sem credenciais fixas no fonte.
- Restante do fluxo (pós‑login, `safe_goto`, integração 2Captcha e parsing das mensagens) **permanece igual**.

> Dica: para execuções não supervisionadas, você pode usar **variáveis de ambiente** ou **argumentos** ao invés de digitar nos prompts.

---

## Troubleshooting rápido

- **Falha no 2Captcha (`ERROR_KEY_DOES_NOT_EXIST`)**: verifique sua `-k`/`TWO_CAPTCHA_API_KEY`.
- **`net::ERR_ABORTED`**: o código já tenta *retry* no `safe_goto`; garanta o pós‑login concluído.
- **Headless**: altere a chamada final para `main(headless=True)` se quiser sem UI.

---

## Segurança

- Evite commitar `SENHA` e `TWO_CAPTCHA_API_KEY`. Prefira **argumentos** ou **variáveis de ambiente**.
- Se usar `run.bat` sem argumentos, ele pede a senha usando prompt do **PowerShell** em modo seguro.