from flask import Blueprint, jsonify, request
from backend.models import PortfolioConfig, PortfolioHistory, PortfolioMetric, RealtimeQuote
from backend import db  # Importa a instância do db
import traceback

portfolio_bp = Blueprint('portfolio_bp', __name__, url_prefix='/api/portfolio')

# --- ROTAS DE LEITURA (GET) ---

@portfolio_bp.route('/config', methods=['GET'])
def get_portfolio_config():
    """Retorna a configuração de ativos da carteira."""
    try:
        config = PortfolioConfig.query.all()
        return jsonify([item.to_dict() for item in config])
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Erro ao buscar configuração do portfólio", "details": str(e)}), 500

# ... (as outras rotas GET para /history, /metrics, e /quotes permanecem as mesmas da resposta anterior) ...
@portfolio_bp.route('/history', methods=['GET'])
def get_portfolio_history():
    try:
        history = PortfolioHistory.query.order_by(PortfolioHistory.date.asc()).all()
        return jsonify([item.to_dict() for item in history])
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Erro ao buscar histórico do portfólio", "details": str(e)}), 500

@portfolio_bp.route('/metrics', methods=['GET'])
def get_portfolio_metrics():
    try:
        metrics = PortfolioMetric.query.all()
        return jsonify([item.to_dict() for item in metrics])
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Erro ao buscar métricas do portfólio", "details": str(e)}), 500
        
@portfolio_bp.route('/quotes', methods=['GET'])
def get_realtime_quotes():
    try:
        quotes = RealtimeQuote.query.all()
        quotes_dict = {quote.ticker: quote.to_dict() for quote in quotes}
        return jsonify(quotes_dict)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Erro ao buscar cotações em tempo real", "details": str(e)}), 500


# --- ROTAS DE ESCRITA (POST) ---

@portfolio_bp.route('/config', methods=['POST'])
def save_portfolio_config():
    """Salva a configuração completa da carteira, substituindo a antiga."""
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({"error": "O corpo da requisição deve ser uma lista de ativos"}), 400

    try:
        # Estratégia de Sincronização: Apaga tudo e insere o novo. Simples e eficaz.
        PortfolioConfig.query.delete()
        
        new_assets = []
        for asset_data in data:
            # Ignora linhas vazias que o usuário possa ter adicionado
            if not asset_data.get('ticker'):
                continue
            
            new_asset = PortfolioConfig(
                ticker=asset_data['ticker'],
                quantity=int(asset_data['quantity']),
                target_weight=float(asset_data['targetWeight'])
            )
            new_assets.append(new_asset)
        
        db.session.bulk_save_objects(new_assets)
        db.session.commit()
        return jsonify({"message": f"Carteira salva com sucesso com {len(new_assets)} ativos."}), 201
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": "Erro ao salvar a configuração da carteira", "details": str(e)}), 500

@portfolio_bp.route('/metrics', methods=['POST'])
def update_portfolio_metrics():
    """Atualiza as métricas diárias."""
    metrics_data = request.get_json()
    if not isinstance(metrics_data, list):
        return jsonify({"error": "O corpo da requisição deve ser uma lista de métricas"}), 400

    try:
        for metric_item in metrics_data:
            metric_to_update = PortfolioMetric.query.filter_by(metric_name=metric_item['label']).first()
            if metric_to_update:
                metric_to_update.metric_value = float(metric_item['value'])
        
        db.session.commit()
        return jsonify({"message": "Métricas atualizadas com sucesso."}), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": "Erro ao atualizar as métricas", "details": str(e)}), 500