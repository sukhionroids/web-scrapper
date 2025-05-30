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
        
        # Use more permissive context settings
        context = await browser.new_context(
            ignore_https_errors=True,  # Handle self-signed certificates
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57"
        )
        
        page = await context.new_page()
        
        # Set a longer timeout (2 minutes)
        print(f"Navigating to {login_url}...")
        try:
            # Increase timeout to 120 seconds (2 minutes)
            await page.goto(login_url, timeout=120000, wait_until="domcontentloaded")
            print("Page loaded successfully!")
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
            print(f"Error navigating to {login_url}: {str(e)}")
            # Try to take screenshot even if there was an error
            try:
                await page.screenshot(path="error_screenshot.png")
                print("Error screenshot saved as error_screenshot.png")
            except:
                pass
            await context.close()
            await browser.close()
            raise

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
