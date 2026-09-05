import joblib
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import xgboost as xgb


class PredictionService:
    def __init__(self):
        # Ładowanie XGBoost
        self.xgb_model = joblib.load('path/to/xgboost_model.joblib')

        # Ładowanie BERT
        self.tokenizer = BertTokenizer.from_pretrained('path/to/bert/tokenizer')
        self.bert_model = BertForSequenceClassification.from_pretrained('path/to/bert/model')
        self.bert_model.eval()

    def predict_xgb(self, features):
        return self.xgb_model.predict([features])[0]

    def predict_bert(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()
        return predicted_class


# Singleton (ładowany raz)
prediction_service = PredictionService()
