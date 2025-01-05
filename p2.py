from flask import Flask, jsonify, request
from flask_sock import Sock
import threading
import random
import time
import json
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
sock = Sock(app)

clients = []

@app.route('/data/histoday', methods=['GET'])
def histoday():
    """Return historical daily data."""
    data = [
        {'time': int(time.time()) - i * 86400, 'open': 40000, 'high': 40500, 'low': 39800, 'close': 40300, 'volumefrom': 10}
        for i in range(10)
    ]
    return jsonify({'Data': data})

@app.route('/data/histohour', methods=['GET'])
def histohour():
    """Return historical hourly data."""
    data = [
        {'time': int(time.time()) - i * 3600, 'open': 40000, 'high': 40500, 'low': 39800, 'close': 40300, 'volumefrom': 10}
        for i in range(24)
    ]
    return jsonify({'Data': data})

@app.route('/data/histominute', methods=['GET'])
def histominute():
    """Return historical minute data."""
    data = [
        {'time': int(time.time()) - i * 60, 'open': 40000, 'high': 40500, 'low': 39800, 'close': 40300, 'volumefrom': 10}
        for i in range(60)
    ]
    return jsonify({'Data': data})

@sock.route('/realtime')
def realtime(sock):
    """Send real-time updates to clients."""
    clients.append(sock)
    while True:
        try:
            price = 40000 + random.uniform(-50, 50)
            data = {
                'time': int(time.time()),
                'open': price,
                'high': price + random.uniform(0, 5),
                'low': price - random.uniform(0, 5),
                'close': price,
                'volumefrom': random.uniform(1, 100)
            }
            sock.send(json.dumps(data))
            time.sleep(1)
        except Exception as e:
            print(f"Client disconnected: {e}")
            clients.remove(sock)
            break

if __name__ == '__main__':
    app.run(debug=True, port=5000)
