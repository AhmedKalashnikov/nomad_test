import logging, pytest, os
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from loginUtils import nomadLogin

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "locale": "cs-CZ",
        "timezone_id": "Europe/Prague",
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 50.0755, "longitude": 14.4378}, 
        "ignore_https_errors": True,
        "bypass_csp": True,
        "java_script_enabled": True
    }

@pytest.fixture(autouse=True)
def configure_timeouts(page):
    page.set_default_timeout(15000) 
    page.set_default_navigation_timeout(10000)  


@pytest.fixture(scope="session")
def browser_launch_args():
    return {
        "args": ["--disable-blink-features=AutomationControlled",
                 "--disable-dev-shm-usage",
                "--disable-extensions-except=/path/to/extension",
                "--disable-extensions",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-default-apps"]    
    }


@pytest.fixture(autouse=True)
def per_test_logging(request):
    test_name = request.node.name
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{test_name}_{datetime.now().strftime('%H-%M-%S-%f')}.log")
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Logger itself accepts all levels
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler - logs ALL levels (DEBUG and above)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)  # File gets everything
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - logs only ERROR and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # Console gets only ERROR and CRITICAL
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logging.info(f"--- STARTING {test_name} ---")
    
    yield
    
    logging.info(f"--- END OF {test_name} --- \n")
    
    # Clean up handlers
    logger.removeHandler(file_handler)
    logger.removeHandler(console_handler)
    file_handler.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    
    # Check if a test failed
    if rep.when == "call" and rep.failed:
        page = None
        for fixture_name in item.fixturenames:
            if fixture_name == "page":
                page = item.funcargs[fixture_name]
                break
                
        if page:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_name = item.nodeid.replace("/", "_").replace(":", "_")
            screenshotPath = Path(f"screenshots/failure-{test_name}-{timestamp}.png")
            page.screenshot(path=screenshotPath)
            print(f"Screenshot saved to {screenshotPath}")



@pytest.fixture(scope="session")
def codegen_context(browser: Browser, browser_context_args):
    '''Special fixture for playwright codegen that maintains login state.
    Uses browser from pytest-playwright.'''

    context = browser.new_context(**browser_context_args)
    
    page = context.new_page()
    nomadLogin(page)
    
    yield context, page
    
    context.close()



