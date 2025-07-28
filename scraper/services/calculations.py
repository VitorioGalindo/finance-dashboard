import numpy as np
import pandas as pd
from typing import Dict, List, Optional

class FinancialCalculations:
    
    @staticmethod
    def calculate_financial_ratios(balance_sheet: Dict, income_statement: Dict) -> Dict:
        """Calculate comprehensive financial ratios"""
        try:
            # Extract key values (handling potential missing data)
            current_assets = balance_sheet.get('total_current_assets', 0)
            total_assets = balance_sheet.get('total_assets', 0)
            current_liabilities = balance_sheet.get('total_current_liabilities', 0)
            total_liabilities = balance_sheet.get('total_liabilities', 0)
            total_equity = balance_sheet.get('total_equity', total_assets - total_liabilities)
            
            revenue = income_statement.get('total_revenue', 0)
            gross_profit = income_statement.get('gross_profit', 0)
            operating_income = income_statement.get('operating_income', 0)
            net_income = income_statement.get('net_income', 0)
            
            ratios = {
                'liquidity_ratios': {
                    'current_ratio': current_assets / current_liabilities if current_liabilities > 0 else 0,
                    'quick_ratio': (current_assets - balance_sheet.get('inventory', 0)) / current_liabilities if current_liabilities > 0 else 0,
                    'cash_ratio': balance_sheet.get('cash_and_equivalents', 0) / current_liabilities if current_liabilities > 0 else 0
                },
                'profitability_ratios': {
                    'gross_margin': gross_profit / revenue if revenue > 0 else 0,
                    'operating_margin': operating_income / revenue if revenue > 0 else 0,
                    'net_margin': net_income / revenue if revenue > 0 else 0,
                    'roe': net_income / total_equity if total_equity > 0 else 0,
                    'roa': net_income / total_assets if total_assets > 0 else 0,
                    'roic': operating_income / (total_equity + balance_sheet.get('total_debt', 0)) if (total_equity + balance_sheet.get('total_debt', 0)) > 0 else 0
                },
                'leverage_ratios': {
                    'debt_to_equity': balance_sheet.get('total_debt', 0) / total_equity if total_equity > 0 else 0,
                    'debt_to_assets': balance_sheet.get('total_debt', 0) / total_assets if total_assets > 0 else 0,
                    'interest_coverage': operating_income / income_statement.get('interest_expense', 1) if income_statement.get('interest_expense', 0) > 0 else 0
                },
                'efficiency_ratios': {
                    'asset_turnover': revenue / total_assets if total_assets > 0 else 0,
                    'inventory_turnover': income_statement.get('cost_of_goods_sold', 0) / balance_sheet.get('inventory', 1) if balance_sheet.get('inventory', 0) > 0 else 0,
                    'receivables_turnover': revenue / balance_sheet.get('accounts_receivable', 1) if balance_sheet.get('accounts_receivable', 0) > 0 else 0
                }
            }
            
            return ratios
            
        except Exception as e:
            return {'error': f'Error calculating ratios: {str(e)}'}
    
    @staticmethod
    def calculate_market_ratios(market_data: Dict, financial_data: Dict) -> Dict:
        """Calculate market valuation ratios"""
        try:
            market_cap = market_data.get('market_cap', 0)
            share_price = market_data.get('share_price', 0)
            shares_outstanding = market_data.get('shares_outstanding', 0)
            
            net_income = financial_data.get('net_income', 0)
            book_value = financial_data.get('total_equity', 0)
            revenue = financial_data.get('total_revenue', 0)
            ebitda = financial_data.get('ebitda', 0)
            
            earnings_per_share = net_income / shares_outstanding if shares_outstanding > 0 else 0
            book_value_per_share = book_value / shares_outstanding if shares_outstanding > 0 else 0
            
            ratios = {
                'valuation_ratios': {
                    'pe_ratio': share_price / earnings_per_share if earnings_per_share > 0 else 0,
                    'pb_ratio': share_price / book_value_per_share if book_value_per_share > 0 else 0,
                    'ev_ebitda': (market_cap + financial_data.get('total_debt', 0) - financial_data.get('cash', 0)) / ebitda if ebitda > 0 else 0,
                    'price_to_sales': market_cap / revenue if revenue > 0 else 0,
                    'price_to_book': market_cap / book_value if book_value > 0 else 0
                },
                'per_share_data': {
                    'earnings_per_share': earnings_per_share,
                    'book_value_per_share': book_value_per_share,
                    'dividend_per_share': financial_data.get('dividends_paid', 0) / shares_outstanding if shares_outstanding > 0 else 0,
                    'cash_flow_per_share': financial_data.get('operating_cash_flow', 0) / shares_outstanding if shares_outstanding > 0 else 0
                },
                'market_data': {
                    'market_cap': market_cap,
                    'enterprise_value': market_cap + financial_data.get('total_debt', 0) - financial_data.get('cash', 0),
                    'shares_outstanding': shares_outstanding,
                    'float_shares': shares_outstanding * 0.6  # Approximate free float
                }
            }
            
            return ratios
            
        except Exception as e:
            return {'error': f'Error calculating market ratios: {str(e)}'}
    
    @staticmethod
    def calculate_technical_indicators(prices: List[float], volumes: List[int] = None) -> Dict:
        """Calculate technical analysis indicators"""
        try:
            if not prices or len(prices) < 2:
                return {'error': 'Insufficient price data'}
            
            prices_array = np.array(prices)
            
            # Simple Moving Averages
            sma_20 = np.mean(prices_array[-20:]) if len(prices_array) >= 20 else np.mean(prices_array)
            sma_50 = np.mean(prices_array[-50:]) if len(prices_array) >= 50 else np.mean(prices_array)
            sma_200 = np.mean(prices_array[-200:]) if len(prices_array) >= 200 else np.mean(prices_array)
            
            # RSI calculation
            def calculate_rsi(prices, period=14):
                if len(prices) < period + 1:
                    return 50  # Neutral RSI
                
                deltas = np.diff(prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[-period:])
                avg_loss = np.mean(losses[-period:])
                
                if avg_loss == 0:
                    return 100
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # Bollinger Bands
            sma_20_full = sma_20
            std_20 = np.std(prices_array[-20:]) if len(prices_array) >= 20 else np.std(prices_array)
            
            indicators = {
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'sma_200': round(sma_200, 2),
                'rsi': round(calculate_rsi(prices_array), 2),
                'bollinger_bands': {
                    'upper': round(sma_20_full + (2 * std_20), 2),
                    'middle': round(sma_20_full, 2),
                    'lower': round(sma_20_full - (2 * std_20), 2)
                },
                'current_price': round(prices_array[-1], 2),
                'price_change': round(prices_array[-1] - prices_array[-2], 2) if len(prices_array) >= 2 else 0,
                'price_change_percent': round(((prices_array[-1] - prices_array[-2]) / prices_array[-2]) * 100, 2) if len(prices_array) >= 2 and prices_array[-2] != 0 else 0
            }
            
            return indicators
            
        except Exception as e:
            return {'error': f'Error calculating technical indicators: {str(e)}'}
    
    @staticmethod
    def calculate_support_resistance(prices: List[float], window: int = 20) -> Dict:
        """Calculate basic support and resistance levels"""
        try:
            if not prices or len(prices) < window:
                return {'error': 'Insufficient data for support/resistance calculation'}
            
            prices_array = np.array(prices)
            
            # Simple approach: use recent highs and lows
            recent_prices = prices_array[-window:]
            
            support_level = np.min(recent_prices)
            resistance_level = np.max(recent_prices)
            
            # Additional levels based on percentiles
            support_levels = [
                np.percentile(recent_prices, 10),
                np.percentile(recent_prices, 25),
                support_level
            ]
            
            resistance_levels = [
                resistance_level,
                np.percentile(recent_prices, 75),
                np.percentile(recent_prices, 90)
            ]
            
            return {
                'support_levels': [round(level, 2) for level in sorted(support_levels)],
                'resistance_levels': [round(level, 2) for level in sorted(resistance_levels, reverse=True)],
                'current_price': round(prices_array[-1], 2),
                'analysis_period': window
            }
            
        except Exception as e:
            return {'error': f'Error calculating support/resistance: {str(e)}'}

# Global instance
financial_calc = FinancialCalculations()
