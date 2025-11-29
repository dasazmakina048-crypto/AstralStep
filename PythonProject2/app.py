from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from config import db, GameSession, Player
import uuid
import random
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()

# Колода карт
SUITS = ['мечи', 'кубки', 'жезлы', 'пенкакли']
RANKS = ['2','3','4','5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']


def create_deck():
    return [{'suit': s, 'rank': r} for s in SUITS for r in RANKS]


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

@app.route('/', methods=['POST'])
def log():
    return "hello world"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
