from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from config import db, GameSession, Player
from flask_sqlalchemy import SQLAlchemy
import uuid
import random
import json
from models import User, generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import cards

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SECRET_KEY'] = 'your-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        user = User.query.get(int(user_id))
        return user
    except Exception:
        return None

db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()


def create_deck():
    return [{'suit': s, 'rank': r} for s in cards.suit for r in cards.rank]


@app.route('/game/<game_id>', methods=['PUT'])
def game(game_id):
    game = GameSession.query.get(game_id)
    if not game:
        return "Игра не найдена", 404
    return render_template('base.html', game_id=game_id)

@socketio.on('create_game')
def create_game(data):
    game_id = str(uuid.uuid4())
    deck = create_deck()
    random.shuffle(deck)

    game = GameSession(
        id=game_id,
        deck=json.dumps(deck),
        trump_suit=None,
        status='waiting'
    )
    db.session.add(game)
    db.session.commit()

    emit('game_created', {'game_id': game_id})


@socketio.on('join_game')
def join_game(data):
    game_id = data['game_id']
    player_id = request.sid
    player_name = data.get('name', 'Игрок')

    game = GameSession.query.get(game_id)
    if not game:
        emit('error', {'message': 'Игра не найдена'})
        return

    # Проверяем, есть ли игрок в игре
    player = Player.query.get(player_id)
    if not player:
        player = Player(
            id=player_id,
            game_id=game_id,
            name=player_name,
            hand=json.dumps([])
        )
        db.session.add(player)
    else:
        player.game_id = game_id  # Обновляем при переподключении

    game.status = 'in_progress'
    db.session.commit()

    emit('player_joined', player.to_dict(), room=game_id)
    join_room(game_id)

@socketio.on('deal_cards')
def deal_cards(data):
    game_id = data['game_id']
    game = GameSession.query.get(game_id)
    if not game or game.status != 'in_progress':
        emit('error', {'message': 'Нельзя раздать карты'})
        return

    deck = json.loads(game.deck)

    # Раздаём по 6 карт
    players = Player.query.filter_by(game_id=game_id).all()
    for player in players:
        hand = deck[:6]
        deck = deck[6:]
        player.hand = json.dumps(hand)

    game.deck = json.dumps(deck)
    game.current_turn = players[0].id  # Первый ход
    db.session.commit()

    for player in players:
        emit('your_cards', {'cards': json.loads(player.hand)}, room=player.id)


@socketio.on('play_card')
def play_card(data):
    game_id = data['game_id']
    player_id = request.sid
    card = data['card']

    game = GameSession.query.get(game_id)
    player = Player.query.get(player_id)

    if not game or not player or game.current_turn != player_id:
        emit('error', {'message': 'Не ваш ход!'})
        return

    # Удаляем карту из руки игрока
    hand = json.loads(player.hand)
    if card in hand:
        hand.remove(card)
        player.hand = json.dumps(hand)

        table = json.loads(game.table or '[]')
        table.append(card)
        game.table = json.dumps(table)
        db.session.commit()

        emit('card_played', {
            'player_id': player_id,
            'card': card,
            'next_turn': game.current_turn
        }, room=game_id)
    else:
        emit('error', {'message': 'У вас нет карт'})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key'

@app.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    zodiac = data.get('zodiac')

    if not all([username, password, zodiac]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({"success": False, "message": f'Логин "{username}" уже занят.'}), 409  # 409 Conflict

    password_hash = generate_password_hash(password)

    new_user = User(
        username=username,
        password=password_hash,
        zodiac=zodiac
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {"success": True, "message": "User registered successfully", "user_id": new_user.id}), 201  # 201 Created


@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"success": False, "message": "Missing JSON in request"}), 400

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        login_user(user)

        return jsonify({
            "success": True,
            "message": "Login successful",
            "username": user.username,
            "zodiac": user.zodiac
        }), 200

    return jsonify({"success": False, "message": "Invalid username or password"}), 401  # 401 Unauthorized


@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return jsonify({
        "success": True,
        "username": current_user.username,
        "zodiac": current_user.zodiac,
        "is_authenticated": current_user.is_authenticated
    }), 200


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Successfully logged out"}), 200


from flask import Flask, render_template, request, jsonify, session
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)

with app.app_context():
    db.create_all()

SKINS = ['skin1', 'skin2', 'skin3']


@app.route('/dashboard')
def dashboard():
    user_id = 1
    user = User.query.get(user_id)

    if not user:
        return "Пользователь не найден", 404

    return render_template(
        'dashboard.html',
        user=user,
        available_skins=SKINS
    )


@app.route('/change_skin', methods=['POST'])
def change_skin():
    skin = request.json.get('skin')
    user_id = 1

    user = User.query.get(user_id)
    if skin in SKINS and user:
        user.skin = skin
        db.session.commit()
        return jsonify({'success': True, 'skin': skin})

    return jsonify({'success': False, 'error': 'Неверный скин'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
