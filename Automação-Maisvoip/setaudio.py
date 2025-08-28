from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
    
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://##########.maisvoipdiscador.com.br:#####/maisvoip/autenticacao.php")

        page.fill("#login", "#######")
        page.fill("#senha", "##########")
        page.get_by_role("button", name="Entrar").click()

        page.get_by_role("link", name="IPBX").click()
        page.get_by_text("Funcionalidades").click()
        page.get_by_role("link", name="URA").click()

        frame = page.frame(name="Post")

        frame.get_by_role("row", name="FGTS Reversa").get_by_role("link").click()
        frame.fill("#obj_ura_tecla_1", "1")
        
        frame.select_option("#obj_ura_tipo_dest_1", "A")
        frame.select_option("#obj_ura_dest_1", "155")
        frame.get_by_role("button", name="Salvar").click()
        frame.get_by_role("link", name="Recarregar").click()

        context.close()
        browser.close()

if __name__ == "__main__":
    run()
