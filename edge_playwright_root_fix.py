import requests
from lxml import html
from bs4 import BeautifulSoup
import asyncio
import os
import sys
from playwright.async_api import async_playwright

# URLs
login_url = "https://salonboard.com/login"
get_url = "https://salonboard.com/KLP/schedule/salonSchedule/?date=20250531"

session_req = requests.session()

# Function to ensure browser is installed
async def install_browser():
    # Check if we need to install browser
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("Running in GitHub Actions environment. Browser will be installed via setup step.")
        return
    else:
        print("Running locally, skipping browser installation")

async def scrape_website():
    # Ensure browser is installed
    await install_browser()
    
    async with async_playwright() as p:
        print("Launching browser...")
        
        # In GitHub Actions, we'll use Chromium instead of msedge
        is_github = os.environ.get("GITHUB_ACTIONS") == "true"
        
        # ========== ROOT CAUSE FIX #1: Enhanced Browser Arguments ==========
        # Use the same robust browser arguments for both Edge and Chrome
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--ignore-certificate-errors",           # Explicitly ignore certificate errors
            "--disable-features=IsolateOrigins",     # Disable site isolation
            "--disable-site-isolation-trials",       # Disable site isolation trials
            "--disable-web-security",                # Disable CORS and other security
            "--disable-features=BlockInsecurePrivateNetworkRequests", # Allow insecure requests
            "--disable-features=CookiesWithoutSameSiteMustBeSecure",  # Allow insecure cookies
            "--disable-backgrounding-occluded-windows",  # Prevent background throttling
            "--disable-background-timer-throttling",     # Prevent timer throttling
            "--disable-background-networking",           # Prevent background networking
            "--disable-breakpad",                        # Disable crash reporting
            "--disable-component-extensions-with-background-pages",  # Disable extensions
            "--disable-features=TranslateUI",            # Disable translation
            "--disable-features=Translate",              # Disable translation
            "--disable-ipc-flooding-protection"          # Disable IPC flooding protection
        ]
        
        if is_github:
            # Use standard Chromium in GitHub Actions
            browser = await p.chromium.launch(
                headless=True,
                args=browser_args
            )
            print("Launched Chromium browser in GitHub Actions")
        else:
            # Use Edge locally
            browser = await p.chromium.launch(
                headless=True,
                channel="msedge",  # Use Edge locally
                args=browser_args
            )
            print("Launched Edge browser locally")
              # ========== ROOT CAUSE FIX #2: Enhanced Browser Context ==========
        # Use a context that mimics Edge even when using Chrome
        context = await browser.new_context(
            ignore_https_errors=True,  # Handle self-signed certificates
            # Always use Edge's user agent string
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
            viewport={"width": 1280, "height": 720},  # Smaller viewport for speed
            locale="en-US",
            timezone_id="America/New_York",
            # Device settings
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            # Edge-like HTTP headers
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-ch-ua": "\"Microsoft Edge\";v=\"113\", \"Chromium\";v=\"113\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document"
            }
        )
        
        # Configure request interception to improve performance
        if is_github:
            # Only use request interception in GitHub Actions
            await context.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,otf}', 
                               lambda route: route.abort())  # Block image and font requests
        
        page = await context.new_page()
        
        # ========== ROOT CAUSE FIX #3: Enhanced Navigation Strategy ==========
        print(f"Navigating to {login_url}...")
        
        # Add retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                print(f"Attempt {retry_count} of {max_retries}...")
                  # ========== ROOT CAUSE FIX #4: Navigation Configuration ==========
                # First clear cookies and cache
                await context.clear_cookies()
                
                # Navigate directly to the target page with more efficient wait condition
                # Use domcontentloaded instead of networkidle - this is a key change
                await page.goto(
                    login_url, 
                    timeout=60000,  # 1 minute timeout is sufficient
                    wait_until="domcontentloaded"  # Much faster than networkidle
                )
                print("Page loaded successfully!")
                
                # Now that the page is loaded, try to clear storage if possible
                try:
                    await page.evaluate("""() => {
                        try {
                            if (window.localStorage) localStorage.clear();
                            if (window.sessionStorage) sessionStorage.clear();
                        } catch (e) {
                            console.log('Could not clear storage, but continuing anyway');
                        }
                    }""")
                except Exception as e:
                    print(f"Non-critical error clearing storage: {str(e)}")
                
                # Wait briefly for JS to initialize, but don't wait for all resources
                await page.wait_for_selector("body", timeout=5000)
                
                content = await page.content()
                
                # Save screenshot for debugging
                screenshot_path = "page_screenshot.png"
                await page.screenshot(path=screenshot_path)
                print(f"Screenshot saved as {screenshot_path}")
                
                # Log page title for debugging
                title = await page.title()
                print(f"Page title: {title}")
                
                await context.close()
                await browser.close()
                return content
                
            except Exception as e:
                print(f"Error on attempt {retry_count}: {str(e)}")
                
                if retry_count >= max_retries:
                    print(f"Failed after {max_retries} attempts")
                    # Try to take screenshot even if there was an error
                    try:
                        await page.screenshot(path=f"error_screenshot_{retry_count}.png")
                        print(f"Error screenshot saved as error_screenshot_{retry_count}.png")
                    except:
                        pass
                    
                    await context.close()
                    await browser.close()
                    raise
                else:
                    print(f"Retrying in 5 seconds...")
                    await asyncio.sleep(5)  # Shorter retry wait than before

# Make script importable and executable
if __name__ == "__main__":
    try:
        # First try with asyncio.run()
        content = asyncio.run(scrape_website())
        
        # Save content to file for inspection
        with open("page_content.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Page content saved to page_content.html")
        
    except RuntimeError:
        # If that fails, use the existing event loop
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(scrape_website())
        
        # Save content to file for inspection
        with open("page_content.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Page content saved to page_content.html")
