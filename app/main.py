# main.py
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import PredictRequest, ScrapePredictRequest, ScrapePredictResponse, ReviewPrediction
from .models.baseline_infer import BaselineModel
from .models.bert_infer import BertModel
from .scrapling.amazon import AmazonScraper
from .scrapling.flipkart import FlipkartScraper

# -------------------------------
# Windows async fix for Playwright
# -------------------------------
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="Fake Review Detector API")

# -------------------------------
# CORS middleware
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -------------------------------
# Load models once
# -------------------------------
BASELINE = BaselineModel()
BERT = None  # lazy load

def get_model(name: str):
    global BERT
    if name == "baseline":
        return BASELINE
    elif name == "bert":
        if BERT is None:
            BERT = BertModel()
        return BERT
    else:
        raise HTTPException(400, detail="Unknown model. Use 'baseline' or 'bert'.")

def pick_scraper(url: str):
    if "amazon." in url:
        return AmazonScraper()
    if "flipkart." in url:
        return FlipkartScraper()
    raise HTTPException(400, detail="Unsupported URL. Currently supports Amazon & Flipkart.")

# -------------------------------
# Health check
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------
# Single review prediction
# -------------------------------
@app.post("/predict")
def predict(req: PredictRequest):
    model = get_model("baseline")  # default
    label, score = model.predict_one(req.text)
    return {"label": label, "score": score}

# -------------------------------
# Scrape and predict reviews
# -------------------------------
@app.post("/scrape_predict", response_model=ScrapePredictResponse)
async def scrape_predict(req: ScrapePredictRequest):
    scraper = pick_scraper(req.url)

    try:
        reviews = await scraper.fetch_reviews(req.url, req.max_reviews)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(500, detail=f"Scraping failed: {str(e)}")

    if not reviews:
        raise HTTPException(404, detail="No reviews found (website might be blocking scraping).")

    # Use BERT by default if model not specified
    model_name = req.model if req.model else "bert"
    model = get_model(model_name)

    preds = []
    fake_count = 0
    for r in reviews:
        label, score = model.predict_one(r)
        fake_count += (label == "Fake")
        preds.append(ReviewPrediction(review=r, prediction=label, score=round(score, 3)))

    summary = {
        "total": len(reviews),
        "fake": fake_count,
        "genuine": len(reviews) - fake_count,
        "fake_ratio": round(fake_count / len(reviews), 3)
    }

    return ScrapePredictResponse(
        url=req.url,
        model=model_name,
        results=preds,
        summary=summary
    )
