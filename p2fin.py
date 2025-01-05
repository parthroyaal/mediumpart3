from flask import Flask, jsonify, request
from flask_sock import Sock
import threading
import random
import time
import math
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
sock = Sock(app)

clients = []

def generate_synthetic_data(interval_seconds, limit, base_price=40000):
    """
    Generate synthetic OHLCV data with properly ordered timestamps
    """
    current_time = int(time.time())
    # Round down to the nearest interval
    current_time = current_time - (current_time % interval_seconds)
    data = []
    price = base_price
    
    # Generate data points from past to present
    start_time = current_time - (interval_seconds * limit)
    
    for i in range(limit):
        timestamp = start_time + (interval_seconds * i)
        
        # Create some volatility
        change_percent = random.uniform(-0.02, 0.02)
        price = price * (1 + change_percent)
        
        # Generate OHLCV data
        open_price = price
        high_price = price * (1 + random.uniform(0, 0.01))
        low_price = price * (1 - random.uniform(0, 0.01))
        close_price = price * (1 + random.uniform(-0.005, 0.005))
        
        # Add some sine wave variation
        sine_modifier = math.sin(i/10) * (price * 0.02)
        open_price += sine_modifier
        high_price += sine_modifier
        low_price += sine_modifier
        close_price += sine_modifier
        
        volume = random.uniform(10, 100)
        
        candle = {
            'time': timestamp,
            'open': round(open_price, 2),
            'high': round(max(open_price, high_price, close_price), 2),
            'low': round(min(open_price, low_price, close_price), 2),
            'close': round(close_price, 2),
            'volumefrom': round(volume, 2),
            'volumeto': round(volume * close_price, 2)
        }
        data.append(candle)
    
    return {
        'Response': 'Success',
        'Data': sorted(data, key=lambda x: x['time']),  # Ensure data is sorted by timestamp
        'TimeTo': current_time,
        'TimeFrom': start_time,
        'FirstValueInArray': True,
        'ConversionType': {
            'type': 'direct',
            'conversionSymbol': ''
        }
    }

@app.route('/data/histominute', methods=['GET'])
def hist_minute():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(60, limit))

@app.route('/data/histohour', methods=['GET'])
def hist_hour():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(3600, limit))

@app.route('/data/histoday', methods=['GET'])
def hist_day():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(86400, limit))

@sock.route('/realtime')
def realtime(sock):
    """Send real-time updates to clients with properly ordered timestamps."""
    clients.append(sock)
    last_time = int(time.time())
    
    while True:
        try:
            current_time = int(time.time())
            # Ensure new data point is after the last one
            if current_time > last_time:
                price = 40000 + random.uniform(-50, 50)
                data = {
                    'time': current_time,
                    'open': price,
                    'high': price + random.uniform(0, 5),
                    'low': price - random.uniform(0, 5),
                    'close': price,
                    'volumefrom': random.uniform(1, 100)
                }
                sock.send(json.dumps(data))
                last_time = current_time
            time.sleep(1)
        except Exception as e:
            print(f"Client disconnected: {e}")
            clients.remove(sock)
            break

if __name__ == '__main__':
    app.run(debug=True, port=5000)