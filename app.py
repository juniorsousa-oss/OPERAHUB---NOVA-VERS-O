import os
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "operahub.db"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "opera-hub-local-dev-key")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "").strip()

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1776493929304-dfe4d50ae96b"
    "?auto=format&fit=crop&fm=jpg&q=82&w=2400"
)

DEFAULT_NAV_ITEMS = [
    ("inicio", "Início", "fa-solid fa-house", "", 1, 0),
    ("mrp", "MRP", "fa-regular fa-file-lines", "", 2, 1),
    ("estoque", "Estoque", "fa-solid fa-box-open", "", 3, 1),
    ("inventario", "Inventário", "fa-regular fa-clipboard", "", 4, 1),
    ("fechamentos", "Fechamentos", "fa-regular fa-calendar-check", "", 5, 1),
    ("conferencias", "Conferências", "fa-solid fa-shield-halved", "", 6, 1),
    ("entregas", "Entregas", "fa-solid fa-truck", "", 7, 1),
    ("indicadores", "Indicadores", "fa-solid fa-chart-column", "", 8, 1),
    ("projetos", "Projetos", "fa-solid fa-bullseye", "", 9, 1),
    ("notificacoes", "Notificações", "fa-regular fa-bell", "", 10, 1),
    ("ajuda", "Ajuda", "fa-regular fa-circle-question", "", 11, 1),
]

DEFAULT_APPLICATIONS = [
    ("gestao-equipes", "GESTÃO DE EQUIPES", "Acompanhamento de indicadores e equipes.", "fa-solid fa-people-group", "gold", "ONLINE", "", 1),
    ("conversor-mrp", "CONVERSOR MRP", "Conversor de relatórios para alimentação MRP.", "fa-solid fa-file-circle-check", "blue", "ONLINE", "", 2),
    ("mrp", "MRP", "Demanda e necessidade de materiais.", "fa-solid fa-clipboard-list", "amber", "ONLINE", "", 3),
    ("gestao-entregas", "GESTÃO DE ENTREGAS", "Controle de entrega de OPs e cronograma.", "fa-solid fa-truck-fast", "orange", "ONLINE", "", 4),
    ("inventario-rotativo", "INVENTÁRIO ROTATIVO", "Acompanhamento e geração de inventários.", "fa-solid fa-boxes-stacked", "green", "WORK", "", 5),
    ("smtc", "SMTC", "Acompanhamento, armazenamento e reposição de parafusos, porcas e arruelas.", "fa-solid fa-screwdriver-wrench", "steel", "WORK", "", 6),
    ("gestao-nfs", "GESTÃO DE NFS", "Controle de realização e envio de NFs para lançamento.", "fa-solid fa-file-invoice-dollar", "violet", "ONLINE", "", 7),
    ("fechamento-mensal", "FECHAMENTO MENSAL", "Auditoria de baixas, acompanhamento da evolução de estoque mês a mês.", "fa-solid fa-chart-simple", "peach", "WORK", "", 8),
    ("monitor-apis", "MONITOR DE APIs", "Painel de verificação de status de conexão de APIs.", "fa-solid fa-network-wired", "sky", "WORK", "", 9),
]


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(db_connect()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS nav_items (
                key TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                icon TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL,
                new_tab INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS applications (
                key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                accent TEXT NOT NULL,
                status TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL,
                new_tab INTEGER NOT NULL DEFAULT 1
            );
            """
        )

        count = conn.execute("SELECT COUNT(*) AS c FROM nav_items").fetchone()["c"]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO nav_items
                (key, label, icon, url, sort_order, new_tab)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                DEFAULT_NAV_ITEMS,
            )

        count = conn.execute("SELECT COUNT(*) AS c FROM applications").fetchone()["c"]
        if count == 0:
            conn.executemany(
                """
                INSERT INTO applications
                (key, name, description, icon, accent, status, url, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                DEFAULT_APPLICATIONS,
            )
        conn.commit()


def safe_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    return ""


def load_nav():
    with closing(db_connect()) as conn:
        return conn.execute(
            "SELECT * FROM nav_items ORDER BY sort_order, label"
        ).fetchall()


def load_apps():
    with closing(db_connect()) as conn:
        return conn.execute(
            "SELECT * FROM applications ORDER BY sort_order, name"
        ).fetchall()


def admin_enabled():
    return bool(app.config["ADMIN_PASSWORD"])


def admin_authorized():
    return (not admin_enabled()) or bool(session.get("admin_ok"))


@app.route("/")
def index():
    return render_template(
        "index.html",
        nav_items=load_nav(),
        applications=load_apps(),
        hero_image=HERO_IMAGE,
    )


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if not admin_authorized():
        return redirect(url_for("login", next=url_for("configuracoes")))

    nav_items = load_nav()
    applications = load_apps()

    if request.method == "POST":
        with closing(db_connect()) as conn:
            for item in nav_items:
                key = item["key"]
                url = safe_url(request.form.get(f"nav_url_{key}", ""))
                new_tab = 1 if request.form.get(f"nav_new_tab_{key}") == "on" else 0
                conn.execute(
                    "UPDATE nav_items SET url = ?, new_tab = ? WHERE key = ?",
                    (url, new_tab, key),
                )

            for item in applications:
                key = item["key"]
                url = safe_url(request.form.get(f"app_url_{key}", ""))
                new_tab = 1 if request.form.get(f"app_new_tab_{key}") == "on" else 0
                conn.execute(
                    "UPDATE applications SET url = ?, new_tab = ? WHERE key = ?",
                    (url, new_tab, key),
                )

            conn.commit()

        flash("Links atualizados com sucesso.", "success")
        return redirect(url_for("configuracoes"))

    return render_template(
        "config.html",
        nav_items=nav_items,
        applications=applications,
        admin_enabled=admin_enabled(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if not admin_enabled():
        return redirect(url_for("configuracoes"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == app.config["ADMIN_PASSWORD"]:
            session["admin_ok"] = True
            next_url = request.args.get("next") or url_for("configuracoes")
            return redirect(next_url)
        flash("Senha incorreta.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
