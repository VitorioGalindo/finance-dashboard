from flask import Blueprint, request, jsonify
from auth import require_api_key, optional_api_key
from utils import create_response, create_error_response, parse_tickers
from models import Ticker, TechnicalIndicator
import logging

logger = logging.getLogger(__name__)

technical_bp = Blueprint('technical_analysis', __name__)

@technical_bp.route('/technical-analysis/<ticker>/indicators', methods=['GET'])
@require_api_key
def get_technical_indicators(ticker):
    """
    GET /technical-analysis/{ticker}/indicators
    Indicadores técnicos (SMA, EMA, RSI, MACD, Bollinger)
    """
    try:
        indicators = request.args.get('indicators', 'sma,ema,rsi,macd,bollinger')
        period = int(request.args.get('period', 20))
        
        ticker_obj = Ticker.query.filter_by(symbol=ticker.upper()).first()
        
        if not ticker_obj:
            return create_error_response("Ticker not found", 404)
        
        # Buscar indicadores técnicos mais recentes
        latest_indicator = TechnicalIndicator.query.filter_by(
            ticker_id=ticker_obj.id
        ).order_by(TechnicalIndicator.indicator_date.desc()).first()
        
        if not latest_indicator:
            return create_error_response("Technical indicators not available for this ticker", 404)
        
        # Construir resposta baseada nos indicadores solicitados
        requested_indicators = [i.strip() for i in indicators.split(',')]
        
        indicators_data = {
            "ticker": ticker.upper(),
            "date": latest_indicator.indicator_date.isoformat(),
            "indicators": {}
        }
        
        # Médias móveis simples
        if 'sma' in requested_indicators:
            indicators_data["indicators"].update({
                "sma_20": latest_indicator.sma_20,
                "sma_50": latest_indicator.sma_50,
                "sma_200": latest_indicator.sma_200
            })
        
        # Médias móveis exponenciais
        if 'ema' in requested_indicators:
            indicators_data["indicators"].update({
                "ema_20": latest_indicator.ema_20,
                "ema_50": latest_indicator.ema_50
            })
        
        # RSI
        if 'rsi' in requested_indicators:
            indicators_data["indicators"]["rsi"] = latest_indicator.rsi
        
        # MACD
        if 'macd' in requested_indicators:
            indicators_data["indicators"]["macd"] = {
                "macd_line": latest_indicator.macd_line,
                "signal_line": latest_indicator.macd_signal,
                "histogram": latest_indicator.macd_histogram
            }
        
        # Bandas de Bollinger
        if 'bollinger' in requested_indicators:
            indicators_data["indicators"]["bollinger_bands"] = {
                "upper": latest_indicator.bb_upper,
                "middle": latest_indicator.bb_middle,
                "lower": latest_indicator.bb_lower
            }
        
        # Análise dos sinais
        signals = []
        
        # Sinal RSI
        if latest_indicator.rsi:
            if latest_indicator.rsi > 70:
                signals.append({"type": "overbought", "indicator": "RSI", "value": latest_indicator.rsi, "signal": "sell"})
            elif latest_indicator.rsi < 30:
                signals.append({"type": "oversold", "indicator": "RSI", "value": latest_indicator.rsi, "signal": "buy"})
        
        # Sinal MACD
        if latest_indicator.macd_line and latest_indicator.macd_signal:
            if latest_indicator.macd_line > latest_indicator.macd_signal and latest_indicator.macd_histogram > 0:
                signals.append({"type": "bullish_crossover", "indicator": "MACD", "signal": "buy"})
            elif latest_indicator.macd_line < latest_indicator.macd_signal and latest_indicator.macd_histogram < 0:
                signals.append({"type": "bearish_crossover", "indicator": "MACD", "signal": "sell"})
        
        indicators_data["signals"] = signals
        
        return create_response(data=indicators_data)
        
    except ValueError:
        return create_error_response("Invalid period parameter", 400)
    except Exception as e:
        logger.error(f"Error retrieving technical indicators for {ticker}: {str(e)}")
        return create_error_response("Failed to retrieve technical indicators", 500)

@technical_bp.route('/technical-analysis/<ticker>/support-resistance', methods=['GET'])
@require_api_key
def get_support_resistance(ticker):
    """
    GET /technical-analysis/{ticker}/support-resistance
    Níveis de suporte e resistência
    """
    try:
        ticker_obj = Ticker.query.filter_by(symbol=ticker.upper()).first()
        
        if not ticker_obj:
            return create_error_response("Ticker not found", 404)
        
        # Buscar cotações recentes para calcular suporte e resistência
        from models import Quote
        
        recent_quotes = Quote.query.filter_by(
            ticker_id=ticker_obj.id
        ).order_by(Quote.quote_datetime.desc()).limit(60).all()
        
        if not recent_quotes:
            return create_error_response("Insufficient price data for analysis", 404)
        
        # Calcular níveis de suporte e resistência baseados em máximas e mínimas
        prices = [quote.price for quote in recent_quotes if quote.price]
        highs = [quote.high_price for quote in recent_quotes if quote.high_price]
        lows = [quote.low_price for quote in recent_quotes if quote.low_price]
        
        if not prices or not highs or not lows:
            return create_error_response("Insufficient price data for analysis", 404)
        
        current_price = prices[0]
        
        # Calcular níveis de resistência (máximas significativas)
        resistance_levels = []
        sorted_highs = sorted(set(highs), reverse=True)
        
        for level in sorted_highs[:3]:  # Top 3 resistance levels
            if level > current_price:
                distance_percent = ((level - current_price) / current_price) * 100
                resistance_levels.append({
                    "level": round(level, 2),
                    "type": "resistance",
                    "strength": "strong" if level in sorted_highs[:1] else "moderate",
                    "distance_percent": round(distance_percent, 2),
                    "touches": highs.count(level)
                })
        
        # Calcular níveis de suporte (mínimas significativas)
        support_levels = []
        sorted_lows = sorted(set(lows))
        
        for level in sorted_lows[:3]:  # Bottom 3 support levels
            if level < current_price:
                distance_percent = ((current_price - level) / current_price) * 100
                support_levels.append({
                    "level": round(level, 2),
                    "type": "support",
                    "strength": "strong" if level in sorted_lows[:1] else "moderate",
                    "distance_percent": round(distance_percent, 2),
                    "touches": lows.count(level)
                })
        
        support_resistance_data = {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "analysis_date": recent_quotes[0].quote_datetime.isoformat() + "Z",
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "key_levels": support_levels + resistance_levels
        }
        
        return create_response(data=support_resistance_data)
        
    except Exception as e:
        logger.error(f"Error calculating support/resistance for {ticker}: {str(e)}")
        return create_error_response("Failed to calculate support and resistance levels", 500)

@technical_bp.route('/technical-analysis/<ticker>/patterns', methods=['GET'])
@require_api_key
def get_chart_patterns(ticker):
    """
    GET /technical-analysis/{ticker}/patterns
    Padrões gráficos
    """
    try:
        ticker_obj = Ticker.query.filter_by(symbol=ticker.upper()).first()
        
        if not ticker_obj:
            return create_error_response("Ticker not found", 404)
        
        # Buscar dados históricos para análise de padrões
        from models import Quote
        from datetime import datetime, timedelta
        
        # Últimos 3 meses de dados
        start_date = datetime.utcnow() - timedelta(days=90)
        
        quotes = Quote.query.filter(
            Quote.ticker_id == ticker_obj.id,
            Quote.quote_datetime >= start_date
        ).order_by(Quote.quote_datetime.asc()).all()
        
        if len(quotes) < 20:
            return create_error_response("Insufficient data for pattern analysis", 404)
        
        # Análise básica de padrões (simulada)
        # Em uma implementação real, usaria algoritmos de reconhecimento de padrões
        
        prices = [quote.price for quote in quotes[-20:]]  # Últimos 20 períodos
        
        # Detectar tendência
        trend = "neutral"
        if len(prices) >= 10:
            early_avg = sum(prices[:5]) / 5
            recent_avg = sum(prices[-5:]) / 5
            
            if recent_avg > early_avg * 1.05:
                trend = "bullish"
            elif recent_avg < early_avg * 0.95:
                trend = "bearish"
        
        # Padrões detectados (simulados)
        detected_patterns = []
        
        # Padrão de alta baseado na tendência
        if trend == "bullish":
            detected_patterns.append({
                "pattern_name": "Ascending Triangle",
                "type": "bullish",
                "confidence": 75,
                "formation_period": "15 days",
                "target_price": round(prices[-1] * 1.08, 2),
                "stop_loss": round(prices[-1] * 0.95, 2),
                "description": "Padrão de consolidação com tendência de alta"
            })
        
        # Padrão de baixa baseado na tendência
        elif trend == "bearish":
            detected_patterns.append({
                "pattern_name": "Descending Triangle",
                "type": "bearish",
                "confidence": 70,
                "formation_period": "12 days",
                "target_price": round(prices[-1] * 0.92, 2),
                "stop_loss": round(prices[-1] * 1.05, 2),
                "description": "Padrão de consolidação com tendência de baixa"
            })
        
        # Padrão neutro
        else:
            detected_patterns.append({
                "pattern_name": "Rectangle",
                "type": "neutral",
                "confidence": 60,
                "formation_period": "20 days",
                "description": "Padrão de consolidação lateral"
            })
        
        # Análise de volume
        volumes = [quote.volume for quote in quotes[-10:] if quote.volume]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        recent_volume = volumes[-1] if volumes else 0
        
        volume_analysis = {
            "average_volume": int(avg_volume),
            "recent_volume": int(recent_volume),
            "volume_trend": "increasing" if recent_volume > avg_volume * 1.2 else "decreasing" if recent_volume < avg_volume * 0.8 else "stable"
        }
        
        patterns_data = {
            "ticker": ticker.upper(),
            "analysis_date": quotes[-1].quote_datetime.isoformat() + "Z",
            "current_price": quotes[-1].price,
            "trend": trend,
            "detected_patterns": detected_patterns,
            "volume_analysis": volume_analysis,
            "data_period": {
                "start_date": quotes[0].quote_datetime.isoformat() + "Z",
                "end_date": quotes[-1].quote_datetime.isoformat() + "Z",
                "total_periods": len(quotes)
            }
        }
        
        return create_response(data=patterns_data)
        
    except Exception as e:
        logger.error(f"Error analyzing chart patterns for {ticker}: {str(e)}")
        return create_error_response("Failed to analyze chart patterns", 500)
