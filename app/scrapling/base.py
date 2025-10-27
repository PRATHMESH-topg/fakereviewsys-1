from abc import ABC, abstractmethod
from typing import List
from bs4 import BeautifulSoup

class ReviewScraper(ABC):
    @abstractmethod
    async def fetch_reviews(self, url: str, max_reviews: int = 50) -> List[str]:
        ...

def extract_texts_by_selectors(html: str, selectors: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for sel in selectors:
        for el in soup.select(sel):
            t = el.get_text(" ", strip=True)
            if t and len(t) > 5:
                out.append(t)
    return out
