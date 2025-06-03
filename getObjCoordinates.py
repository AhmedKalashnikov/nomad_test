import sys
from playwright.sync_api import sync_playwright
from loginUtils import nomadLogin


def get_coordinates(url: str, browser: str) -> None:
    '''
    Opens a browser instance with coordinate logging functionality.
    
    Args:
        url (str): The URL to open for codegen
        browser (str): Browser to use (chromium, firefox, webkit)
    '''

    with sync_playwright() as p:
        # launch browser
        if browser == "chromium":
            browser_instance = p.chromium.launch(headless=False)
        elif browser == "firefox":
            browser_instance = p.firefox.launch(headless=False)
        elif browser == "webkit":
            browser_instance = p.webkit.launch(headless=False)
        else:
            raise ValueError("Browser must be 'chromium', 'firefox', or 'webkit'")
        
        # create context and page, parse script 
        context = browser_instance.new_context()
        page = context.new_page()
        coordinateLogger = """
            console.log('Coordinate Logger Activated!');
            console.log('Click anywhere to see coordinates...');
            
            document.addEventListener('click', (e) => {
                const coords = {
                    viewport: { x: e.clientX, y: e.clientY },
                    page: { x: e.pageX, y: e.pageY },
                    screen: { x: e.screenX, y: e.screenY }
                };
                
                console.log('   CLICK COORDINATES:');
                console.log(`   Viewport: (${coords.viewport.x}, ${coords.viewport.y})`);
                console.log(`   Page: (${coords.page.x}, ${coords.page.y})`);
                console.log(`   Screen: (${coords.screen.x}, ${coords.screen.y})`);
                console.log(`   Element:`, e.target);
                console.log('   Python code: page.mouse.click(' + coords.viewport.x + ', ' + coords.viewport.y + ')');
                console.log('---');
            }, true);
        """

        # navigate to URL
        try:
            if url == 'app.nomad-games.eu':
                nomadLogin(page)
            else:
                page.goto('https://'+url)
        except:
            raise ValueError('Invalid URL!')
            
        # add coordinate logging with JavaScript
        page.add_init_script(coordinateLogger)
        page.evaluate(coordinateLogger)
        
        print(f"Browser opened at: {url}")
        print('Whenever you click, the coordinates will show up in the developer console log.')
        
        # keep browser open until user closes it
        try:
            # wait for page to be closed by checking if context is still active
            while not page.is_closed():
                page.wait_for_timeout(10000)  # Check every second
        except:
            pass
        
        print("Browser closed. Coordinate logging session ended.")


if __name__ == "__main__":
    url = str(sys.argv[1])
    browser = str(sys.argv[2])
    get_coordinates(url=url, browser=browser)
