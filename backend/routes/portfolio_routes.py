
from flask import Blueprint, jsonify
from backend.models import PortfolioConfig, PortfolioHistory, PortfolioMetric
import traceback

portfolio_bp = Blueprint('portfolio_bp', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('/config', methods=['GET'])
def get_portfolio_config():
    """
    Retorna a lista de ativos e suas configurações na carteira.
    """
    try:
        configs = PortfolioConfig.query.all()
        return jsonify([config.to_dict() for config in configs])
    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_portfolio_config: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": "Ocorreu um erro interno no servidor ao buscar a configuração do portfólio.",
            "details": str(e)
        }), 500

@portfolio_bp.route('/history', methods=['GET'])
def get_portfolio_history():
    """
    Retorna o histórico de valores da carteira, ordenado por data.
    """
    try:
        # Ordenar por data é importante para gráficos de histórico
        history_data = PortfolioHistory.query.order_by(PortfolioHistory.date.asc()).all()
        return jsonify([item.to_dict() for item in history_data])
    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_portfolio_history: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": "Ocorreu um erro interno no servidor ao buscar o histórico do portfólio.",
            "details": str(e)
        }), 500

@portfolio_bp.route('/metrics', methods=['GET'])
def get_portfolio_metrics():
    """
    Retorna as métricas de performance da carteira.
    """
    try:
        metrics = PortfolioMetric.query.all()
        return jsonify([metric.to_dict() for metric in metrics])
    except Exception as e:
        print("="*80)
        print(f"ERRO DETALHADO em get_portfolio_metrics: {e}")
        traceback.print_exc()
        print("="*80)
        return jsonify({
            "error": "Ocorreu um erro interno no servidor ao buscar as métricas do portfólio.",
            "details": str(e)
        }), 500
