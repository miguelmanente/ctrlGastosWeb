import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

# 1. Creamos la instancia de la aplicación Flask
app = Flask(__name__)

# Configuración básica de base de datos SQLite
DB_NAME = "gastos.db"

def init_db():
    """Crea la tabla de gastos si no existe aún."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT,
            fecha DATE DEFAULT CURRENT_DATE
        )
    ''')
    conn.commit()
    conn.close()

# Inicializamos la base de datos al arrancar
init_db()

# 2. Definimos las rutas (URLs) de tu aplicación
@app.route('/')
def index():
    """Página principal que muestra la lista de gastos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, monto, categoria, descripcion, fecha FROM gastos ORDER BY fecha DESC")
    gastos = cursor.fetchall()
    conn.close()
    
    # Renderiza la plantilla HTML o devuelve JSON
    # Si tienes una carpeta 'templates' con 'index.html', puedes usar: render_template('index.html', gastos=gastos)
    return jsonify(gastos)

@app.route('/agregar', methods=['POST'])
def agregar_gasto():
    """Ruta para guardar un nuevo gasto."""
    monto = request.form.get('monto') or request.json.get('monto')
    categoria = request.form.get('categoria') or request.json.get('categoria')
    descripcion = request.form.get('descripcion') or request.json.get('descripcion')

    if monto and categoria:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gastos (monto, categoria, descripcion) VALUES (?, ?, ?)",
            (monto, categoria, descripcion)
        )
        conn.commit()
        conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)