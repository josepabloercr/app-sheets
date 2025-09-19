import os
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")
CREDS_PATH = os.getenv("GOOGLE_CREDENTIALS", "credentials.json")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")  # cambia en prod

# --- Google Sheets client ---
gc = gspread.service_account(filename=CREDS_PATH)
sh = gc.open_by_key(os.getenv("SHEET_ID"))
ws = sh.sheet1  # o sh.worksheet("tareas") si prefieres una con nombre

def row_to_task(row):
    """Convierte una fila [id, titulo, estado, creado] en dict seguro."""
    return {
        "id": row[0],
        "titulo": row[1] if len(row) > 1 else "",
        "estado": row[2] if len(row) > 2 else "pendiente",
        "creado": row[3] if len(row) > 3 else "",
    }

def get_tasks():
    vals = ws.get_all_values()
    if not vals:
        return []
    header, *data = vals
    tasks = []
    for r in data:
        if r and r[0]:
            tasks.append(row_to_task(r + [""] * (4 - len(r))))
    # opcional: ordenar por fecha (ultimo arriba)
    tasks.sort(key=lambda t: t["creado"], reverse=True)
    return tasks

def find_row_index_by_id(task_id):
    """Devuelve el índice (1-based) de la fila con ese id. None si no está."""
    col_ids = ws.col_values(1)  # primera columna: id
    for idx, val in enumerate(col_ids, start=1):
        if val == task_id:
            return idx
    return None

@app.route("/")
def index():
    tasks = get_tasks()
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add():
    titulo = request.form.get("titulo", "").strip()
    if not titulo:
        flash("El título no puede estar vacío.", "warning")
        return redirect(url_for("index"))
    # id simple basado en timestamp
    task_id = str(int(time.time() * 1000))
    creado = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([task_id, titulo, "pendiente", creado])
    flash("Tarea creada ✅", "success")
    return redirect(url_for("index"))

@app.route("/toggle/<task_id>", methods=["POST"])
def toggle(task_id):
    row_idx = find_row_index_by_id(task_id)
    if not row_idx:
        flash("No se encontró la tarea.", "danger")
        return redirect(url_for("index"))
    row = ws.row_values(row_idx)
    estado = row[2] if len(row) > 2 else "pendiente"
    nuevo = "hecha" if estado != "hecha" else "pendiente"
    ws.update_cell(row_idx, 3, nuevo)  # col 3 = estado
    flash("Estado actualizado 🔁", "info")
    return redirect(url_for("index"))

@app.route("/delete/<task_id>", methods=["POST"])
def delete(task_id):
    row_idx = find_row_index_by_id(task_id)
    if not row_idx:
        flash("No se encontró la tarea.", "danger")
        return redirect(url_for("index"))
    ws.delete_rows(row_idx)
    flash("Tarea eliminada 🗑️", "info")
    return redirect(url_for("index"))

# --- PWA assets ---
@app.route("/offline")
def offline():
    # Página simple mostrada si no hay conexión
    return "<h1>Estás offline</h1><p>Vuelve cuando tengas internet.</p>"

if __name__ == "__main__":
    app.run(debug=True)
