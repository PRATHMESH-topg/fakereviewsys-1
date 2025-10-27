# flipkart.py
from .base import ReviewScraper, extract_texts_by_selectors
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List
import asyncio

class FlipkartScraper(ReviewScraper):
    async def fetch_reviews(self, url: str, max_reviews: int = 10) -> List[str]:
        reviews = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                )

                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 720}
                )

                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(1)  # small wait for JS

                # Extract initial reviews
                html = await page.content()
                reviews = extract_texts_by_selectors(html, [
                    "div._6K-7Co",        # review text block
                    "div.t-ZTKy div div", # expanded text
                ])
                reviews = list(set(reviews))

                # Pagination / next pages
                tries = 0
                while len(reviews) < max_reviews and tries < 3:
                    tries += 1
                    next_btn = page.locator("a._1LKTO3:has-text('Next')")
                    if await next_btn.count() > 0:
                        try:
                            await next_btn.first.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await asyncio.sleep(1)
                            html = await page.content()
                            new_reviews = extract_texts_by_selectors(html, [
                                "div._6K-7Co",
                                "div.t-ZTKy div div",
                            ])
                            reviews = list(set(reviews + new_reviews))
                        except:
                            break
                    else:
                        break

                # Final scroll attempt if still less than max_reviews
                if len(reviews) < max_reviews:
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1)
                    html = await page.content()
                    new_reviews = extract_texts_by_selectors(html, [
                        "div._6K-7Co",
                        "div.t-ZTKy div div",
                    ])
                    reviews = list(set(reviews + new_reviews))

                await browser.close()

        except PlaywrightTimeoutError:
            print(f"Timeout while fetching {url}")
        except Exception as e:
            print(f"Error scraping Flipkart: {e}")

        return reviews[:max_reviews]
