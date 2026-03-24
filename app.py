import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
# Esto crea el archivo prode.db en la misma carpeta del proyecto
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mundial2026-clave-secreta'

db = SQLAlchemy(app)

# --- MODELOS (TABLAS DE BASE DE DATOS) ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(10), default='user') # 'admin' o 'user'
    points = db.Column(db.Integer, default=0)

class Match(db.Model):
    id = db.Column(db.String(20), primary_key=True) # Ej: 'GA1'
    home = db.Column(db.String(50))
    away = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    phase = db.Column(db.String(20))
    home_score = db.Column(db.Integer, nullable=True) # Resultado real
    away_score = db.Column(db.Integer, nullable=True) # Resultado real

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
    dorsal_pred = db.Column(db.Integer, nullable=True)

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        return jsonify({"id": user.id, "name": user.name, "role": user.role})
    return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

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
    
    # VALIDACIÓN: Bloqueo exacto a la hora del partido
    if datetime.now() >= match.date:
        return jsonify({"error": "Tiempo agotado. El partido ya comenzó."}), 403
    
    pred = Prediction.query.filter_by(user_id=data['user_id'], match_id=data['match_id']).first()
    if not pred:
        pred = Prediction(user_id=data['user_id'], match_id=data['match_id'])
    
    pred.home_pred = data['home_pred']
    pred.away_pred = data['away_pred']
    pred.dorsal_pred = data['dorsal_pred']
    
    db.session.add(pred)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/admin/resultados', methods=['POST'])
def carga_masiva():
    data = request.json
    for res in data['resultados']:
        match = Match.query.get(res['id'])
        if match:
            match.home_score = res['goles_a']
            match.away_score = res['goles_b']
    db.session.commit()
    return jsonify({"status": "Resultados oficiales actualizados"})

# --- INICIALIZACIÓN DE DATOS (PARA RENDER) ---

with app.app_context():
    db.create_all()
    
    # 1. Crear Admin Inicial
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123', name='Admin Prode', role='admin')
        db.session.add(admin)
    
    # 2. Crear Partidos de Prueba (puedes borrar esto cuando cargues los reales)
    if not Match.query.first():
        partidos_iniciales = [
            Match(id='GA1', home='Argentina', away='México', phase='Grupos', date=datetime(2026, 6, 20, 16, 0)),
            Match(id='GA2', home='España', away='Alemania', phase='Grupos', date=datetime(2026, 6, 21, 14, 0))
        ]
        db.session.add_all(partidos_iniciales)

    # 3. Algunos jugadores para probar el buscador de dorsal
    if not Player.query.first():
        jugadores = [
            Player(name='Lionel Messi', team='Argentina', dorsal=10),
            Player(name='Julián Álvarez', team='Argentina', dorsal=9),
            Player(name='Pedri', team='España', dorsal=8),
            Player(name='Lamine Yamal', team='España', dorsal=19)
        ]
        db.session.add_all(jugadores)
    
    db.session.commit()

# --- ARRANQUE DEL SERVIDOR ---

if __name__ == '__main__':
    # Render usa la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
