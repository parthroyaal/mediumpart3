from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import random
import math

app = Flask(__name__)
CORS(app)

def generate_synthetic_data(interval_seconds, limit, base_price=40000):
    """
    Generate synthetic OHLCV data
    interval_seconds: time between each candle in seconds
    limit: number of candles to generate
    base_price: starting price point
    """
    current_time = int(time.time())
    data = []
    price = base_price
    
    # Generate random walk data
    for i in range(limit):
        timestamp = current_time - (interval_seconds * (limit - i))
        
        # Create some volatility
        change_percent = random.uniform(-0.02, 0.02)
        price = price * (1 + change_percent)
        
        # Generate OHLCV data
        open_price = price
        high_price = price * (1 + random.uniform(0, 0.01))
        low_price = price * (1 - random.uniform(0, 0.01))
        close_price = price * (1 + random.uniform(-0.005, 0.005))
        
        # Add some sine wave variation for more natural looking price movement
        sine_modifier = math.sin(i/10) * (price * 0.02)
        open_price += sine_modifier
        high_price += sine_modifier
        low_price += sine_modifier
        close_price += sine_modifier
        
        # Generate volume
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
        'Data': data,
        'TimeTo': current_time,
        'TimeFrom': current_time - (interval_seconds * limit),
        'FirstValueInArray': True,
        'ConversionType': {
            'type': 'direct',
            'conversionSymbol': ''
        }
    }

@app.route('/data/histominute', methods=['GET'])
def hist_minute():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(60, limit))  # 60 seconds interval

@app.route('/data/histohour', methods=['GET'])
def hist_hour():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(3600, limit))  # 3600 seconds (1 hour) interval

@app.route('/data/histoday', methods=['GET'])
def hist_day():
    limit = int(request.args.get('limit', 2000))
    return jsonify(generate_synthetic_data(86400, limit))  # 86400 seconds (1 day) interval

if __name__ == '__main__':
    app.run(debug=True, port=5000)