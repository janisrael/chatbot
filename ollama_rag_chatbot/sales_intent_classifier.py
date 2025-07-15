# sales_intent_classifier.py

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os




# Load dataset from CSV
csv_path = '/home/jan-israel/dev/chatbot/ollama_rag_chatbot/data/convo_data.csv'
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Training data not found at {csv_path}")

df = pd.read_csv(csv_path)
texts = df["message"].astype(str).tolist()
labels = df["sales_flag"].astype(str).tolist()

# Train the model
model = make_pipeline(CountVectorizer(), MultinomialNB())
model.fit(texts, labels)

# Save model (optional)
joblib.dump(model, "sales_classifier.joblib")

def classify_message(message):
    return model.predict([message])[0]



# Define training data
training_data = [
    ("I'm interested in your services", "interest"),
    ("Can I hire you for a project?", "interest"),
    ("I want to work with your team", "interest"),
    ("Let's work together", "interest"),
    ("I'm ready to begin", "interest"),
    
    ("How much does it cost?", "inquiry"),
    ("Can you provide a quote?", "inquiry"),
    ("What’s your pricing?", "inquiry"),
    ("Do you offer discounts?", "inquiry"),
    ("What are your rates?", "inquiry"),

    ("I can’t afford it", "objection"),
    ("That’s too expensive", "objection"),
    ("I'm not sure about the price", "objection"),
    ("I’ll think about it", "objection"),
    ("Seems out of budget", "objection"),

    ("Hello", "other"),
    ("Hi there", "other"),
    ("I’m just browsing", "other"),
    ("Cool website", "other"),
    ("What do you do?", "other"),
]

# Prepare and train the model
texts, labels = zip(*training_data)
model = make_pipeline(CountVectorizer(), MultinomialNB())
model.fit(texts, labels)

# Save the trained model
MODEL_PATH = "sales_classifier.joblib"
joblib.dump(model, MODEL_PATH)

def classify_message(message):
    """Load trained model and classify a new message"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Classifier model not found at {MODEL_PATH}. Make sure to train and save it first.")
    clf = joblib.load(MODEL_PATH)
    return clf.predict([message])[0]
