from transformers import pipeline
import logging
import os

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    _instance = None
    _pipeline = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pipeline is None:
            try:
                cache_dir = os.path.join(os.path.dirname(__file__), 'model_cache')
                os.makedirs(cache_dir, exist_ok=True)
                
                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1,  # CPU
                    model_kwargs={"cache_dir": cache_dir}
                )
                logger.info("✅ Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading sentiment model: {e}")
                self._pipeline = None
    
    def analyze(self, text):
        """
        Analyze sentiment of text
        Returns: {'label': 'POSITIVE/NEGATIVE', 'score': 0.99, 'emoji': '😊', 'color': '#4ade80'}
        """
        if not text or not self._pipeline:
            return {
                'label': 'NEUTRAL',
                'score': 0.0,
                'emoji': '😐',
                'color': '#94a3b8'
            }
        
        try:
            # Truncate long messages
            text = text[:500]
            
            result = self._pipeline(text)[0]
            
            sentiment_map = {
                'POSITIVE': {'emoji': '😊', 'color': '#4ade80'},
                'NEGATIVE': {'emoji': '😞', 'color': '#f87171'}
            }
            
            label = result['label']
            extra = sentiment_map.get(label, {'emoji': '😐', 'color': '#94a3b8'})
            
            return {
                'label': label,
                'score': round(result['score'], 4),
                'emoji': extra['emoji'],
                'color': extra['color']
            }
        
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'label': 'NEUTRAL',
                'score': 0.0,
                'emoji': '😐',
                'color': '#94a3b8'
            }

# Singleton instance
sentiment_analyzer = SentimentAnalyzer()