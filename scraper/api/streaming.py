from flask import Blueprint, request
from flask_socketio import emit, join_room, leave_room, disconnect
from utils.auth import validate_api_key
from services.data_fetcher import data_fetcher
from app import socketio, redis_client
import json
import asyncio
import threading
import time
from datetime import datetime

streaming_bp = Blueprint('streaming', __name__)

# Store active connections and their subscriptions
active_connections = {}
subscription_rooms = {}

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    print(f'Client {request.sid} connected')
    active_connections[request.sid] = {
        'connected_at': datetime.now(),
        'subscriptions': [],
        'authenticated': False
    }

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    print(f'Client {request.sid} disconnected')
    
    # Clean up subscriptions
    if request.sid in active_connections:
        for subscription in active_connections[request.sid]['subscriptions']:
            leave_room(subscription['room'])
        del active_connections[request.sid]

@socketio.on('authenticate')
def on_authenticate(data):
    """Authenticate WebSocket connection"""
    api_key = data.get('api_key') or data.get('token')
    
    if not api_key:
        emit('error', {'message': 'API key required for authentication'})
        disconnect()
        return
    
    api_key_obj, error = validate_api_key(api_key)
    if error:
        emit('error', {'message': f'Authentication failed: {error}'})
        disconnect()
        return
    
    # Update connection info
    if request.sid in active_connections:
        active_connections[request.sid]['authenticated'] = True
        active_connections[request.sid]['api_key_obj'] = api_key_obj
        
        emit('authenticated', {
            'message': 'Successfully authenticated',
            'plan': api_key_obj.plan,
            'rate_limit': api_key_obj.requests_per_hour
        })
    else:
        emit('error', {'message': 'Connection not found'})
        disconnect()

@socketio.on('subscribe_quotes')
def on_subscribe_quotes(data):
    """Subscribe to real-time quotes"""
    if request.sid not in active_connections or not active_connections[request.sid]['authenticated']:
        emit('error', {'message': 'Authentication required'})
        return
    
    tickers = data.get('tickers', [])
    if not tickers:
        emit('error', {'message': 'Tickers list is required'})
        return
    
    # Validate tickers
    from utils.validators import validate_ticker
    valid_tickers = []
    
    for ticker in tickers:
        valid, error = validate_ticker(ticker)
        if valid:
            valid_tickers.append(ticker.upper())
        else:
            emit('error', {'message': f'Invalid ticker {ticker}: {error}'})
            return
    
    # Join rooms for each ticker
    for ticker in valid_tickers:
        room_name = f'quotes_{ticker}'
        join_room(room_name)
        
        # Track subscription
        subscription = {
            'type': 'quotes',
            'ticker': ticker,
            'room': room_name,
            'subscribed_at': datetime.now()
        }
        
        active_connections[request.sid]['subscriptions'].append(subscription)
        
        # Add to subscription tracking
        if room_name not in subscription_rooms:
            subscription_rooms[room_name] = []
        subscription_rooms[room_name].append(request.sid)
    
    emit('subscribed', {
        'type': 'quotes',
        'tickers': valid_tickers,
        'message': f'Subscribed to {len(valid_tickers)} tickers'
    })
    
    # Send initial quote data
    for ticker in valid_tickers:
        quote_data = data_fetcher.fetch_quote(ticker)
        if quote_data:
            emit('quote_update', {
                'ticker': ticker,
                'data': quote_data,
                'timestamp': datetime.now().isoformat()
            })

@socketio.on('subscribe_orderbook')
def on_subscribe_orderbook(data):
    """Subscribe to order book updates"""
    if request.sid not in active_connections or not active_connections[request.sid]['authenticated']:
        emit('error', {'message': 'Authentication required'})
        return
    
    ticker = data.get('ticker')
    if not ticker:
        emit('error', {'message': 'Ticker is required'})
        return
    
    from utils.validators import validate_ticker
    valid, error = validate_ticker(ticker)
    if not valid:
        emit('error', {'message': f'Invalid ticker: {error}'})
        return
    
    ticker = ticker.upper()
    room_name = f'orderbook_{ticker}'
    join_room(room_name)
    
    # Track subscription
    subscription = {
        'type': 'orderbook',
        'ticker': ticker,
        'room': room_name,
        'subscribed_at': datetime.now()
    }
    
    active_connections[request.sid]['subscriptions'].append(subscription)
    
    emit('subscribed', {
        'type': 'orderbook',
        'ticker': ticker,
        'message': f'Subscribed to {ticker} order book'
    })
    
    # Send mock order book data (as external order book APIs are not available)
    emit('orderbook_update', {
        'ticker': ticker,
        'data': {
            'bids': [
                {'price': 28.43, 'size': 1000, 'orders': 5},
                {'price': 28.42, 'size': 2500, 'orders': 12},
                {'price': 28.41, 'size': 1800, 'orders': 8}
            ],
            'asks': [
                {'price': 28.47, 'size': 500, 'orders': 3},
                {'price': 28.48, 'size': 1200, 'orders': 7},
                {'price': 28.49, 'size': 900, 'orders': 4}
            ],
            'timestamp': datetime.now().isoformat()
        }
    })

@socketio.on('subscribe_trades')
def on_subscribe_trades(data):
    """Subscribe to trade updates"""
    if request.sid not in active_connections or not active_connections[request.sid]['authenticated']:
        emit('error', {'message': 'Authentication required'})
        return
    
    ticker = data.get('ticker')
    if not ticker:
        emit('error', {'message': 'Ticker is required'})
        return
    
    from utils.validators import validate_ticker
    valid, error = validate_ticker(ticker)
    if not valid:
        emit('error', {'message': f'Invalid ticker: {error}'})
        return
    
    ticker = ticker.upper()
    room_name = f'trades_{ticker}'
    join_room(room_name)
    
    # Track subscription
    subscription = {
        'type': 'trades',
        'ticker': ticker,
        'room': room_name,
        'subscribed_at': datetime.now()
    }
    
    active_connections[request.sid]['subscriptions'].append(subscription)
    
    emit('subscribed', {
        'type': 'trades',
        'ticker': ticker,
        'message': f'Subscribed to {ticker} trades'
    })

@socketio.on('unsubscribe')
def on_unsubscribe(data):
    """Unsubscribe from updates"""
    if request.sid not in active_connections:
        emit('error', {'message': 'Connection not found'})
        return
    
    subscription_type = data.get('type')
    ticker = data.get('ticker')
    
    if not subscription_type:
        emit('error', {'message': 'Subscription type is required'})
        return
    
    # Find and remove subscription
    subscriptions = active_connections[request.sid]['subscriptions']
    removed_subscriptions = []
    
    for i, subscription in enumerate(subscriptions):
        if subscription['type'] == subscription_type:
            if not ticker or subscription['ticker'] == ticker.upper():
                leave_room(subscription['room'])
                removed_subscriptions.append(subscriptions.pop(i))
    
    if removed_subscriptions:
        emit('unsubscribed', {
            'type': subscription_type,
            'ticker': ticker,
            'count': len(removed_subscriptions),
            'message': f'Unsubscribed from {len(removed_subscriptions)} subscriptions'
        })
    else:
        emit('error', {'message': 'No matching subscriptions found'})

@socketio.on('get_connection_info')
def on_get_connection_info():
    """Get connection information"""
    if request.sid not in active_connections:
        emit('error', {'message': 'Connection not found'})
        return
    
    connection_info = active_connections[request.sid].copy()
    
    # Remove sensitive data
    if 'api_key_obj' in connection_info:
        del connection_info['api_key_obj']
    
    # Convert datetime to string
    connection_info['connected_at'] = connection_info['connected_at'].isoformat()
    
    for subscription in connection_info['subscriptions']:
        subscription['subscribed_at'] = subscription['subscribed_at'].isoformat()
    
    emit('connection_info', connection_info)

# Background task to simulate real-time data updates
def background_data_updater():
    """Background task to push real-time data updates"""
    while True:
        try:
            # Update quotes for all subscribed tickers
            for room_name, connection_ids in subscription_rooms.items():
                if room_name.startswith('quotes_') and connection_ids:
                    ticker = room_name.replace('quotes_', '')
                    
                    # Fetch fresh quote data
                    quote_data = data_fetcher.fetch_quote(ticker)
                    
                    if quote_data:
                        socketio.emit('quote_update', {
                            'ticker': ticker,
                            'data': quote_data,
                            'timestamp': datetime.now().isoformat()
                        }, room=room_name)
            
            # Wait before next update
            time.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            print(f"Error in background data updater: {e}")
            time.sleep(10)  # Wait longer on error

# Start background updater thread
def start_background_updater():
    """Start the background data updater thread"""
    updater_thread = threading.Thread(target=background_data_updater, daemon=True)
    updater_thread.start()

# REST endpoint for WebSocket connection info
@streaming_bp.route('/stream/info', methods=['GET'])
def get_streaming_info():
    """Get streaming API information"""
    return {
        'websocket_url': '/socket.io',
        'supported_events': {
            'client_to_server': [
                'authenticate',
                'subscribe_quotes',
                'subscribe_orderbook', 
                'subscribe_trades',
                'unsubscribe',
                'get_connection_info'
            ],
            'server_to_client': [
                'authenticated',
                'subscribed',
                'unsubscribed',
                'quote_update',
                'orderbook_update',
                'trade_update',
                'connection_info',
                'error'
            ]
        },
        'authentication': {
            'method': 'API key via authenticate event',
            'format': '{"api_key": "your_api_key_here"}'
        },
        'rate_limits': {
            'max_connections': 50,
            'max_subscriptions_per_connection': 100
        },
        'active_connections': len(active_connections),
        'active_subscriptions': sum(len(conn['subscriptions']) for conn in active_connections.values())
    }

# Initialize background updater when module is imported
start_background_updater()
