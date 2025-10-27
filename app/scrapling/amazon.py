# amazon.py
import os
import asyncio
import requests
from typing import List
from .base import ReviewScraper, extract_texts_by_selectors

# Try importing Playwright safely
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class AmazonScraper(ReviewScraper):
    async def _fetch_reviews_playwright(self, url: str, max_reviews: int = 10) -> List[str]:
        """Scrape reviews using Playwright (JS-rendered version)."""
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
                await asyncio.sleep(1)

                # Extract initial reviews
                html = await page.content()
                reviews = extract_texts_by_selectors(html, [
                    "div[data-hook='review'] span[data-hook='review-body']",
                    "span.review-text-content",
                    "span.a-size-base.review-text"
                ])
                reviews = list(set(reviews))

                # "See all reviews" link
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
                    except Exception:
                        pass

                # Scroll for more reviews
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
            print(f"Error scraping Amazon with Playwright: {e}")

        return reviews[:max_reviews]

    def _fetch_reviews_static(self, url: str, max_reviews: int = 10) -> List[str]:
        """Fallback: Scrape using static HTML (Render-safe)."""
        reviews = []
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=20)
            html = resp.text
            reviews = extract_texts_by_selectors(html, [
                "div[data-hook='review'] span[data-hook='review-body']",
                "span.review-text-content",
                "span.a-size-base.review-text"
            ])
        except Exception as e:
            print(f"Error scraping Amazon (static fallback): {e}")

        return list(set(reviews))[:max_reviews]

    async def fetch_reviews(self, url: str, max_reviews: int = 10) -> List[str]:
        """
        Automatically decides whether to use Playwright or fallback requests.
        """
        # Detect Render or restricted environment
        running_on_render = (
            "RENDER" in os.environ
            or os.environ.get("DYNO")  # Heroku-style env check
            or not PLAYWRIGHT_AVAILABLE
        )

        if running_on_render:
            print("[INFO] Using static HTML scraper (Render safe mode)")
            return self._fetch_reviews_static(url, max_reviews)

        else:
            print("[INFO] Using Playwright for full scraping (local mode)")
            reviews = await self._fetch_reviews_playwright(url, max_reviews)
            if not reviews:  # fallback if Playwright fails
                print("[WARN] Playwright failed, falling back to static method.")
                reviews = self._fetch_reviews_static(url, max_reviews)
            return reviews

