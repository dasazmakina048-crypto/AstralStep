from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/game', methods=['PUT'])
def game():
    data = request.get_json()
    if 'values' not in data:
        return jsonify({'error': 'Invalid request'}), 400

@app.route('/cabinet', methods=['PUT'])
def cabinet():
    data = request.get_json()
    if 'values' not in data:
        return jsonify({'error': 'Invalid request'}), 400


@app.route('/log', methods=['POST'])
def log():
    return "hello world"


if __name__ == '__main__':
    app.run(host="0.0.0.0", threaded=True, port=5000, debug=True)
