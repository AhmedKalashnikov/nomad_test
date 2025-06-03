from playwright.sync_api import sync_playwright, Page 
import csv
from pathlib import Path

def get_user_credentials(credsDir: str) -> list:
        '''
        Reads and returns user credentials from a csv.
        
        Args: 
            credsDir (str): the directory of your csv file that should contain credentials.
        '''

        with open(credsDir, 'r') as credsFile:
            credsReader = csv.reader(credsFile)
            creds = list(credsReader)
            flat_creds = [item for sublist in creds for item in sublist]
            if len(flat_creds) >= 4:
                return flat_creds[:4]
            else:
                raise ValueError("Missing credentials in CSV file")
                

def nomadLogin(page: Page) -> None:
    '''Logs in with credentials from test environment.'''
    email, pwd, email2, pwd2 = get_user_credentials('creds.csv')
    try:
        page.goto('https://app.nomad-games.eu')
        page.get_by_role("button", name="Log in (manually)").click()
        page.get_by_role("textbox", name="Email (username)").click()
        page.get_by_role("textbox", name="Email (username)").fill(email)
        page.get_by_role("textbox", name="Password").click()
        page.get_by_role("textbox", name="Password").fill(str(pwd))
        page.locator(".mat-checkbox-inner-container").click()
        page.get_by_role("button", name="Log in").click()

    except Exception as e:
        print('LOGIN FAILED: ' + str(e))
        raise

def login_and_save_profile(target_url='app.nomad-games.eu', browser='chromium') -> str:

    profile_path = f"user_data/{browser}"
    Path(profile_path).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = getattr(p, browser).launch_persistent_context(
            user_data_dir=profile_path,
            headless=True
        )
        page = browser.new_page()
        page.goto(target_url)
        nomadLogin(page)

        # počkej chvilku na uložení session
        page.wait_for_timeout(2000)
        browser.close()

    return profile_path

if __name__ == "__main__":
    login_and_save_profile()
