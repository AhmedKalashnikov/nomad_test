from playwright.sync_api import sync_playwright
from loginUtils import nomadLogin

def runAuthCodegen(browser='chromium', url='https://app.nomad-games.eu'):
    with sync_playwright() as p:
        browser = getattr(p, browser)
        context = browser.launch_persistent_context(
            user_data_dir=f"user_data/{browser}",
            headless=False
        )
        page = context.new_page()
        page.goto(url)
        nomadLogin(page)
        page.pause()  # opens playwright inspector
        context.close()

if __name__ == "__main__":
    runAuthCodegen()