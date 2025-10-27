import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .text_clean import clean_text

MODEL_NAME = "distilbert-base-uncased"
# If you fine-tuned, change to your folder path
FINETUNED_PATH = None  # e.g., "./models_artifacts/bert_finetuned"

class BertModel:
    def __init__(self):
        name = FINETUNED_PATH or MODEL_NAME
        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model = AutoModelForSequenceClassification.from_pretrained(name)
        self.model.eval()

    @torch.inference_mode()
    def predict_one(self, text: str):
        tx = clean_text(text)
        toks = self.tokenizer(tx, return_tensors="pt", truncation=True, max_length=256)
        out = self.model(**toks)
        probs = out.logits.softmax(dim=-1).cpu().numpy()[0]
        # assume id 1 = Fake, 0 = Genuine (adjust to your fine-tuning)
        prob_fake = float(probs[1]) if probs.shape[-1] >=2 else float(probs[0])
        label = "Fake" if prob_fake >= 0.5 else "Genuine"
        return label, prob_fake
