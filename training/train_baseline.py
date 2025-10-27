import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# 🔹 Apna CSV file ka path
CSV_PATH = r"D:\archive\Labelled_Yelp_Dataset.csv"
df = pd.read_csv(CSV_PATH)

# 🔹 Dataset ke column ko rename karna model ke liye
df["text"] = df["Review"].astype(str)   # Review -> text
df["label"] = df["Label"].astype(int)   # Label -> label (0/1)

# 🔹 TF-IDF Vectorizer
tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
X = tfidf.fit_transform(df["text"])
y = df["label"]

# 🔹 Train Logistic Regression model
model = LogisticRegression()
model.fit(X, y)

# 🔹 Save vectorizer and model
joblib.dump(tfidf, "tfidf.pkl")
joblib.dump(model, "lr_model.pkl")

print("✅ Model training completed and saved as tfidf.pkl & lr_model.pkl")

