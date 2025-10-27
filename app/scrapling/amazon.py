# amazon.py
from .base import ReviewScraper, extract_texts_by_selectors
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List
import asyncio

class AmazonScraper(ReviewScraper):
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
                    "div[data-hook='review'] span[data-hook='review-body']",
                    "span.review-text-content",
                    "span.a-size-base.review-text"
                ])
                reviews = list(set(reviews))

                # Quick retry if "see all reviews" link exists
                more_link = page.locator("a[data-hook='see-all-reviews-link-foot']")
                if await more_link.count() > 0 and len(reviews) < max_reviews:
                    try:
                        await more_link.first.click()
                        await page.wait_for_load_state("domcontentloaded")
                        await asyncio.sleep(1)
                        html = await page.content()
                        new_reviews = extract_texts_by_selectors(html, [
                            "div[data-hook='review'] span[data-hook='review-body']",
                            "span.review-text-content",
                            "span.a-size-base.review-text"
                        ])
                        reviews = list(set(reviews + new_reviews))
                    except:
                        pass

                # One scroll to load more if still less than max_reviews
                if len(reviews) < max_reviews:
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1)
                    html = await page.content()
                    new_reviews = extract_texts_by_selectors(html, [
                        "div[data-hook='review'] span[data-hook='review-body']",
                        "span.review-text-content",
                        "span.a-size-base.review-text"
                    ])
                    reviews = list(set(reviews + new_reviews))

                await browser.close()

        except PlaywrightTimeoutError:
            print(f"Timeout while fetching {url}")
        except Exception as e:
            print(f"Error scraping Amazon: {e}")

        return reviews[:max_reviews]
