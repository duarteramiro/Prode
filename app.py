import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración robusta de la base de datos
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'prode.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave-secreta-prode'

db = SQLAlchemy(app)

# MODELOS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(10), default='user')

# RUTA PRINCIPAL
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# RUTA DE LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        user = User.query.filter_by(username=data['username'], password=data['password']).first()
        if user:
            return jsonify({"id": user.id, "name": user.name, "role": user.role})
        return jsonify({"error": "Usuario o clave incorrectos"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# INICIALIZACIÓN FORZADA (Esto arregla el error 'no such table')
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='123', name='Admin Prode', role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Base de datos y admin creados!")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
