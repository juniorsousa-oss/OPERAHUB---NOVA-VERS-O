import base64
import os
from io import BytesIO
from urllib.parse import urlparse

import requests
from PIL import Image, ImageChops, ImageDraw
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_file,
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "opera-hub-local-dev-key")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "").strip()

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://cuixazpxkvniqldmmnth.supabase.co",
).rstrip("/")
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "sb_publishable_ZTqIgmA9Ez6AVQsoXa0P8Q_6CYHDFye",
).strip()
SUPABASE_WRITE_TOKEN = os.getenv("SUPABASE_WRITE_TOKEN", "").strip()

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1776493929304-dfe4d50ae96b"
    "?auto=format&fit=crop&fm=jpg&q=82&w=2400"
)

DEFAULT_SETTINGS = {
    "id": "main",
    "logo_data": "",
    "favicon_data": "",
    "logo_width": 190,
}

DEFAULT_NAV_ITEMS = [
    {"key": "inicio", "label": "Início", "icon": "fa-solid fa-house", "url": "", "sort_order": 1, "new_tab": False},
    {"key": "mrp", "label": "MRP", "icon": "fa-regular fa-file-lines", "url": "", "sort_order": 2, "new_tab": True},
    {"key": "estoque", "label": "Estoque", "icon": "fa-solid fa-box-open", "url": "", "sort_order": 3, "new_tab": True},
    {"key": "inventario", "label": "Inventário", "icon": "fa-regular fa-clipboard", "url": "", "sort_order": 4, "new_tab": True},
    {"key": "fechamentos", "label": "Fechamentos", "icon": "fa-regular fa-calendar-check", "url": "", "sort_order": 5, "new_tab": True},
    {"key": "conferencias", "label": "Conferências", "icon": "fa-solid fa-shield-halved", "url": "", "sort_order": 6, "new_tab": True},
    {"key": "entregas", "label": "Entregas", "icon": "fa-solid fa-truck", "url": "", "sort_order": 7, "new_tab": True},
    {"key": "indicadores", "label": "Indicadores", "icon": "fa-solid fa-chart-column", "url": "", "sort_order": 8, "new_tab": True},
    {"key": "projetos", "label": "Projetos", "icon": "fa-solid fa-bullseye", "url": "", "sort_order": 9, "new_tab": True},
    {"key": "notificacoes", "label": "Notificações", "icon": "fa-regular fa-bell", "url": "", "sort_order": 10, "new_tab": True},
    {"key": "ajuda", "label": "Ajuda", "icon": "fa-regular fa-circle-question", "url": "", "sort_order": 11, "new_tab": True},
]

DEFAULT_APPLICATIONS = [
    {"key": "gestao-equipes", "name": "GESTÃO DE EQUIPES", "description": "Acompanhamento de indicadores e equipes.", "icon": "fa-solid fa-people-group", "accent": "gold", "status": "ONLINE", "url": "", "sort_order": 1, "new_tab": True},
    {"key": "conversor-mrp", "name": "CONVERSOR MRP", "description": "Conversor de relatórios para alimentação MRP.", "icon": "fa-solid fa-file-circle-check", "accent": "blue", "status": "ONLINE", "url": "", "sort_order": 2, "new_tab": True},
    {"key": "mrp", "name": "MRP", "description": "Demanda e necessidade de materiais.", "icon": "fa-solid fa-clipboard-list", "accent": "amber", "status": "ONLINE", "url": "", "sort_order": 3, "new_tab": True},
    {"key": "gestao-entregas", "name": "GESTÃO DE ENTREGAS", "description": "Controle de entrega de OPs e cronograma.", "icon": "fa-solid fa-truck-fast", "accent": "orange", "status": "ONLINE", "url": "", "sort_order": 4, "new_tab": True},
    {"key": "inventario-rotativo", "name": "INVENTÁRIO ROTATIVO", "description": "Acompanhamento e geração de inventários.", "icon": "fa-solid fa-boxes-stacked", "accent": "green", "status": "WORK", "url": "", "sort_order": 5, "new_tab": True},
    {"key": "smtc", "name": "SMTC", "description": "Acompanhamento, armazenamento e reposição de parafusos, porcas e arruelas.", "icon": "fa-solid fa-screwdriver-wrench", "accent": "steel", "status": "WORK", "url": "", "sort_order": 6, "new_tab": True},
    {"key": "gestao-nfs", "name": "GESTÃO DE NFS", "description": "Controle de realização e envio de NFs para lançamento.", "icon": "fa-solid fa-file-invoice-dollar", "accent": "violet", "status": "ONLINE", "url": "", "sort_order": 7, "new_tab": True},
    {"key": "fechamento-mensal", "name": "FECHAMENTO MENSAL", "description": "Auditoria de baixas, acompanhamento da evolução de estoque mês a mês.", "icon": "fa-solid fa-chart-simple", "accent": "peach", "status": "WORK", "url": "", "sort_order": 8, "new_tab": True},
    {"key": "monitor-apis", "name": "MONITOR DE APIs", "description": "Painel de verificação de status de conexão de APIs.", "icon": "fa-solid fa-network-wired", "accent": "sky", "status": "WORK", "url": "", "sort_order": 9, "new_tab": True},
]


def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def sb_get(table, params):
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=sb_headers(),
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def sb_rpc(name, payload):
    if not SUPABASE_WRITE_TOKEN:
        raise RuntimeError(
            "SUPABASE_WRITE_TOKEN não configurado no Render."
        )
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/{name}",
        headers=sb_headers(),
        json={"p_token": SUPABASE_WRITE_TOKEN, **payload},
        timeout=20,
    )
    response.raise_for_status()


def load_settings():
    try:
        rows = sb_get(
            "operahub_settings",
            {"id": "eq.main", "select": "id,logo_width,updated_at", "limit": "1"},
        )
        if rows:
            data = dict(DEFAULT_SETTINGS)
            data.update(rows[0])
            data["logo_width"] = max(
                100,
                min(320, int(data.get("logo_width") or 190)),
            )
            return data
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)


def load_asset_data(column):
    if column not in {"logo_data", "favicon_data"}:
        return ""
    try:
        rows = sb_get(
            "operahub_settings",
            {"id": "eq.main", "select": column, "limit": "1"},
        )
        if rows:
            return rows[0].get(column) or ""
    except Exception:
        pass
    return ""


def load_nav():
    try:
        rows = sb_get(
            "operahub_nav_items",
            {"select": "*", "order": "sort_order.asc"},
        )
        if rows:
            return rows
    except Exception:
        pass
    return [dict(item) for item in DEFAULT_NAV_ITEMS]


def load_apps():
    try:
        rows = sb_get(
            "operahub_applications",
            {"select": "*", "order": "sort_order.asc"},
        )
        if rows:
            return rows
    except Exception:
        pass
    return [dict(item) for item in DEFAULT_APPLICATIONS]


def safe_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    return ""


def file_to_data_uri(file_storage, max_bytes, max_dimension=2400):
    if not file_storage or not file_storage.filename:
        return None

    mime = (file_storage.mimetype or "").lower()
    allowed = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
    if mime not in allowed:
        raise ValueError("Formato de imagem não suportado.")

    raw = file_storage.read()
    if len(raw) > max_bytes:
        raise ValueError(
            f"Imagem acima de {max_bytes // (1024 * 1024)} MB."
        )

    # SVG permanece vetorial. Para imagens raster, reduzimos dimensões muito
    # grandes antes de gravar no Supabase, sem impor o antigo limite de 1 MB.
    if mime == "image/svg+xml":
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except Exception:
        raise ValueError("Não foi possível processar a imagem enviada.")

    if max(image.size) > max_dimension:
        image.thumbnail(
            (max_dimension, max_dimension),
            Image.Resampling.LANCZOS,
        )

    out = BytesIO()

    if mime == "image/jpeg":
        image = image.convert("RGB")
        image.save(
            out,
            format="JPEG",
            quality=92,
            optimize=True,
            progressive=True,
        )
        result_mime = "image/jpeg"
    elif mime == "image/webp":
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA")
        image.save(
            out,
            format="WEBP",
            quality=92,
            method=6,
        )
        result_mime = "image/webp"
    else:
        image = image.convert("RGBA")
        image.save(
            out,
            format="PNG",
            optimize=True,
        )
        result_mime = "image/png"

    encoded = base64.b64encode(out.getvalue()).decode("ascii")
    return f"data:{result_mime};base64,{encoded}"


def decode_data_uri(data_uri):
    if not data_uri or "," not in data_uri:
        return b""
    try:
        return base64.b64decode(data_uri.split(",", 1)[1])
    except Exception:
        return b""


def normalized_favicon_png(data_uri):
    raw = decode_data_uri(data_uri)
    if not raw:
        return None

    try:
        image = Image.open(BytesIO(raw)).convert("RGBA")
    except Exception:
        return None

    # Reduz imagens enormes antes do processamento.
    if max(image.size) > 1024:
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    white = Image.new("RGB", image.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, white).convert("L")

    # Descobre se há um fundo branco/creme ocupando as bordas.
    corners = [
        image.getpixel((0, 0)),
        image.getpixel((image.width - 1, 0)),
        image.getpixel((0, image.height - 1)),
        image.getpixel((image.width - 1, image.height - 1)),
    ]
    white_corners = sum(
        1 for r, g, b, a in corners
        if a > 200 and r > 242 and g > 242 and b > 242
    )

    if white_corners >= 3:
        # Remove apenas o fundo claro conectado visualmente às bordas,
        # preservando antialias e deixando o favicon realmente transparente.
        bg_alpha = diff.point(
            lambda p: 0 if p <= 10 else min(255, (p - 10) * 14)
        )
        alpha = ImageChops.multiply(alpha, bg_alpha)
        image.putalpha(alpha)

    # Recorta margens transparentes / quase vazias.
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda p: 255 if p > 14 else 0).getbbox()
    if bbox:
        image = image.crop(bbox)

    # Se o usuário enviou somente o símbolo horizontal, cria automaticamente
    # um bloco navy para ocupar melhor o slot 16x16/32x32 do navegador.
    ratio = image.width / max(1, image.height)
    if ratio > 1.35:
        tile = Image.new("RGBA", (256, 256), (15, 27, 45, 255))
        draw = ImageDraw.Draw(tile)
        # cantos transparentes dão aparência de ícone de app sem desperdiçar área
        radius = 48
        mask = Image.new("L", (256, 256), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, 255, 255),
            radius=radius,
            fill=255,
        )
        tile.putalpha(mask)

        image.thumbnail((222, 154), Image.Resampling.LANCZOS)
        x = (256 - image.width) // 2
        y = (256 - image.height) // 2
        tile.alpha_composite(image, (x, y))
        image = tile
    else:
        # Ícones já quadrados/circulares são ampliados até quase encostar
        # no limite, mantendo a proporção original.
        image.thumbnail((252, 252), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        x = (256 - image.width) // 2
        y = (256 - image.height) // 2
        canvas.alpha_composite(image, (x, y))
        image = canvas

    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out


def admin_enabled():
    return bool(app.config["ADMIN_PASSWORD"])


def admin_authorized():
    return (not admin_enabled()) or bool(session.get("admin_ok"))


@app.route("/")
def index():
    settings = load_settings()
    return render_template(
        "index.html",
        nav_items=load_nav(),
        applications=load_apps(),
        settings=settings,
        hero_image=HERO_IMAGE,
    )


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if not admin_authorized():
        return redirect(url_for("login", next=url_for("configuracoes")))

    nav_items = load_nav()
    applications = load_apps()
    settings = load_settings()

    if request.method == "POST":
        try:
            nav_payload = []
            for item in nav_items:
                key = item["key"]
                nav_payload.append(
                    {
                        "key": key,
                        "url": safe_url(
                            request.form.get(f"nav_url_{key}", "")
                        ),
                        "new_tab": request.form.get(
                            f"nav_new_tab_{key}"
                        ) == "on",
                    }
                )

            app_payload = []
            for item in applications:
                key = item["key"]
                app_payload.append(
                    {
                        "key": key,
                        "url": safe_url(
                            request.form.get(f"app_url_{key}", "")
                        ),
                        "new_tab": request.form.get(
                            f"app_new_tab_{key}"
                        ) == "on",
                    }
                )

            logo_file = request.files.get("logo_upload")
            favicon_file = request.files.get("favicon_upload")
            remove_logo = request.form.get("remove_logo") == "on"
            remove_favicon = request.form.get("remove_favicon") == "on"

            new_logo = file_to_data_uri(
                logo_file,
                10 * 1024 * 1024,
                max_dimension=2400,
            )
            new_favicon = file_to_data_uri(
                favicon_file,
                10 * 1024 * 1024,
                max_dimension=1024,
            )

            logo_width = max(
                100,
                min(
                    320,
                    int(
                        request.form.get(
                            "logo_width",
                            settings.get("logo_width", 190),
                        )
                    ),
                ),
            )

            identity_changed = (
                bool(new_logo)
                or bool(new_favicon)
                or remove_logo
                or remove_favicon
                or logo_width != int(settings.get("logo_width", 190))
            )

            if identity_changed:
                logo_data = (
                    ""
                    if remove_logo
                    else (new_logo or load_asset_data("logo_data"))
                )
                favicon_data = (
                    ""
                    if remove_favicon
                    else (new_favicon or load_asset_data("favicon_data"))
                )

                sb_rpc(
                    "operahub_save_settings",
                    {
                        "p_logo_data": logo_data,
                        "p_favicon_data": favicon_data,
                        "p_logo_width": logo_width,
                    },
                )

            sb_rpc("operahub_save_nav", {"p_items": nav_payload})
            sb_rpc("operahub_save_apps", {"p_items": app_payload})

            flash(
                "Alterações salvas permanentemente no Supabase.",
                "success",
            )
            return app.response_class(status=204)
        except Exception as exc:
            flash(f"Não foi possível salvar: {exc}", "error")

    return render_template(
        "config.html",
        nav_items=nav_items,
        applications=applications,
        settings=settings,
        admin_enabled=admin_enabled(),
        supabase_write_ready=bool(SUPABASE_WRITE_TOKEN),
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

    return render_template(
        "login.html",
        settings=load_settings(),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/brand-logo")
def brand_logo():
    data_uri = load_asset_data("logo_data")
    raw = decode_data_uri(data_uri)
    if not raw:
        return redirect(url_for("static", filename="favicon.svg"))

    mime = "image/png"
    if data_uri.startswith("data:image/jpeg"):
        mime = "image/jpeg"
    elif data_uri.startswith("data:image/webp"):
        mime = "image/webp"
    elif data_uri.startswith("data:image/svg+xml"):
        mime = "image/svg+xml"

    response = send_file(BytesIO(raw), mimetype=mime, max_age=3600)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@app.route("/favicon.png")
def favicon_png():
    favicon = normalized_favicon_png(load_asset_data("favicon_data"))
    if favicon is None:
        return redirect(url_for("static", filename="favicon.svg"))

    response = send_file(
        favicon,
        mimetype="image/png",
        max_age=0,
        download_name="favicon.png",
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/healthz")
def healthz():
    return {"status": "ok", "storage": "supabase"}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True,
    )
