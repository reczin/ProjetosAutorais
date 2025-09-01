# main.py
# -*- coding: utf-8 -*-
import argparse
from getpass import getpass
import os
import time
import requests
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PWError,
)

URL_LOGIN = "https://desenv.facta.com.br/sistemaNovo/login.php"
URL_ANDAMENTO = "https://desenv.facta.com.br/sistemaNovo/andamentoPropostas.php"

USUARIO = os.getenv("USUARIO", "")
SENHA = os.getenv("SENHA", "")
CODIGO_AF = os.getenv("CODIGO_AF", "")
TWO_CAPTCHA_API_KEY = os.getenv("TWO_CAPTCHA_API_KEY", "")
REPETIR = os.getenv("REPETIR", "")
VEZES = os.getenv("VEZES", "")


def _is_enterprise(page) -> bool:
    try:
        return page.evaluate("""() => {
            const hasEnterpriseScript = !![...document.querySelectorAll('script[src]')].some(s => /recaptcha\\/enterprise\\.js/.test(s.src));
            const hasEnterpriseObj = !!(window.grecaptcha && window.grecaptcha.enterprise);
            return hasEnterpriseScript || hasEnterpriseObj;
        }""")
    except Exception:
        return False

def _detect_invisible(page) -> bool:
    try:
        return page.evaluate("""() => {
            const el = document.querySelector('[data-sitekey]');
            if (el && el.getAttribute('data-size') === 'invisible') return true;
            return !!(window.grecaptcha && (window.grecaptcha.execute || (window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute)));
        }""")
    except Exception:
        return False

def _extract_sitekey(page) -> str:
    sitekey = page.evaluate("""() => {
        const el = document.querySelector('[data-sitekey]');
        return el ? el.getAttribute('data-sitekey') : null;
    }""")
    if sitekey:
        return sitekey

    try:
        for f in page.frames:
            try:
                url = f.url
                if "google.com/recaptcha" in url or "recaptcha.net" in url:
                    qs = parse_qs(urlparse(url).query)
                    if "k" in qs and qs["k"]:
                        return qs["k"][0]
            except Exception:
                continue
    except Exception:
        pass

    try:
        sitekeys = page.evaluate("""() => {
            const out = [];
            const cfg = window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients;
            if (!cfg) return out;
            for (const i in cfg) {
                const c = cfg[i];
                const stack = [c]; const visited = new Set();
                while (stack.length) {
                    const obj = stack.pop();
                    if (!obj || typeof obj !== 'object' || visited.has(obj)) continue;
                    visited.add(obj);
                    for (const k in obj) {
                        if (k === 'sitekey' && typeof obj[k] === 'string') out.push(obj[k]);
                        const val = obj[k];
                        if (val && typeof val === 'object') stack.push(val);
                    }
                }
            }
            return [...new Set(out)];
        }""")
        if sitekeys and len(sitekeys) > 0:
            return sitekeys[0]
    except Exception:
        pass

    raise RuntimeError("Não foi possível detectar o sitekey do reCAPTCHA na página.")

def _create_task_2captcha(api_key: str, website_url: str, sitekey: str, is_enterprise: bool, is_invisible: bool, user_agent: str = None) -> int:
    task_type = "RecaptchaV2EnterpriseTaskProxyless" if is_enterprise else "RecaptchaV2TaskProxyless"
    payload = {
        "clientKey": api_key,
        "task": {
            "type": task_type,
            "websiteURL": website_url,
            "websiteKey": sitekey,
            "isInvisible": bool(is_invisible)
        }
    }
    if user_agent:
        payload["task"]["userAgent"] = user_agent
    resp = requests.post("https://api.2captcha.com/createTask", json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errorId"):
        raise RuntimeError(f"2Captcha createTask falhou: {data.get('errorCode')} - {data.get('errorDescription')}")
    task_id = data.get("taskId")
    if not task_id:
        raise RuntimeError("2Captcha createTask não retornou taskId.")
    return task_id

def _poll_result_2captcha(api_key: str, task_id: int, timeout_sec: int = 180, first_wait: int = 5, step_wait: int = 3) -> str:
    url = "https://api.2captcha.com/getTaskResult"
    started = time.time()
    time.sleep(first_wait)
    while True:
        resp = requests.post(url, json={"clientKey": api_key, "taskId": task_id}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errorId"):
            raise RuntimeError(f"2Captcha getTaskResult falhou: {data.get('errorCode')} - {data.get('errorDescription')}")
        if data.get("status") == "ready":
            sol = data.get("solution") or {}
            token = sol.get("gRecaptchaResponse") or sol.get("token")
            if not token:
                raise RuntimeError("2Captcha retornou 'ready' mas sem token.")
            return token
        if time.time() - started > timeout_sec:
            raise TimeoutError("Tempo limite atingido aguardando solução do CAPTCHA no 2Captcha.")
        time.sleep(step_wait)

def _inject_recaptcha_token(page, token: str):
    page.evaluate(
        """(tok) => {
            function setVal(sel) {
                const el = document.querySelector(sel);
                if (el) {
                    el.value = tok;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            setVal('textarea[name="g-recaptcha-response"]');
            setVal('textarea[name="g-recaptcha-response-100000"]');
            try {
                const cfg = window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients;
                if (cfg) {
                    for (const i in cfg) {
                        const c = cfg[i];
                        const stack = [c]; const visited = new Set();
                        while (stack.length) {
                            const obj = stack.pop();
                            if (!obj || typeof obj !== 'object' || visited.has(obj)) continue;
                            visited.add(obj);
                            for (const k in obj) {
                                if (k === 'callback' && typeof obj[k] === 'function') {
                                    try { obj[k](tok); } catch(e){}
                                }
                                const val = obj[k];
                                if (val && typeof val === 'object') stack.push(val);
                            }
                        }
                    }
                }
            } catch(e){}
        }""",
        token
    )

def solve_recaptcha_v2_with_2captcha(page) -> None:
    if not TWO_CAPTCHA_API_KEY or "COLOQUE_SUA_CHAVE" in TWO_CAPTCHA_API_KEY:
        raise RuntimeError("Defina TWO_CAPTCHA_API_KEY (env, arg ou prompt).")
    website_url = page.url
    sitekey = _extract_sitekey(page)
    is_enterprise = _is_enterprise(page)
    is_invisible = _detect_invisible(page)
    try:
        user_agent = page.context.user_agent
    except Exception:
        user_agent = None
    task_id = _create_task_2captcha(
        api_key=TWO_CAPTCHA_API_KEY,
        website_url=website_url,
        sitekey=sitekey,
        is_enterprise=is_enterprise,
        is_invisible=is_invisible,
        user_agent=user_agent
    )
    token = _poll_result_2captcha(TWO_CAPTCHA_API_KEY, task_id, timeout_sec=180)
    _inject_recaptcha_token(page, token)

    page.wait_for_function(
        """() => {
            const a = document.querySelector('textarea[name="g-recaptcha-response"]');
            const b = document.querySelector('textarea[name="g-recaptcha-response-100000"]');
            return !!((a && a.value && a.value.length > 0) || (b && b.value && b.value.length > 0));
        }""",
        timeout=10000
    )

def safe_goto(page, url: str, attempts: int = 3):
    for i in range(attempts):
        try:
            page.goto(url, wait_until="load", timeout=45000)
            page.wait_for_load_state("networkidle", timeout=15000)
            return
        except PWError as e:
            msg = str(e)
            if "net::ERR_ABORTED" in msg and i < attempts - 1:
                page.wait_for_timeout(250)
                continue
            raise

def _to_int(x, default=0):
    try:
        return int(str(x).strip())
    except Exception:
        return default

def _load_runtime_config():
    """
    Prioridade:
    1) CLI args  (--codigo-af / --captcha-key / --usuario / --senha / --repetir / --vezes)
    2) Variáveis de ambiente (CODIGO_AF / TWO_CAPTCHA_API_KEY / USUARIO / SENHA / REPETIR / VEZES)
    3) Prompt (fallback com input / getpass)
    """
    parser = argparse.ArgumentParser(description="APIFacta V2")
    parser.add_argument("-c", "--codigo-af", dest="codigo_af", help="Código AF")
    parser.add_argument("-k", "--captcha-key", dest="captcha_key", help="2Captcha API key")
    parser.add_argument("-u", "--usuario", dest="usuario", help="Usuário de login (e-mail)")
    parser.add_argument("-p", "--senha", dest="senha", help="Senha de login")
    parser.add_argument("-r", "--repetir", dest="repetir", help="Vai repetir (1=sim, 2=nao)")
    parser.add_argument("-v", "--vezes", dest="vezes", help="Quantas vezes vai repetir (int)")
    args = parser.parse_args()

    codigo_af = (args.codigo_af or os.getenv("CODIGO_AF") or "").strip()
    captcha_key = (args.captcha_key or os.getenv("TWO_CAPTCHA_API_KEY") or "").strip().strip('"').strip("'")
    usuario = (args.usuario or os.getenv("USUARIO") or "").strip()
    senha = (args.senha or os.getenv("SENHA") or "").strip()
    repetir = (args.repetir or os.getenv("REPETIR") or "").strip()
    vezes = (args.vezes or os.getenv("VEZES") or "").strip()

    if not codigo_af:
        codigo_af = input("Informe CODIGO_AF: ").strip()
    if not captcha_key:
        captcha_key = getpass("Informe TWO_CAPTCHA_API_KEY: ").strip()
    if not usuario:
        usuario = input("Informe USUÁRIO (login/e-mail): ").strip()
    if not senha:
        senha = getpass("Informe SENHA: ").strip()
    if not repetir:
        repetir = input("Repetir? (1=sim, 2=nao): ").strip()
    if not vezes:
        vezes = input("Quantas vezes vai repetir (int): ").strip()

    if not codigo_af:
        raise RuntimeError("CODIGO_AF não informado.")
    if len(captcha_key) < 20:
        print("[AVISO] Captcha key com tamanho inesperado.")

    return codigo_af, captcha_key, usuario, senha, _to_int(repetir, 0), _to_int(vezes, 0)

def main(headless: bool = False, usuario: str = "", senha: str = ""):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        context.set_default_timeout(15000)
        context.set_default_navigation_timeout(30000)
        page = context.new_page()

        page.goto(URL_LOGIN, wait_until="domcontentloaded")
        user_box = page.get_by_role("textbox", name="usuário")
        user_box.wait_for(state="visible")
        user_box.fill(usuario)
        page.get_by_role("textbox", name="senha").fill(senha)
        page.get_by_role("button", name="Entrar").click()
        page.wait_for_load_state("networkidle", timeout=30000)

        CONDICAO = 1
        i = 0
        while CONDICAO == 1 and REPETIR == 1 and i < VEZES:
            safe_goto(page, URL_ANDAMENTO)

            af_box = page.locator("#codigoAf")
            af_box.wait_for(state="visible", timeout=15000)
            af_box.fill(CODIGO_AF)

            page.get_by_role("radio", name="Data Último Status").check()
            page.get_by_role("button", name="Pesquisar").click()

            link_res = page.get_by_role("link", name="AGUARDA AVERBACAO -")
            link_res.wait_for(state="visible", timeout=15000)
            link_res.click()

            btn_hist = page.get_by_role("button", name="  Histórico Dataprev")
            btn_hist.wait_for(state="visible", timeout=15000)
            btn_hist.click()

            solve_recaptcha_v2_with_2captcha(page)

            btn_averbar = page.get_by_role("button", name="Averbar")
            btn_averbar.wait_for(state="visible", timeout=15000)
            btn_averbar.click()

            dialog = page.get_by_role("dialog").first
            dialog.wait_for(state="visible", timeout=10000)
            RESPOSTA = dialog.inner_text().strip()

            import unicodedata, re as _re
            def norm(s: str) -> str:
                s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
                s = _re.sub(r"\s+", " ", s).strip().lower()
                return s

            txt = norm(RESPOSTA)
            ok_msg = norm("Inclusão efetuada com sucesso")
            bloqueio_1_raw = [
                "Ação bloqueada: menos de 3 dias úteis desde a assinatura do contrato",
                "Benefício bloqueado na concessão",
                "Benefício bloqueado para empréstimo pelo beneficiário",
                "Benefício bloqueado por TBM",
            ]
            bloqueio_3_raw = [
                "Margem consignável excedida",
                "A AF não pode ser Averbada. Está fora do fluxo ou não atende aos critérios.",
            ]
            bloqueio_1_keys = [norm(x) for x in bloqueio_1_raw]
            bloqueio_3_keys = [norm(x) for x in bloqueio_3_raw]

            if ok_msg in txt:
                dialog.get_by_role("button", name="OK").click(timeout=6000)
                dialog.wait_for(state="hidden", timeout=15000)
                print(f"[ATENÇÃO] Mensagem condicao 2: {RESPOSTA}")
                CONDICAO = 2
                break

            elif any(k in txt for k in bloqueio_1_keys):
                dialog.get_by_role("button", name="OK").click(timeout=6000)
                dialog.wait_for(state="hidden", timeout=15000)
                print(f"[ATENÇÃO] Mensagem condicao 1 (temporário): {RESPOSTA}")
                CONDICAO = 1
                i += 1
                continue

            elif any(k in txt for k in bloqueio_3_keys):
                dialog.get_by_role("button", name="OK").click(timeout=6000)
                dialog.wait_for(state="hidden", timeout=15000)
                print(f"[ATENÇÃO] Mensagem condicao 3 (terminal): {RESPOSTA}")
                CONDICAO = 3
                break

            else:
                dialog.get_by_role("button", name="OK").click(timeout=6000)
                dialog.wait_for(state="hidden", timeout=15000)
                print(f"[ATENÇÃO] Mensagem não mapeada: {RESPOSTA}")
                CONDICAO = 0
                break

        context.close()
        browser.close()

if __name__ == "__main__":
    CODIGO_AF, TWO_CAPTCHA_API_KEY, USUARIO, SENHA, REPETIR, VEZES = _load_runtime_config()
    main(headless=True, usuario=USUARIO, senha=SENHA)
