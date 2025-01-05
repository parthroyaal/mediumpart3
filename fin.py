from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sock import Sock
import time
from datetime import datetime
import random
import json

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Store connected WebSocket clients
clients = []

def generate_base_minute_data(start_time, end_time):
    """Generate 1-minute base data"""
    data = []
    price = 40000
    
    current_time = start_time
    while current_time <= end_time:
        change_percent = random.uniform(-0.002, 0.002)
        price = price * (1 + change_percent)
        
        candle = {
            'time': current_time,
            'open': round(price * (1 + random.uniform(-0.001, 0.001)), 2),
            'high': round(price * (1 + random.uniform(0, 0.002)), 2),
            'low': round(price * (1 - random.uniform(0, 0.002)), 2),
            'close': round(price * (1 + random.uniform(-0.001, 0.001)), 2),
            'volumefrom': round(random.uniform(1, 10), 2)
        }
        candle['volumeto'] = candle['close'] * candle['volumefrom']
        data.append(candle)
        current_time += 60  # 1 minute increment
        
    return data

def aggregate_candles(minute_data, interval_minutes):
    """Aggregate 1-minute candles into larger timeframes"""
    if not minute_data:
        return []
    
    aggregated_data = []
    current_chunk = []
    
    for candle in minute_data:
        # Check if candle belongs to current chunk
        if not current_chunk or (candle['time'] - current_chunk[0]['time']) < interval_minutes * 60:
            current_chunk.append(candle)
        else:
            # Aggregate current chunk
            if current_chunk:
                aggregated_candle = {
                    'time': current_chunk[0]['time'],  # Use first candle's time
                    'open': current_chunk[0]['open'],  # First candle's open
                    'high': max(c['high'] for c in current_chunk),
                    'low': min(c['low'] for c in current_chunk),
                    'close': current_chunk[-1]['close'],  # Last candle's close
                    'volumefrom': sum(c['volumefrom'] for c in current_chunk),
                    'volumeto': sum(c['volumeto'] for c in current_chunk)
                }
                aggregated_data.append(aggregated_candle)
            current_chunk = [candle]
    
    # Don't forget the last chunk
    if current_chunk:
        aggregated_candle = {
            'time': current_chunk[0]['time'],
            'open': current_chunk[0]['open'],
            'high': max(c['high'] for c in current_chunk),
            'low': min(c['low'] for c in current_chunk),
            'close': current_chunk[-1]['close'],
            'volumefrom': sum(c['volumefrom'] for c in current_chunk),
            'volumeto': sum(c['volumeto'] for c in current_chunk)
        }
        aggregated_data.append(aggregated_candle)
    
    return aggregated_data

def get_data_for_resolution(resolution, to_ts=None, limit=2000):
    """Get data for any resolution using 1-minute data as base"""
    # Convert resolution to minutes
    if resolution.endswith('D'):
        interval_minutes = 1440  # Daily
    elif int(resolution) >= 60:
        interval_minutes = int(resolution)  # Hourly
    else:
        interval_minutes = int(resolution)  # Minutes
    
    # Calculate time range
    end_time = int(to_ts) if to_ts else int(time.time())  # Use current time if to_ts is not provided
    start_time = end_time - (interval_minutes * 60 * limit)
    
    # Get base 1-minute data
    minute_data = generate_base_minute_data(start_time, end_time)
    
    # If requesting 1-minute data, return as is
    if interval_minutes == 1:
        data = minute_data
    else:
        # Aggregate to requested timeframe
        data = aggregate_candles(minute_data, interval_minutes)
    
    # Ensure we only return the requested number of candles
    data = data[-limit:] if len(data) > limit else data
    
    return {
        'Response': 'Success',
        'Data': data,
        'TimeTo': end_time,
        'TimeFrom': start_time,
        'FirstValueInArray': True,
        'ConversionType': {
            'type': 'direct',
            'conversionSymbol': ''
        }
    }

# All endpoints now use the same data generation function
@app.route('/data/histominute', methods=['GET'])
@app.route('/data/histohour', methods=['GET'])
@app.route('/data/histoday', methods=['GET'])
def get_history():
    limit = int(request.args.get('limit', 2000))
    to_ts = request.args.get('toTs')
    
    # Determine resolution based on endpoint
    if request.path == '/data/histoday':
        resolution = '1D'
    elif request.path == '/data/histohour':
        resolution = '60'
    else:
        resolution = '1'
    
    print(f"\nRequest - Path: {request.path}, Resolution: {resolution}, ToTs: {datetime.fromtimestamp(int(to_ts)) if to_ts else 'current'}")
    return jsonify(get_data_for_resolution(resolution, to_ts, limit))

# WebSocket endpoint for real-time updates
@sock.route('/realtime')
def realtime(ws):
    """Send real-time updates to clients with properly ordered timestamps."""
    clients.append(ws)
    last_time = int(time.time())
    
    while True:
        try:
            current_time = int(time.time())
            # Ensure new data point is after the last one
            if current_time > last_time:
                price = 40000 + random.uniform(-50, 50)
                data = {
                    'time': current_time * 1000,  # Convert to milliseconds
                    'open': price,
                    'high': price + random.uniform(0, 5),
                    'low': price - random.uniform(0, 5),
                    'close': price,
                    'volumefrom': random.uniform(1, 100)
                }
                ws.send(json.dumps(data))
                last_time = current_time
            time.sleep(1)  # Send updates every second
        except Exception as e:
            print(f"Client disconnected: {e}")
            clients.remove(ws)
            break

if __name__ == '__main__':
    app.run(debug=True, port=5000)