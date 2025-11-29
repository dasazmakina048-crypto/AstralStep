from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class GameSession(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='waiting')
    deck = db.Column(db.Text)
    table = db.Column(db.Text)

    players = db.relationship('Player', backref='game', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'trump_suit': self.trump_suit,
            'current_turn': self.current_turn,
            'deck': json.loads(self.deck) if self.deck else [],
            'table': json.loads(self.table) if self.table else []
        }


class Player(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    game_id = db.Column(db.String(36), db.ForeignKey('game_session.id'), nullable=False)
    name = db.Column(db.String(50))
    hand = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hand': json.loads(self.hand) if self.hand else [],
            'is_active': self.is_active
        }
