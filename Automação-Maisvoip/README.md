# Automação URA (MaisVoIP) com Playwright

Este repositório contém um script de automação em Python que acessa o painel do **MaisVoIP Discador**, navega até **IPBX → URA** e realiza ajustes básicos (teclas, destino e salvamento) usando **Playwright**. Há também um arquivo de credenciais de **Service Account** do Google, que deve ser tratado como **secreto** e mantido fora do controle de versão.

> **Status**: script funcional com seletores estáveis; ajuste os valores no código conforme seu fluxo de URA.

---

## 📁 Estrutura

- `setaudio.py` — Script principal de automação com Playwright que:
  - Faz login no painel do MaisVoIP
  - Acessa **IPBX → URA**
  - Abre a URA desejada (ex.: “FGTS Reversa”)
  - Ajusta a tecla/roteamento (ex.: tecla 1 → ramal/atendedor) e salva
- `service-account.json` — Credenciais do Google (não versionar, uso opcional para outras integrações do projeto)

> Dica: renomeie as credenciais para algo como `gcp-service-account.json` e use variáveis de ambiente para apontar o caminho do arquivo.

---

## ✅ Pré‑requisitos

- Python 3.10+ (recomendado 3.11)
- [Playwright](https://playwright.dev/python/) para Python
- Navegadores do Playwright instalados

---

## 🚀 Instalação Rápida

```bash
# 1) Criar e ativar o ambiente
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Instalar dependências
pip install playwright

# 3) Instalar navegadores do Playwright
python -m playwright install
```

> Se o painel usar certificado não confiado (porta 8001/HTTPS), e houver erro de SSL, você pode precisar habilitar `ignore_https_errors=True` ao criar o contexto no Playwright.

---

## 🔧 Configuração

Atualmente, os dados de login, a URA a ser editada e os campos a ajustar estão **no código** (`setaudio.py`). Para produção, recomenda‑se migrar esses parâmetros para **variáveis de ambiente** ou um `.env`. Exemplos de variáveis úteis:

- `MAISVOIP_URL` (ex.: `https://seu-dominio:8001/maisvoip/autenticacao.php`)
- `MAISVOIP_USER` (ex.: `######`)
- `MAISVOIP_PASS` (sua senha)
- `URA_ROW_NAME` (ex.: `FGTS Reversa`)
- `URA_TECLA_1` (ex.: `1`)
- `URA_DEST_TIPO_1` (ex.: `A`)
- `URA_DEST_ID_1` (ex.: `155`)

E para o Google (opcional em outros scripts do projeto):

- `GOOGLE_APPLICATION_CREDENTIALS` apontando para o caminho do `service-account.json`

> **Nunca** faça commit do `service-account.json`. Adicione-o ao `.gitignore`.

**Exemplo de `.gitignore`:**
```
.venv/
*.pyc
__pycache__/
service-account.json
.env
```

---

## ▶️ Uso

Com o ambiente ativado:

```bash
python setaudio.py
```

Por padrão, o script executa em **headless** (sem abrir janela). Para depurar visualmente, altere a criação do navegador para `headless=False` em `setaudio.py`.

---

## 🧩 O que o script faz (resumo)

1. Acessa a URL de login do MaisVoIP
2. Preenche **usuário** e **senha**
3. Navega até **IPBX → Funcionalidades → URA**
4. Entra na URA alvo (linha da tabela)
5. Ajusta `obj_ura_tecla_1`, `obj_ura_tipo_dest_1`, `obj_ura_dest_1`
6. **Salvar** e **Recarregar**

Se o nome da URA, IDs ou estrutura da página mudarem, atualize os seletores de acordo.

---

## 🛠️ Dicas de Depuração

- **Timeouts**: aumente `page.set_default_timeout(...)` ou adicione `wait_for_*` específicos entre etapas.
- **Frame**: confirme o `frame` correto (ex.: `frame = page.frame(name="Post")`).
- **Seletores**: valide nomes, textos e rótulos (use `page.locator(...)` para testar).
- **Headful**: rode com `headless=False` para ver a navegação.
- **SSL**: se necessário, `browser.new_context(ignore_https_errors=True)`.

---

## 🔐 Segurança (muito importante)

- Trate `service-account.json` como **secreto** e **não** faça commit.
- Use variáveis de ambiente e **não** deixe credenciais hardcoded em scripts.
- Restrinja permissões da Service Account apenas ao necessário.
- Rotacione chaves periodicamente e mantenha auditoria dos acessos.

---

## 📜 Licença

Uso interno. Adapte para seu projeto. Automação Criada por Roger Eduardo Corrêa© Eventuais duvidas rec.regor@gmail.com

---

## 📣 Créditos & Referências

- Playwright para Python
- Painel MaisVoIP Discador (IPBX/URA)
- Google Service Account para integrações futuras (opcional)
