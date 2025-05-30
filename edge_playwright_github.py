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
        # In GitHub Actions, we install browsers in the workflow file
        return
    else:
        print("Running locally, skipping browser installation")
        # When running locally, we assume the browser is already installed

async def scrape_website():
    # Ensure browser is installed
    await install_browser()
    
    async with async_playwright() as p:
        print("Launching browser...")
        
        # In GitHub Actions, we'll use Chromium instead of msedge
        is_github = os.environ.get("GITHUB_ACTIONS") == "true"
        
        if is_github:
            # Use standard Chromium in GitHub Actions
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security"]
            )
            print("Launched Chromium browser in GitHub Actions")
        else:
            # Use Edge locally
            browser = await p.chromium.launch(
                headless=True,
                channel="msedge",  # Use Edge locally
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security"]
            )
            print("Launched Edge browser locally")
          # Use more permissive context settings with a realistic browser profile
        context = await browser.new_context(
            ignore_https_errors=True,  # Handle self-signed certificates
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            # Appear like a common browser
            device_scale_factor=1.0,
            is_mobile=False,
            has_touch=False,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
            }
        )
        
        page = await context.new_page()
          # Set a longer timeout (2 minutes)
        print(f"Navigating to {login_url}...")
        
        # Add retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                print(f"Attempt {retry_count} of {max_retries}...")
                
                # Add a random delay before navigation to mimic human behavior
                import random
                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)
                
                # Modify the approach to handle timeouts better
                await page.goto("about:blank")  # First navigate to a blank page
                print("Navigated to blank page, now going to target...")
                
                # More permissive timeout and wait condition
                await page.goto(
                    login_url, 
                    timeout=180000,  # 3 minutes
                    wait_until="networkidle"  # Wait until network is idle
                )
                print("Page loaded successfully!")
                
                # Wait a moment for any client-side scripts to finish
                await asyncio.sleep(5)
                
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
                    print(f"Retrying in 10 seconds...")
                    await asyncio.sleep(10)  # Wait 10 seconds before retrying

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
