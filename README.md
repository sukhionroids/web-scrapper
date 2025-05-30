# Web Scraper with Playwright

A headless browser web scraper that runs on GitHub Actions.

## Files

- `edge_playwright_github.py` - The main scraper script
- `requirements.txt` - Python dependencies
- `.github/workflows/run-scraper.yml` - GitHub Actions workflow

## How it works

This scraper runs every 6 hours via GitHub Actions. It:

1. Uses Playwright to launch a headless browser
2. Navigates to the specified URL
3. Captures the page content and takes screenshots
4. Uploads results as artifacts that you can download

## Setup

The scraper is already configured to run automatically via GitHub Actions.
You can also trigger it manually from the Actions tab in GitHub.

## Accessing results

After each run:
1. Go to the Actions tab in your GitHub repository
2. Click on the completed workflow run
3. Scroll down to the Artifacts section
4. Download the zip file containing the scraping results
