from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import shutil
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Lee la URL de PostgreSQL configurada en Render
DATABASE_URL = os.environ.get("DATABASE_URL")

def conectar():
    if DATABASE_URL:
        import psycopg2
        # Render entrega 'postgres://', pero psycopg2 requiere 'postgresql://'
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn
    else:
        # Modo local en tu PC usando SQLite
        conn = sqlite3.connect("gastos.db", timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

def inicializar_db():
    """Crea automáticamente las tablas en PostgreSQL o SQLite si no existen."""
    conn = conectar()
    cursor = conn.cursor()
    
    is_postgres = DATABASE_URL is not None
    pk_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS gastos (
            id {pk_type},
            fecha DATE NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto NUMERIC(10, 2) NOT NULL
        );
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ingresos (
            id {pk_type},
            fecha DATE NOT NULL,
            descripcion TEXT NOT NULL,
            monto NUMERIC(10, 2) NOT NULL
        );
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS categorias (
            id {pk_type},
            nombre TEXT UNIQUE NOT NULL
        );
    """)

    conn.commit()
    conn.close()

# Inicializa la base de datos al arrancar la aplicación
inicializar_db()

@app.route("/")
def index():
    mes = request.args.get("mes")
    anio = request.args.get("anio")

    if not mes:
        hoy = datetime.now()
        mes = hoy.strftime("%m")
        anio = hoy.strftime("%Y")

    conn = conectar()
    cursor = conn.cursor()

    is_postgres = DATABASE_URL is not None

    # Adaptación de consultas según el motor de base de datos
    if is_postgres:
        filtro_fecha = "TO_CHAR(fecha, 'MM') = %s AND TO_CHAR(fecha, 'YYYY') = %s"
    else:
        filtro_fecha = "strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ?"

    # LISTA INGRESOS
    cursor.execute(f"""
        SELECT id, fecha, descripcion, monto
        FROM ingresos
        WHERE {filtro_fecha}
        ORDER BY fecha DESC
    """, (mes, anio))
    ingresos = cursor.fetchall()

    # TOTAL INGRESOS
    cursor.execute(f"""
        SELECT SUM(monto) FROM ingresos
        WHERE {filtro_fecha}
    """, (mes, anio))
    res_ing = cursor.fetchone()
    total_ingresos = res_ing[0] if res_ing and res_ing[0] is not None else 0

    # TOTAL GASTOS
    cursor.execute(f"""
        SELECT SUM(monto) FROM gastos
        WHERE {filtro_fecha}
    """, (mes, anio))
    res_gast = cursor.fetchone()
    total_gastos = res_gast[0] if res_gast and res_gast[0] is not None else 0

    # LISTA GASTOS
    cursor.execute(f"""
        SELECT id, fecha, descripcion, categoria, monto
        FROM gastos
        WHERE {filtro_fecha}
        ORDER BY fecha DESC
    """, (mes, anio))
    gastos = cursor.fetchall()

    # CATEGORÍAS
    cursor.execute("SELECT nombre FROM categorias ORDER BY nombre")
    categorias = [fila[0] for fila in cursor.fetchall()]

    conn.close()

    return render_template("index.html",
        gastos=gastos,
        ingresos=ingresos,
        categorias=categorias,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        mes=mes,
        anio=anio
    )

@app.route("/agregar", methods=["POST"])
def agregar():
    fecha = request.form["fecha"]
    descripcion = request.form["descripcion"]
    categoria = request.form["categoria"]
    monto = float(request.form["monto"])

    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    cursor.execute(f"""
        INSERT INTO gastos (fecha, descripcion, categoria, monto)
        VALUES ({param}, {param}, {param}, {param})
    """, (fecha, descripcion, categoria, monto))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/agregar_ingreso", methods=["POST"])
def agregar_ingreso():
    fecha = request.form["fecha"]
    descripcion = request.form["descripcion"]
    monto = float(request.form["monto"])

    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    cursor.execute(f"""
        INSERT INTO ingresos (fecha, descripcion, monto)
        VALUES ({param}, {param}, {param})
    """, (fecha, descripcion, monto))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/editar_ingreso/<int:id>", methods=["GET", "POST"])
def editar_ingreso(id):
    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    if request.method == "POST":
        fecha = request.form["fecha"]
        descripcion = request.form["descripcion"]
        monto = request.form["monto"]

        cursor.execute(f"""
            UPDATE ingresos
            SET fecha={param}, descripcion={param}, monto={param}
            WHERE id={param}
        """, (fecha, descripcion, monto, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute(f"SELECT fecha, descripcion, monto FROM ingresos WHERE id={param}", (id,))
    ingreso = cursor.fetchone()
    conn.close()

    return render_template("editar_ingreso.html", ingreso=ingreso, id=id)

@app.route("/editar_gasto/<int:id>", methods=["GET", "POST"])
def editar_gasto(id):
    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    if request.method == "POST":
        fecha = request.form["fecha"]
        descripcion = request.form["descripcion"]
        categoria = request.form["categoria"]
        monto = request.form["monto"]

        cursor.execute(f"""
            UPDATE gastos
            SET fecha={param}, descripcion={param}, categoria={param}, monto={param}
            WHERE id={param}
        """, (fecha, descripcion, categoria, monto, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute(f"SELECT fecha, descripcion, categoria, monto FROM gastos WHERE id={param}", (id,))
    gasto = cursor.fetchone()

    cursor.execute("SELECT nombre FROM categorias")
    categorias = cursor.fetchall()
    conn.close()

    return render_template("editar_gasto.html", gasto=gasto, categorias=categorias, id=id)

@app.route("/eliminar_ingreso/<int:id>")
def eliminar_ingreso(id):
    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    cursor.execute(f"DELETE FROM ingresos WHERE id = {param}", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/agregar_categoria", methods=["POST"])
def agregar_categoria():
    nombre = request.form["nombre"]

    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    cursor.execute(f"INSERT INTO categorias (nombre) VALUES ({param})", (nombre,))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = conectar()
    cursor = conn.cursor()
    param = "%s" if DATABASE_URL else "?"

    cursor.execute(f"DELETE FROM gastos WHERE id = {param}", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/cambiar_mes", methods=["POST"])
def cambiar_mes():
    mes = request.form.get("mes")
    anio = request.form.get("anio")

    hacer_backup()
    return redirect(url_for("index", mes=mes, anio=anio))

def hacer_backup():
    """Realiza una copia local solo si el archivo SQLite existe."""
    origen = "gastos.db"
    if os.path.exists(origen):
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        carpeta = "backups"
        os.makedirs(carpeta, exist_ok=True)
        destino = f"{carpeta}/gastos_{fecha}.db"
        shutil.copy2(origen, destino)

@app.route("/test_db")
def test_db():
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Probar si la conexión funciona
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()
        
        # Ver qué motor está usando
        engine = "PostgreSQL" if DATABASE_URL else "SQLite"
        
        # Ver si existen las tablas
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';" if DATABASE_URL else "SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        
        conn.close()
        return f"<h1>¡Conexión Exitosa!</h1><p>Motor: {engine}</p><p>Tablas encontradas: {tablas}</p>"
    except Exception as e:
        return f"<h1>Error de Conexión:</h1><p>{str(e)}</p>"

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)