import os
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# 🔹 Apna dataset path
CSV_PATH = r"D:\archive\fake_reviews_sample.csv"
MODEL_NAME = "distilbert-base-uncased"

# 🔹 CSV read karo aur column rename karo
df = pd.read_csv(CSV_PATH)[["Review", "Label"]]
df = df.rename(columns={"Review": "text", "Label": "label"})

# 🔹 HuggingFace Dataset banao
ds = Dataset.from_pandas(df)

# 🔹 Tokenizer load karo
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# 🔹 Tokenization function
def tok(ex):
    return tokenizer(ex["text"], truncation=True, padding="max_length", max_length=256)

ds = ds.map(tok, batched=True)

# 🔹 Rename target column for Trainer
ds = ds.rename_column("label", "labels")

# 🔹 Train-test split
ds = ds.train_test_split(test_size=0.2, seed=42)

# 🔹 Model load karo (binary classification)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

# 🔹 Training arguments
args = TrainingArguments(
    output_dir="./bert_out",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    num_train_epochs=2,
    evaluation_strategy="epoch",
    logging_steps=50,
    save_strategy="epoch"
)

# 🔹 Trainer setup
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=ds["train"],
    eval_dataset=ds["test"]
)

# 🔹 Train model
trainer.train()

# 🔹 Save fine-tuned model
trainer.save_model("./bert_out")
tokenizer.save_pretrained("./bert_out")

print("✅ Saved fine-tuned model to ./bert_out (update BertModel.FINETUNED_PATH)")

