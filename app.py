import base64
import os
from io import BytesIO
from urllib.parse import urlparse

import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
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
    "https://images.unsplash.com/photo-1769701000453-e306362a7d03"
    "?auto=format&fit=crop&fm=jpg&q=82&w=2400"
)

DEFAULT_SETTINGS = {
    "id": "main",
    "logo_width": 190,
    "has_logo": False,
    "has_favicon": False,
    "has_hero": False,
    "hero_pos_x": 50,
    "hero_pos_y": 50,
    "hero_zoom": 100,
    "login_required": False,
    "updated_at": "",
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
    if not response.content:
        return None
    return response.json()


def sb_rpc_public(name, payload=None):
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/{name}",
        headers=sb_headers(),
        json=payload or {},
        timeout=20,
    )
    response.raise_for_status()
    if not response.content:
        return None
    return response.json()


def load_settings():
    try:
        rows = sb_get(
            "operahub_settings",
            {
                "id": "eq.main",
                "select": (
                    "id,logo_width,has_logo,has_favicon,"
                    "has_hero,hero_pos_x,hero_pos_y,hero_zoom,"
                    "login_required,updated_at"
                ),
                "limit": "1",
            },
        )
        if rows:
            data = dict(DEFAULT_SETTINGS)
            data.update(rows[0])
            data["logo_width"] = max(
                80,
                min(240, int(data.get("logo_width") or 190)),
            )
            data["hero_pos_x"] = max(
                0,
                min(100, int(data.get("hero_pos_x") or 50)),
            )
            data["hero_pos_y"] = max(
                0,
                min(100, int(data.get("hero_pos_y") or 50)),
            )
            data["hero_zoom"] = max(
                100,
                min(220, int(data.get("hero_zoom") or 100)),
            )
            return data
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)


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
            {
                "select": (
                    "key,name,description,icon,accent,status,url,"
                    "sort_order,new_tab,accent_color,has_image,image_zoom,updated_at"
                ),
                "order": "sort_order.asc",
            },
        )
        if rows:
            return rows
    except Exception:
        pass

    fallback_colors = {
        "gold": "#F4B400",
        "blue": "#4F7FE8",
        "amber": "#F2A11B",
        "orange": "#F58B38",
        "green": "#36B66F",
        "steel": "#6998CF",
        "violet": "#8B67E8",
        "peach": "#EF9A54",
        "sky": "#5F9FDB",
    }
    items = []
    for item in DEFAULT_APPLICATIONS:
        data = dict(item)
        data["accent_color"] = fallback_colors.get(
            data.get("accent"),
            "#F4B400",
        )
        data["has_image"] = False
        data["image_zoom"] = 142
        data["updated_at"] = ""
        items.append(data)
    return items


def safe_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    return ""


def safe_hex_color(value, fallback="#F4B400"):
    value = (value or "").strip()
    if (
        len(value) == 7
        and value.startswith("#")
        and all(ch in "0123456789abcdefABCDEF" for ch in value[1:])
    ):
        return value.upper()
    return fallback


def asset_data(table, column, key_column, key_value):
    try:
        rows = sb_get(
            table,
            {
                key_column: f"eq.{key_value}",
                "select": column,
                "limit": "1",
            },
        )
        if rows:
            return rows[0].get(column) or ""
    except Exception:
        pass
    return ""


def data_uri_response(data_uri, max_age=3600):
    if not data_uri or "," not in data_uri:
        return None
    try:
        header, encoded = data_uri.split(",", 1)
        mime = header.split(":", 1)[1].split(";", 1)[0]
        raw = base64.b64decode(encoded)
    except Exception:
        return None

    response = send_file(
        BytesIO(raw),
        mimetype=mime,
        max_age=max_age,
    )
    response.headers["Cache-Control"] = (
        f"public, max-age={max_age}"
    )
    return response


def file_to_data_uri(file_storage, max_bytes):
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

    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def admin_enabled():
    return bool(app.config["ADMIN_PASSWORD"])


def auth_users_exist():
    try:
        result = sb_rpc_public("operahub_has_users")
        return bool(result)
    except Exception:
        return False


def load_users():
    if not SUPABASE_WRITE_TOKEN:
        return []
    try:
        rows = sb_rpc("operahub_list_users", {})
        return rows or []
    except Exception:
        return []


def current_user():
    if session.get("user_id"):
        name = session.get("user_name") or session.get("username") or "Usuário"
        initials = "".join(
            part[0] for part in str(name).split()[:2] if part
        ).upper() or "US"
        return {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "name": name,
            "email": session.get("user_email") or "",
            "role": session.get("user_role") or "user",
            "initials": initials,
            "legacy": False,
        }

    if session.get("admin_ok"):
        return {
            "id": "legacy-admin",
            "username": "admin",
            "name": "Administrador",
            "email": "",
            "role": "admin",
            "initials": "AD",
            "legacy": True,
        }

    return None


def is_logged_in():
    return current_user() is not None


def admin_authorized():
    user = current_user()
    if user and user.get("role") == "admin":
        return True

    if not auth_users_exist() and not admin_enabled():
        return True

    return False


@app.route("/assets/logo")
def logo_asset():
    data = asset_data(
        "operahub_settings",
        "logo_data",
        "id",
        "main",
    )
    response = data_uri_response(data)
    if response is not None:
        return response
    return redirect(url_for("static", filename="favicon.svg"))


@app.route("/assets/favicon")
def favicon_asset():
    data = asset_data(
        "operahub_settings",
        "favicon_data",
        "id",
        "main",
    )
    response = data_uri_response(data)
    if response is not None:
        return response
    return redirect(url_for("static", filename="favicon.svg"))


@app.route("/assets/hero")
def hero_asset():
    data = asset_data(
        "operahub_settings",
        "hero_data",
        "id",
        "main",
    )
    response = data_uri_response(data)
    if response is not None:
        return response
    return redirect(HERO_IMAGE)


@app.route("/assets/app/<app_key>")
def application_asset(app_key):
    data = asset_data(
        "operahub_applications",
        "image_data",
        "key",
        app_key,
    )
    response = data_uri_response(data)
    if response is not None:
        return response
    return ("", 404)


@app.route("/")
def index():
    settings = load_settings()

    if (
        settings.get("login_required")
        and auth_users_exist()
        and not is_logged_in()
    ):
        return redirect(url_for("login", next=url_for("index")))

    return render_template(
        "index.html",
        nav_items=load_nav(),
        applications=load_apps(),
        settings=settings,
        logged_in=is_logged_in(),
        current_user=current_user(),
        can_admin=admin_authorized(),
        hero_image=url_for(
            "hero_asset",
            v=settings.get("updated_at", ""),
        ),
    )


@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    if not admin_authorized():
        return redirect(url_for("login", next=url_for("configuracoes")))

    nav_items = load_nav()
    applications = load_apps()
    settings = load_settings()
    users = load_users()

    if request.method == "POST":
        try:
            config_action = request.form.get(
                "config_action",
                "save_general",
            )

            if config_action == "create_user":
                username = request.form.get("user_username", "").strip()
                full_name = request.form.get("user_full_name", "").strip()
                email = request.form.get("user_email", "").strip()
                password = request.form.get("user_password", "")
                role = request.form.get("user_role", "user")

                if not username or not full_name or not password:
                    raise ValueError(
                        "Informe nome, usuário e senha para criar a conta."
                    )

                sb_rpc(
                    "operahub_create_user",
                    {
                        "p_username": username,
                        "p_full_name": full_name,
                        "p_email": email,
                        "p_password": password,
                        "p_role": role,
                    },
                )
                flash("Usuário criado com sucesso.", "success")
                return redirect(
                    url_for("configuracoes", _anchor="login")
                )

            if config_action == "save_login_settings":
                require_login = (
                    request.form.get("login_required") == "on"
                )

                if require_login and not auth_users_exist():
                    raise ValueError(
                        "Crie pelo menos um usuário antes de exigir login."
                    )

                sb_rpc(
                    "operahub_set_login_required",
                    {
                        "p_login_required": require_login,
                    },
                )
                flash(
                    "Configuração de acesso atualizada.",
                    "success",
                )
                return redirect(
                    url_for("configuracoes", _anchor="login")
                )

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
                image_file = request.files.get(
                    f"app_image_{key}"
                )
                remove_image = request.form.get(
                    f"remove_app_image_{key}"
                ) == "on"
                new_image = file_to_data_uri(
                    image_file,
                    10 * 1024 * 1024,
                )
                update_image = remove_image or new_image is not None
                current_color = item.get(
                    "accent_color",
                    "#F4B400",
                )

                app_payload.append(
                    {
                        "key": key,
                        "url": safe_url(
                            request.form.get(f"app_url_{key}", "")
                        ),
                        "new_tab": request.form.get(
                            f"app_new_tab_{key}"
                        ) == "on",
                        "accent_color": safe_hex_color(
                            request.form.get(
                                f"app_color_{key}",
                                current_color,
                            ),
                            current_color,
                        ),
                        "image_zoom": max(
                            100,
                            min(
                                220,
                                int(
                                    request.form.get(
                                        f"app_zoom_{key}",
                                        item.get("image_zoom", 142),
                                    )
                                ),
                            ),
                        ),
                        "update_image": update_image,
                        "image_data": (
                            ""
                            if remove_image
                            else (new_image or "")
                        ),
                    }
                )

            remove_logo = request.form.get("remove_logo") == "on"
            new_logo = file_to_data_uri(
                request.files.get("logo_upload"),
                10 * 1024 * 1024,
            )
            update_logo = remove_logo or new_logo is not None

            remove_favicon = (
                request.form.get("remove_favicon") == "on"
            )
            new_favicon = file_to_data_uri(
                request.files.get("favicon_upload"),
                10 * 1024 * 1024,
            )
            update_favicon = (
                remove_favicon or new_favicon is not None
            )

            remove_hero = request.form.get("remove_hero") == "on"
            new_hero = file_to_data_uri(
                request.files.get("hero_upload"),
                10 * 1024 * 1024,
            )
            update_hero = remove_hero or new_hero is not None

            logo_width = max(
                80,
                min(
                    240,
                    int(
                        request.form.get(
                            "logo_width",
                            settings.get("logo_width", 190),
                        )
                    ),
                ),
            )

            hero_pos_x = max(
                0,
                min(
                    100,
                    int(
                        request.form.get(
                            "hero_pos_x",
                            settings.get("hero_pos_x", 50),
                        )
                    ),
                ),
            )
            hero_pos_y = max(
                0,
                min(
                    100,
                    int(
                        request.form.get(
                            "hero_pos_y",
                            settings.get("hero_pos_y", 50),
                        )
                    ),
                ),
            )
            hero_zoom = max(
                100,
                min(
                    220,
                    int(
                        request.form.get(
                            "hero_zoom",
                            settings.get("hero_zoom", 100),
                        )
                    ),
                ),
            )

            sb_rpc(
                "operahub_save_settings_v3",
                {
                    "p_logo_data": (
                        ""
                        if remove_logo
                        else (new_logo or "")
                    ),
                    "p_favicon_data": (
                        ""
                        if remove_favicon
                        else (new_favicon or "")
                    ),
                    "p_logo_width": logo_width,
                    "p_hero_data": (
                        ""
                        if remove_hero
                        else (new_hero or "")
                    ),
                    "p_update_logo": update_logo,
                    "p_update_favicon": update_favicon,
                    "p_update_hero": update_hero,
                    "p_hero_pos_x": hero_pos_x,
                    "p_hero_pos_y": hero_pos_y,
                    "p_hero_zoom": hero_zoom,
                },
            )
            sb_rpc("operahub_save_nav", {"p_items": nav_payload})
            sb_rpc(
                "operahub_save_apps_v3",
                {"p_items": app_payload},
            )

            flash(
                "Alterações salvas permanentemente no Supabase.",
                "success",
            )
            return redirect(url_for("configuracoes"))
        except Exception as exc:
            flash(f"Não foi possível salvar: {exc}", "error")

    return render_template(
        "config.html",
        nav_items=nav_items,
        applications=applications,
        settings=settings,
        admin_enabled=admin_enabled(),
        auth_users_exist=auth_users_exist(),
        users=users,
        current_user=current_user(),
        supabase_write_ready=bool(SUPABASE_WRITE_TOKEN),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or url_for("index")
    if not next_url.startswith("/"):
        next_url = url_for("index")

    if request.method == "POST":
        login_id = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        try:
            rows = sb_rpc_public(
                "operahub_auth_user",
                {
                    "p_login": login_id,
                    "p_password": password,
                },
            )
        except Exception:
            rows = []

        if rows:
            user = rows[0]
            session.clear()
            session["user_id"] = str(user["id"])
            session["username"] = user["username"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user.get("email") or ""
            session["user_role"] = user["role"]
            session.permanent = True
            flash(
                f"Bem-vindo, {user['full_name']}.",
                "success",
            )
            return redirect(next_url)

        if (
            admin_enabled()
            and password == app.config["ADMIN_PASSWORD"]
        ):
            session.clear()
            session["admin_ok"] = True
            session.permanent = True
            flash(
                "Acesso administrativo realizado.",
                "success",
            )
            return redirect(next_url)

        flash(
            "Usuário ou senha inválidos.",
            "error",
        )

    return render_template(
        "login.html",
        settings=load_settings(),
        admin_enabled=admin_enabled(),
        auth_users_exist=auth_users_exist(),
        next_url=next_url,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/healthz")
def healthz():
    return {
        "status": "ok",
        "storage": "supabase",
        "admin_auth_configured": admin_enabled(),
        "user_auth_configured": auth_users_exist(),
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True,
    )
