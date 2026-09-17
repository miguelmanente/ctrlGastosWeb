from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import shutil
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta"

def conectar():
    conn = sqlite3.connect("gastos.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

@app.route("/")
def index():
    mes = request.args.get("mes")
    anio = request.args.get("anio")

    if not mes:
        from datetime import datetime
        hoy = datetime.now()
        mes = hoy.strftime("%m")
        anio = hoy.strftime("%Y")

    conn = conectar()
    cursor = conn.cursor()

    # INGRESOS DEL MES (lista)
    cursor.execute("""
        SELECT id, fecha, descripcion, monto
        FROM ingresos
        WHERE strftime('%m', fecha) = ?
        AND strftime('%Y', fecha) = ?
        ORDER BY fecha DESC
    """, (mes, anio))

    ingresos = cursor.fetchall()

    # INGRESOS
    cursor.execute("""
        SELECT SUM(monto) FROM ingresos
        WHERE strftime('%m', fecha) = ?
        AND strftime('%Y', fecha) = ?
    """, (mes, anio))
    total_ingresos = cursor.fetchone()[0] or 0

    # GASTOS
    cursor.execute("""
        SELECT SUM(monto) FROM gastos
        WHERE strftime('%m', fecha) = ?
        AND strftime('%Y', fecha) = ?
    """, (mes, anio))
    total_gastos = cursor.fetchone()[0] or 0

    # LISTA GASTOS
    cursor.execute("""
        SELECT id, fecha, descripcion, categoria, monto
        FROM gastos
        WHERE strftime('%m', fecha) = ?
        AND strftime('%Y', fecha) = ?
        ORDER BY fecha DESC
    """, (mes, anio))
    gastos = cursor.fetchall()

    # Categorías
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

    cursor.execute("""
        INSERT INTO gastos (fecha, descripcion, categoria, monto)
        VALUES (?, ?, ?, ?)
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

    cursor.execute("""
        INSERT INTO ingresos (fecha, descripcion, monto)
        VALUES (?, ?, ?)
    """, (fecha, descripcion, monto))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/editar_ingreso/<int:id>", methods=["GET", "POST"])
def editar_ingreso(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        fecha = request.form["fecha"]
        descripcion = request.form["descripcion"]
        monto = request.form["monto"]

        cursor.execute("""
            UPDATE ingresos
            SET fecha=?, descripcion=?, monto=?
            WHERE id=?
        """, (fecha, descripcion, monto, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT fecha, descripcion, monto FROM ingresos WHERE id=?", (id,))
    ingreso = cursor.fetchone()

    conn.close()

    return render_template("editar_ingreso.html", ingreso=ingreso, id=id)

@app.route("/editar_gasto/<int:id>", methods=["GET", "POST"])
def editar_gasto(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        fecha = request.form["fecha"]
        descripcion = request.form["descripcion"]
        categoria = request.form["categoria"]
        monto = request.form["monto"]

        cursor.execute("""
            UPDATE gastos
            SET fecha=?, descripcion=?, categoria=?, monto=?
            WHERE id=?
        """, (fecha, descripcion, categoria, monto, id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT fecha, descripcion, categoria, monto FROM gastos WHERE id=?", (id,))
    gasto = cursor.fetchone()

    cursor.execute("SELECT nombre FROM categorias")
    categorias = cursor.fetchall()

    conn.close()

    return render_template("editar_gasto.html", gasto=gasto, categorias=categorias, id=id)

@app.route("/eliminar_ingreso/<int:id>")
def eliminar_ingreso(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ingresos WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/agregar_categoria", methods=["POST"])
def agregar_categoria():
    nombre = request.form["nombre"]

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM gastos WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/cambiar_mes", methods=["POST"])
def cambiar_mes():
    mes = request.form.get("mes")
    anio = request.form.get("anio")

    # Backup (esto sí está perfecto)
    archivo = hacer_backup()

    # Redirigir pasando mes y año por URL
    return redirect(url_for("index", mes=mes, anio=anio))

def hacer_backup():
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    carpeta = "backups"
    os.makedirs(carpeta, exist_ok=True)

    origen = "gastos.db"
    destino = f"{carpeta}/gastos_{fecha}.db"

    shutil.copy2(origen, destino)

    return destino


if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)