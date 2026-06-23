from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import io
import csv

app = Flask(__name__)

# Configuración de base de datos para Render
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'quimica.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_quimica_segura_2024'

db = SQLAlchemy(app)

PASSWORD_PROFESOR = "quimica2024"

class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_acceso = db.Column(db.String(20), unique=True, nullable=False)
    respuestas = db.relationship('Respuesta', backref='alumno', lazy=True)

class Respuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    puntos = db.Column(db.Integer)
    tema = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumno.id'), nullable=False)

# --- FUNCIÓN PARA ASEGURAR QUE LAS TABLAS EXISTAN ---
def init_db():
    with app.app_context():
        db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    init_db() # Crea las tablas si no existen al entrar aquí
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD_PROFESOR:
            session['admin_logeado'] = True
            return redirect(url_for('profesor_panel'))
        return render_template('login.html', error="Contraseña incorrecta")
    return render_template('login.html')

@app.route('/profesor')
def profesor_panel():
    init_db() # Crea las tablas si no existen al entrar aquí
    if not session.get('admin_logeado'):
        return redirect(url_for('login'))
    alumnos = Alumno.query.all()
    for a in alumnos:
        a.total = sum(r.puntos for r in a.respuestas)
    recientes = Respuesta.query.order_by(Respuesta.fecha.desc()).limit(10).all()
    return render_template('profesor.html', alumnos=alumnos, recientes=recientes)

# ... (el resto de tus rutas: puntuar, exportar, etc. deben seguir igual) ...

@app.route('/logout')
def logout():
    session.pop('admin_logeado', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('profesor_panel'))

@app.route('/exportar')
def exportar():
    if not session.get('admin_logeado'): return redirect(url_for('login'))
    alumnos = Alumno.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nombre', 'ID Acceso', 'Puntos Totales'])
    for a in alumnos:
        total = sum(r.puntos for r in a.respuestas)
        writer.writerow([a.nombre, a.id_acceso, total])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=notas_quimica.csv"})

@app.route('/add_alumno', methods=['POST'])
def add_alumno():
    if not session.get('admin_logeado'): return redirect(url_for('login'))
    nombre = request.form.get('nombre')
    id_acceso = request.form.get('id_acceso')
    if nombre and id_acceso:
        db.session.add(Alumno(nombre=nombre, id_acceso=id_acceso))
        db.session.commit()
    return redirect(url_for('profesor_panel'))

@app.route('/puntuar', methods=['POST'])
def puntuar():
    if not session.get('admin_logeado'): return redirect(url_for('login'))
    alumno_id = request.form.get('alumno_id')
    puntos = request.form.get('puntos')
    tema = request.form.get('tema')
    if alumno_id and puntos:
        db.session.add(Respuesta(puntos=int(puntos), tema=tema, alumno_id=int(alumno_id)))
        db.session.commit()
    return redirect(url_for('profesor_panel'))

@app.route('/eliminar_respuesta/<int:id>')
def eliminar_respuesta(id):
    if not session.get('admin_logeado'): return redirect(url_for('login'))
    res = Respuesta.query.get_or_404(id)
    db.session.delete(res)
    db.session.commit()
    return redirect(url_for('profesor_panel'))

@app.route('/alumno/<id_acceso>')
def alumno_panel(id_acceso):
    init_db()
    alumno = Alumno.query.filter_by(id_acceso=id_acceso).first_or_404()
    total_puntos = sum(r.puntos for r in alumno.respuestas)
    return render_template('alumno.html', alumno=alumno, total=total_puntos)

if __name__ == '__main__':
    app.run(debug=True)
