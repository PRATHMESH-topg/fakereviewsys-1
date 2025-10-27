from joblib import load
import os
from .text_clean import clean_text
import numpy as np

ART_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "models_artifacts")
TFIDF_PATH = os.path.abspath(os.path.join(ART_DIR, "tfidf.pkl"))
LR_PATH = os.path.abspath(os.path.join(ART_DIR, "lr_model.pkl"))

class BaselineModel:
    def __init__(self):
        self.vec = load(TFIDF_PATH)
        self.clf = load(LR_PATH)

    def predict_one(self, text: str):
        tx = clean_text(text)
        X = self.vec.transform([tx])
        prob = float(self.clf.predict_proba(X)[0,1])
        label = "Fake" if prob >= 0.5 else "Genuine"
        return label, prob
