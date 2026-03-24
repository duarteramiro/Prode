import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración básica de base de datos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'prode-2026-key'

db = SQLAlchemy(app)

# --- MODELOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(10), default='user')

class Match(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    home = db.Column(db.String(50))
    away = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    phase = db.Column(db.String(20))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dorsal = db.Column(db.Integer)

# --- RUTAS ---
@app.route('/')
def index():
    # Esta línea busca el archivo dentro de la carpeta /templates
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        return jsonify({"id": user.id, "name": user.name, "role": user.role})
    return jsonify({"error": "No válido"}), 401

@app.route('/api/matches', methods=['GET'])
def get_matches():
    matches = Match.query.all()
    return jsonify([{"id": m.id, "home": m.home, "away": m.away, "date": m.date.isoformat(), "phase": m.phase} for m in matches])

@app.route('/api/player/<int:dorsal>', methods=['GET'])
def get_player(dorsal):
    p = Player.query.filter_by(dorsal=dorsal).first()
    return jsonify({"name": p.name}) if p else (jsonify({"error": "No hay"}), 404)

# --- INICIALIZACIÓN (Clave para Render) ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='123', name='Admin Prode', role='admin'))
    if not Match.query.first():
        db.session.add(Match(id='GA1', home='Argentina', away='México', phase='Grupos', date=datetime(2026, 6, 20, 16, 0)))
        db.session.add(Player(name='Lionel Messi', dorsal=10))
    db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
