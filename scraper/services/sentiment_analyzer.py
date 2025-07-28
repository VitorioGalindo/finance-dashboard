import re
from typing import Dict, List
from textblob import TextBlob

class SentimentAnalyzer:
    
    def __init__(self):
        # Brazilian Portuguese positive/negative keywords
        self.positive_keywords = [
            'alta', 'subida', 'crescimento', 'lucro', 'ganho', 'positivo', 'otimista',
            'forte', 'bom', 'excelente', 'recuperação', 'melhora', 'valorização',
            'aumento', 'expansão', 'sucesso', 'avanço', 'progresso'
        ]
        
        self.negative_keywords = [
            'queda', 'baixa', 'perda', 'prejuízo', 'negativo', 'pessimista',
            'fraco', 'ruim', 'péssimo', 'crise', 'declínio', 'desvalorização',
            'redução', 'retração', 'fracasso', 'recuo', 'deterioração'
        ]
        
        self.neutral_keywords = [
            'estável', 'mantém', 'lateral', 'sem alteração', 'inalterado',
            'neutro', 'equilibrado', 'constante'
        ]
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of financial text"""
        if not text:
            return {
                'sentiment': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0
            }
        
        # Clean and normalize text
        text_lower = text.lower()
        
        # Count keyword occurrences
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in keyword in text_lower)
        neutral_count = sum(1 for keyword in self.neutral_keywords if keyword in text_lower)
        
        # Use TextBlob for additional sentiment analysis
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
        except:
            polarity = 0.0
            subjectivity = 0.5
        
        # Combine keyword-based and TextBlob analysis
        keyword_score = (positive_count - negative_count) / max(len(text.split()), 1)
        combined_score = (keyword_score + polarity) / 2
        
        # Determine sentiment category
        if combined_score > 0.1:
            sentiment = 'positive'
        elif combined_score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence based on keyword density and subjectivity
        total_keywords = positive_count + negative_count + neutral_count
        keyword_density = total_keywords / max(len(text.split()), 1)
        confidence = min(keyword_density + (1 - subjectivity), 1.0)
        
        return {
            'sentiment': sentiment,
            'sentiment_score': round(combined_score, 3),
            'confidence': round(confidence, 3),
            'details': {
                'positive_keywords_found': positive_count,
                'negative_keywords_found': negative_count,
                'neutral_keywords_found': neutral_count,
                'textblob_polarity': round(polarity, 3),
                'textblob_subjectivity': round(subjectivity, 3)
            }
        }
    
    def calculate_impact_score(self, text: str, related_tickers: List[str] = None) -> float:
        """Calculate potential market impact score (0-10)"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # High impact keywords
        high_impact_keywords = [
            'petrobras', 'vale', 'itau', 'banco do brasil', 'bradesco',
            'selic', 'juros', 'inflação', 'pib', 'bovespa', 'cvm',
            'fusão', 'aquisição', 'ipo', 'dividendos', 'resultado',
            'balanço', 'lucro', 'prejuízo', 'receita'
        ]
        
        # Company-specific impact
        company_impact = sum(2 for keyword in high_impact_keywords if keyword in text_lower)
        
        # Length-based impact (longer articles might be more impactful)
        length_impact = min(len(text) / 1000, 3)  # Max 3 points for length
        
        # Ticker-specific impact
        ticker_impact = len(related_tickers) * 0.5 if related_tickers else 0
        
        # Sentiment strength impact
        sentiment_result = self.analyze_sentiment(text)
        sentiment_impact = abs(sentiment_result['sentiment_score']) * 2
        
        total_impact = company_impact + length_impact + ticker_impact + sentiment_impact
        
        # Normalize to 0-10 scale
        impact_score = min(total_impact, 10.0)
        
        return round(impact_score, 1)
    
    def analyze_news_batch(self, news_list: List[Dict]) -> List[Dict]:
        """Analyze sentiment for a batch of news articles"""
        analyzed_news = []
        
        for news_item in news_list:
            # Combine title and summary for analysis
            text_to_analyze = f"{news_item.get('title', '')} {news_item.get('summary', '')}"
            
            sentiment_result = self.analyze_sentiment(text_to_analyze)
            impact_score = self.calculate_impact_score(
                text_to_analyze, 
                news_item.get('related_tickers', [])
            )
            
            # Add sentiment analysis to news item
            analyzed_item = news_item.copy()
            analyzed_item.update({
                'sentiment': sentiment_result['sentiment'],
                'sentiment_score': sentiment_result['sentiment_score'],
                'sentiment_confidence': sentiment_result['confidence'],
                'impact_score': impact_score
            })
            
            analyzed_news.append(analyzed_item)
        
        return analyzed_news

# Global instance
sentiment_analyzer = SentimentAnalyzer()
