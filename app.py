import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración de Base de Datos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mundial2026-secret'

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(10), default='user') # 'admin' o 'user'
    points = db.Column(db.Integer, default=0)

class Match(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    home = db.Column(db.String(50))
    away = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    phase = db.Column(db.String(20))
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(50))
    dorsal = db.Column(db.Integer)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    match_id = db.Column(db.String(20), db.ForeignKey('match.id'))
    home_pred = db.Column(db.Integer)
    away_pred = db.Column(db.Integer)
    dorsal_pred = db.Column(db.Integer)

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        return jsonify({"id": user.id, "name": user.name, "role": user.role})
    return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/api/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    return jsonify([{
        "id": m.id, "home": m.home, "away": m.away, 
        "date": m.date.isoformat(), "phase": m.phase,
        "home_score": m.home_score, "away_score": m.away_score
    } for m in matches])

@app.route('/api/player/<int:dorsal>', methods=['GET'])
def get_player(dorsal):
    player = Player.query.filter_by(dorsal=dorsal).first()
    if player:
        return jsonify({"name": player.name, "team": player.team})
    return jsonify({"error": "No encontrado"}), 404

@app.route('/api/predict', methods=['POST'])
def save_prediction():
    data = request.json
    match = Match.query.get(data['match_id'])
    
    # REGLA: Bloqueo a la hora del partido
    if datetime.now() >= match.date:
        return jsonify({"error": "El partido ya comenzó"}), 403
    
    pred = Prediction.query.filter_by(user_id=data['user_id'], match_id=data['match_id']).first()
    if not pred:
        pred = Prediction(user_id=data['user_id'], match_id=data['match_id'])
    
    pred.home_pred = data['home_pred']
    pred.away_pred = data['away_pred']
    pred.dorsal_pred = data['dorsal_pred']
    
    db.session.add(pred)
    db.session.commit()
    return jsonify({"success": True})

# Iniciar base de datos con datos de prueba
def seed():
    if not Match.query.first():
        m1 = Match(id='GA1', home='Argentina', away='México', phase='Grupos', date=datetime(2026, 6, 20, 16, 0))
        p1 = Player(name='Lionel Messi', team='Argentina', dorsal=10)
        u1 = User(username='admin', password='123', name='Admin', role='admin')
        db.session.add_all([m1, p1, u1])
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
