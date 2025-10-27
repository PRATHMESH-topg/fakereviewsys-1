from pydantic import BaseModel

class PredictRequest(BaseModel):
    text: str

class ScrapePredictRequest(BaseModel):
    url: str
    max_reviews: int = 50
    model: str = "baseline"  # or "bert"

class ReviewPrediction(BaseModel):
    review: str
    prediction: str
    score: float

class ScrapePredictResponse(BaseModel):
    url: str
    model: str
    results: list[ReviewPrediction]
    summary: dict
