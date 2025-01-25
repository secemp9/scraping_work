from playwright.async_api import async_playwright
import asyncio


async def run_headless():
    async with async_playwright() as p:
        # Launch headless browser with advanced stealth settings
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-features=site-per-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-infobars',
            '--disable-gpu',
            '--lang=en-US,en',
        ])

        # Create a new browser context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )

        # Hide automation-related properties
        await context.add_init_script("""
            // Pass the WebDriver test
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Mock plugins and languages
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        # Open a new page
        page = await context.new_page()

        # Navigate to the URL
        try:
            await page.goto("https://t.co/JkQ7hF56Lt", wait_until='domcontentloaded')
            await page.wait_for_load_state('networkidle')

            # Print the page title
            title = await page.title()
            print("Page Title:", title)

            # Take a screenshot
            await page.screenshot(path="screenshot.png")
            print("Screenshot saved as 'screenshot.png'")

            # Extract content
            content = await page.content()
            print("Page Content (First 500 characters):", content[:500])

        except Exception as e:
            print(f"Error during navigation: {e}")

        # Close the browser
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_headless())
