from flask import Flask, jsonify, request

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    conn.close()

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL)')
    conn.close()


tasks = [
    {'id': 1, 'title': '', 'done': False},
    {'id': 2, 'title': '', 'done': True}
]


@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = next((task for task in tasks if task['id'] == task_id), None)
    if task is None:
        return jsonify({'error': 'Задача не найдена'}), 404
    return jsonify({'task': task})

@app.route('/divide', methods=['POST'])
def sumWithPostBody():
    reqJson = request.get_json()
    x = reqJson['x']
    y = reqJson['y']
    try:
        result = x/y
        return {"message": f"{x} divided by {y} is {result}"}
    except Exception as err:
        return {"error": str(err)}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50100, debug=True)
