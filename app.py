import base64
import os
import re
import time
import unicodedata
from io import BytesIO
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from PIL import Image, ImageOps
from flask import (
    Flask,
    flash,
    g,
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

HERO_CACHE = {}
APP_IMAGE_CACHE = {}
BRAND_IMAGE_CACHE = {}
LOGIN_IMAGE_CACHE = {}
RUNTIME_CACHE = {}

HTTP = requests.Session()
HTTP.mount("https://", HTTPAdapter(pool_connections=20, pool_maxsize=20))
HTTP.mount("http://", HTTPAdapter(pool_connections=10, pool_maxsize=10))

BOOTSTRAP_TTL = 120
USERS_TTL = 45
ASSET_DATA_TTL = 900
SUPABASE_CONNECT_TIMEOUT = 3.05
SUPABASE_READ_TIMEOUT = 8
SUPABASE_WRITE_TIMEOUT = 12
SLOW_BACKEND_SECONDS = 0.8

WRITE_RPCS = {
    "operahub_create_user_v2",
    "operahub_update_user_avatar",
    "operahub_set_login_required",
    "operahub_save_login_visual",
    "operahub_save_settings_v3",
    "operahub_save_nav",
    "operahub_save_apps_v4",
    "operahub_save_general_v1",
}


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
    "has_login_image": False,
    "login_pos_x": 50,
    "login_pos_y": 50,
    "login_zoom": 100,
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
    {"key": "gestao-equipes", "name": "GESTÃO DE EQUIPES", "description": "Acompanhamento de indicadores e equipes.", "icon": "fa-solid fa-people-group", "status": "online", "url": "", "sort_order": 1, "new_tab": True},
    {"key": "conversor-mrp", "name": "CONVERSOR MRP", "description": "Conversor de relatórios para alimentação MRP.", "icon": "fa-solid fa-file-circle-check", "status": "online", "url": "", "sort_order": 2, "new_tab": True},
    {"key": "mrp", "name": "MRP", "description": "Demanda e necessidade de materiais.", "icon": "fa-solid fa-clipboard-list", "status": "online", "url": "", "sort_order": 3, "new_tab": True},
    {"key": "gestao-entregas", "name": "GESTÃO DE ENTREGAS", "description": "Controle de entrega de OPs e cronograma.", "icon": "fa-solid fa-truck-fast", "status": "online", "url": "", "sort_order": 4, "new_tab": True},
    {"key": "inventario-rotativo", "name": "INVENTÁRIO ROTATIVO", "description": "Acompanhamento e geração de inventários.", "icon": "fa-solid fa-boxes-stacked", "status": "development", "url": "", "sort_order": 5, "new_tab": True},
    {"key": "smtc", "name": "SMTC", "description": "Acompanhamento, armazenamento e reposição de parafusos, porcas e arruelas.", "icon": "fa-solid fa-screwdriver-wrench", "status": "development", "url": "", "sort_order": 6, "new_tab": True},
    {"key": "gestao-nfs", "name": "GESTÃO DE NFS", "description": "Controle de realização e envio de NFs para lançamento.", "icon": "fa-solid fa-file-invoice-dollar", "status": "online", "url": "", "sort_order": 7, "new_tab": True},
    {"key": "fechamento-mensal", "name": "FECHAMENTO MENSAL", "description": "Auditoria de baixas, acompanhamento da evolução de estoque mês a mês.", "icon": "fa-solid fa-chart-simple", "status": "development", "url": "", "sort_order": 8, "new_tab": True},
    {"key": "monitor-apis", "name": "MONITOR DE APIs", "description": "Painel de verificação de status de conexão de APIs.", "icon": "fa-solid fa-network-wired", "status": "development", "url": "", "sort_order": 9, "new_tab": True},
]


def cache_get(key, ttl):
    item = RUNTIME_CACHE.get(key)
    if not item:
        return None

    created_at, value = item
    if (time.monotonic() - created_at) > ttl:
        RUNTIME_CACHE.pop(key, None)
        return None

    return value


def cache_set(key, value):
    RUNTIME_CACHE[key] = (time.monotonic(), value)
    return value


def invalidate_runtime_caches():
    # Invalida apenas dados leves. As imagens usam URLs versionadas,
    # então manter o cache binário evita reprocessamento desnecessário.
    RUNTIME_CACHE.clear()


def log_slow_backend(label, started_at):
    elapsed = time.perf_counter() - started_at
    if elapsed >= SLOW_BACKEND_SECONDS:
        app.logger.warning(
            "PERF backend=%s duration_ms=%d",
            label,
            round(elapsed * 1000),
        )


def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def sb_get(table, params):
    started_at = time.perf_counter()
    try:
        response = HTTP.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=sb_headers(),
            params=params,
            timeout=(
                SUPABASE_CONNECT_TIMEOUT,
                SUPABASE_READ_TIMEOUT,
            ),
        )
        response.raise_for_status()
        return response.json()
    finally:
        log_slow_backend(f"GET:{table}", started_at)


def sb_rpc(name, payload):
    if not SUPABASE_WRITE_TOKEN:
        raise RuntimeError(
            "SUPABASE_WRITE_TOKEN não configurado no Render."
        )

    started_at = time.perf_counter()
    try:
        response = HTTP.post(
            f"{SUPABASE_URL}/rest/v1/rpc/{name}",
            headers=sb_headers(),
            json={"p_token": SUPABASE_WRITE_TOKEN, **payload},
            timeout=(
                SUPABASE_CONNECT_TIMEOUT,
                SUPABASE_WRITE_TIMEOUT,
            ),
        )
        response.raise_for_status()
        if not response.content:
            result = None
        else:
            result = response.json()
    finally:
        log_slow_backend(f"RPC:{name}", started_at)

    if name in WRITE_RPCS:
        invalidate_runtime_caches()

    return result


def sb_rpc_public(name, payload=None):
    started_at = time.perf_counter()
    try:
        response = HTTP.post(
            f"{SUPABASE_URL}/rest/v1/rpc/{name}",
            headers=sb_headers(),
            json=payload or {},
            timeout=(
                SUPABASE_CONNECT_TIMEOUT,
                SUPABASE_READ_TIMEOUT,
            ),
        )
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()
    finally:
        log_slow_backend(f"RPC_PUBLIC:{name}", started_at)


def normalize_settings(row):
    data = dict(DEFAULT_SETTINGS)
    if isinstance(row, dict):
        data.update(row)

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
    data["login_pos_x"] = max(
        0,
        min(100, int(data.get("login_pos_x") or 50)),
    )
    data["login_pos_y"] = max(
        0,
        min(100, int(data.get("login_pos_y") or 50)),
    )
    data["login_zoom"] = max(
        100,
        min(220, int(data.get("login_zoom") or 100)),
    )
    return data


def fallback_apps():
    items = []
    for item in DEFAULT_APPLICATIONS:
        data = dict(item)
        data["has_image"] = False
        data["image_zoom"] = 142
        data["updated_at"] = ""
        items.append(data)
    return items


def load_bootstrap():
    stale_item = RUNTIME_CACHE.get("bootstrap")
    stale_value = stale_item[1] if stale_item else None

    cached = cache_get("bootstrap", BOOTSTRAP_TTL)
    if cached is not None:
        return cached

    fallback = {
        "settings": dict(DEFAULT_SETTINGS),
        "nav": [dict(item) for item in DEFAULT_NAV_ITEMS],
        "applications": fallback_apps(),
        "has_users": False,
    }

    try:
        payload = sb_rpc_public("operahub_bootstrap")
        if isinstance(payload, dict):
            settings = normalize_settings(payload.get("settings") or {})
            nav_items = payload.get("nav") or fallback["nav"]
            applications = (
                payload.get("applications")
                or fallback["applications"]
            )
            result = {
                "settings": settings,
                "nav": nav_items,
                "applications": applications,
                "has_users": bool(payload.get("has_users")),
            }
            return cache_set("bootstrap", result)
    except Exception as exc:
        app.logger.warning(
            "Bootstrap Supabase indisponível: %s",
            exc,
        )

    if stale_value is not None:
        return stale_value

    return fallback


def load_settings():
    return dict(load_bootstrap()["settings"])


def load_nav():
    return [
        dict(item)
        for item in load_bootstrap()["nav"]
    ]


def load_apps():
    return [
        dict(item)
        for item in load_bootstrap()["applications"]
    ]


def safe_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    return ""


def normalize_username(value):
    raw = unicodedata.normalize(
        "NFKD",
        (value or "").strip().lower(),
    )
    ascii_value = "".join(
        ch for ch in raw
        if not unicodedata.combining(ch)
    )
    ascii_value = ascii_value.encode(
        "ascii",
        "ignore",
    ).decode("ascii")
    ascii_value = re.sub(
        r"[^a-z0-9._-]+",
        ".",
        ascii_value,
    )
    ascii_value = re.sub(r"\.{2,}", ".", ascii_value)
    return ascii_value.strip(".")


def humanize_save_error(exc):
    detail = str(exc)
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            payload = response.json()
            detail = " ".join(
                str(payload.get(key, ""))
                for key in ("message", "details", "hint")
            ).strip() or detail
        except Exception:
            detail = getattr(response, "text", "") or detail

    lowered = detail.lower()

    if "username_invalid" in lowered:
        return (
            "O nome de usuário precisa ter pelo menos 3 caracteres. "
            "Use letras, números, ponto, hífen ou sublinhado."
        )
    if "password_too_short" in lowered:
        return "A senha precisa ter pelo menos 6 caracteres."
    if "name_invalid" in lowered:
        return "Informe um nome válido para o usuário."
    if "user_or_email_already_exists" in lowered:
        return "Já existe um usuário ou e-mail com esses dados."
    if "unauthorized" in lowered:
        return (
            "O token de gravação do Supabase não foi aceito. "
            "Verifique SUPABASE_WRITE_TOKEN no Render."
        )

    return "Não foi possível concluir a alteração. Revise os dados e tente novamente."


def asset_data(table, column, key_column, key_value):
    cache_key = (
        f"asset:{table}:{column}:{key_column}:{key_value}"
    )
    stale_item = RUNTIME_CACHE.get(cache_key)
    stale_value = stale_item[1] if stale_item else None

    cached = cache_get(cache_key, ASSET_DATA_TTL)
    if cached is not None:
        return cached

    try:
        rows = sb_get(
            table,
            {
                key_column: f"eq.{key_value}",
                "select": column,
                "limit": "1",
            },
        )
        value = rows[0].get(column) or "" if rows else ""
        return cache_set(cache_key, value)
    except Exception as exc:
        app.logger.warning(
            "Asset Supabase indisponível table=%s column=%s: %s",
            table,
            column,
            exc,
        )
        if stale_value is not None:
            return stale_value
        return ""


def binary_response(raw, mime, max_age=3600):
    response = send_file(
        BytesIO(raw),
        mimetype=mime,
        max_age=max_age,
    )
    response.headers["Cache-Control"] = (
        f"public, max-age={max_age}, immutable"
    )
    return response


def data_uri_parts(data_uri):
    if not data_uri or "," not in data_uri:
        return None, None
    try:
        header, encoded = data_uri.split(",", 1)
        mime = header.split(":", 1)[1].split(";", 1)[0]
        raw = base64.b64decode(encoded)
        return mime, raw
    except Exception:
        return None, None


def data_uri_response(data_uri, max_age=3600):
    mime, raw = data_uri_parts(data_uri)
    if not mime or raw is None:
        return None
    return binary_response(raw, mime, max_age=max_age)


def optimize_banner_data_uri(data_uri, force=False):
    if (
        not force
        and str(data_uri).startswith("data:image/webp;base64,")
    ):
        return data_uri

    mime, raw = data_uri_parts(data_uri)
    if not mime or raw is None:
        return data_uri

    if mime == "image/svg+xml":
        return data_uri

    try:
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(
                (2200, 1400),
                Image.Resampling.LANCZOS,
            )

            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGB")

            output = BytesIO()
            image.save(
                output,
                format="WEBP",
                quality=82,
                method=6,
            )
            optimized = output.getvalue()

        if len(optimized) >= len(raw):
            return data_uri

        encoded = base64.b64encode(optimized).decode("ascii")
        return f"data:image/webp;base64,{encoded}"
    except Exception:
        return data_uri


def optimize_app_icon_data_uri(data_uri, force=False):
    if (
        not force
        and str(data_uri).startswith("data:image/webp;base64,")
    ):
        return data_uri

    mime, raw = data_uri_parts(data_uri)
    if not mime or raw is None:
        return data_uri

    if mime == "image/svg+xml":
        return data_uri

    try:
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(
                (320, 320),
                Image.Resampling.LANCZOS,
            )

            has_alpha = (
                image.mode in {"RGBA", "LA"}
                or (
                    image.mode == "P"
                    and "transparency" in image.info
                )
            )
            image = image.convert("RGBA" if has_alpha else "RGB")

            output = BytesIO()
            image.save(
                output,
                format="WEBP",
                quality=84,
                method=6,
            )
            optimized = output.getvalue()

        if len(optimized) >= len(raw):
            return data_uri

        encoded = base64.b64encode(optimized).decode("ascii")
        return f"data:image/webp;base64,{encoded}"
    except Exception:
        return data_uri


def optimize_brand_data_uri(data_uri, favicon=False, force=False):
    raw_value = str(data_uri)
    if not force:
        if (
            not favicon
            and raw_value.startswith("data:image/webp;base64,")
        ):
            return data_uri
        if (
            favicon
            and raw_value.startswith("data:image/png;base64,")
            and len(raw_value) <= 120000
        ):
            return data_uri

    mime, raw = data_uri_parts(data_uri)
    if not mime or raw is None:
        return data_uri

    if mime == "image/svg+xml":
        return data_uri

    try:
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            max_size = (192, 192) if favicon else (720, 260)
            image.thumbnail(
                max_size,
                Image.Resampling.LANCZOS,
            )

            has_alpha = (
                image.mode in {"RGBA", "LA"}
                or (
                    image.mode == "P"
                    and "transparency" in image.info
                )
            )

            output = BytesIO()

            if favicon:
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.save(
                    output,
                    format="PNG",
                    optimize=True,
                )
                out_mime = "image/png"
            else:
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.save(
                    output,
                    format="WEBP",
                    quality=88,
                    method=6,
                )
                out_mime = "image/webp"

            optimized = output.getvalue()

        if len(optimized) >= len(raw):
            return data_uri

        encoded = base64.b64encode(optimized).decode("ascii")
        return f"data:{out_mime};base64,{encoded}"
    except Exception:
        return data_uri


def file_to_data_uri(
    file_storage,
    max_bytes,
    optimize_banner=False,
    optimize_app_icon=False,
):
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
    data_uri = f"data:{mime};base64,{encoded}"

    if optimize_banner:
        data_uri = optimize_banner_data_uri(
            data_uri,
            force=True,
        )

    if optimize_app_icon:
        data_uri = optimize_app_icon_data_uri(
            data_uri,
            force=True,
        )

    return data_uri


def admin_enabled():
    return bool(app.config["ADMIN_PASSWORD"])


def auth_users_exist():
    return bool(load_bootstrap().get("has_users"))


def load_users():
    if not SUPABASE_WRITE_TOKEN:
        return []

    stale_item = RUNTIME_CACHE.get("users")
    stale_value = stale_item[1] if stale_item else None

    cached = cache_get("users", USERS_TTL)
    if cached is not None:
        return [dict(row) for row in cached]

    try:
        rows = sb_rpc("operahub_list_users", {}) or []
        cache_set("users", rows)
        return [dict(row) for row in rows]
    except Exception as exc:
        app.logger.warning(
            "Lista de usuários indisponível: %s",
            exc,
        )
        if stale_value is not None:
            return [dict(row) for row in stale_value]
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
            "has_avatar": bool(session.get("user_has_avatar")),
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
            "has_avatar": False,
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
    version = request.args.get("v", "current")
    cache_key = f"logo:{version}"

    cached = BRAND_IMAGE_CACHE.get(cache_key)
    if cached:
        raw, mime = cached
        return binary_response(raw, mime, max_age=2592000)

    data = asset_data(
        "operahub_settings",
        "logo_data",
        "id",
        "main",
    )

    if data:
        optimized = optimize_brand_data_uri(data, favicon=False)
        mime, raw = data_uri_parts(optimized)
        if mime and raw is not None:
            BRAND_IMAGE_CACHE[cache_key] = (raw, mime)

            if optimized != data and SUPABASE_WRITE_TOKEN:
                try:
                    sb_rpc(
                        "operahub_store_optimized_brand_assets",
                        {
                            "p_logo_data": optimized,
                            "p_favicon_data": None,
                        },
                    )
                except Exception:
                    pass

            return binary_response(raw, mime, max_age=2592000)

    return redirect(url_for("static", filename="favicon.svg"))


@app.route("/assets/favicon")
def favicon_asset():
    version = request.args.get("v", "current")
    cache_key = f"favicon:{version}"

    cached = BRAND_IMAGE_CACHE.get(cache_key)
    if cached:
        raw, mime = cached
        return binary_response(raw, mime, max_age=2592000)

    data = asset_data(
        "operahub_settings",
        "favicon_data",
        "id",
        "main",
    )

    if data:
        optimized = optimize_brand_data_uri(data, favicon=True)
        mime, raw = data_uri_parts(optimized)
        if mime and raw is not None:
            BRAND_IMAGE_CACHE[cache_key] = (raw, mime)

            if optimized != data and SUPABASE_WRITE_TOKEN:
                try:
                    sb_rpc(
                        "operahub_store_optimized_brand_assets",
                        {
                            "p_logo_data": None,
                            "p_favicon_data": optimized,
                        },
                    )
                except Exception:
                    pass

            return binary_response(raw, mime, max_age=2592000)

    return redirect(url_for("static", filename="favicon.svg"))


@app.route("/assets/hero")
def hero_asset():
    version = request.args.get("v", "current")

    cached = HERO_CACHE.get(version)
    if cached:
        raw, mime = cached
        return binary_response(
            raw,
            mime,
            max_age=604800,
        )

    data = asset_data(
        "operahub_settings",
        "hero_data",
        "id",
        "main",
    )

    if data:
        optimized = optimize_banner_data_uri(data)
        mime, raw = data_uri_parts(optimized)

        if mime and raw is not None:
            HERO_CACHE.clear()
            HERO_CACHE[version] = (raw, mime)

            if optimized != data and SUPABASE_WRITE_TOKEN:
                try:
                    sb_rpc(
                        "operahub_store_optimized_hero",
                        {"p_hero_data": optimized},
                    )
                except Exception:
                    pass

            return binary_response(
                raw,
                mime,
                max_age=604800,
            )

    return redirect(HERO_IMAGE)


@app.route("/assets/login-image")
def login_image_asset():
    version = request.args.get("v", "current")
    cache_key = f"login-image:{version}"

    cached = LOGIN_IMAGE_CACHE.get(cache_key)
    if cached:
        raw, mime = cached
        return binary_response(
            raw,
            mime,
            max_age=2592000,
        )

    data = asset_data(
        "operahub_settings",
        "login_image_data",
        "id",
        "main",
    )
    mime, raw = data_uri_parts(data)

    if mime and raw is not None:
        LOGIN_IMAGE_CACHE.clear()
        LOGIN_IMAGE_CACHE[cache_key] = (raw, mime)
        return binary_response(
            raw,
            mime,
            max_age=2592000,
        )

    return redirect(
        url_for("hero_asset", v=version)
    )


@app.route("/assets/app/<app_key>")
def application_asset(app_key):
    version = request.args.get("v", "current")
    cache_key = f"{app_key}:{version}"

    cached = APP_IMAGE_CACHE.get(cache_key)
    if cached:
        raw, mime = cached
        return binary_response(
            raw,
            mime,
            max_age=2592000,
        )

    data = asset_data(
        "operahub_applications",
        "image_data",
        "key",
        app_key,
    )

    if data:
        optimized = optimize_app_icon_data_uri(data)
        mime, raw = data_uri_parts(optimized)

        if mime and raw is not None:
            # Keep cache small and invalidate old versions of this module.
            stale_keys = [
                key for key in APP_IMAGE_CACHE
                if key.startswith(f"{app_key}:")
            ]
            for key in stale_keys:
                APP_IMAGE_CACHE.pop(key, None)

            APP_IMAGE_CACHE[cache_key] = (raw, mime)

            if optimized != data and SUPABASE_WRITE_TOKEN:
                try:
                    sb_rpc(
                        "operahub_store_optimized_app_image",
                        {
                            "p_key": app_key,
                            "p_image_data": optimized,
                        },
                    )
                except Exception:
                    pass

            return binary_response(
                raw,
                mime,
                max_age=2592000,
            )

    return ("", 404)


@app.route("/assets/user/<user_id>")
def user_avatar_asset(user_id):
    if not is_logged_in():
        return ("", 403)

    version = request.args.get("v", "current")
    cache_key = f"user-avatar:{user_id}:{version}"
    data = cache_get(cache_key, ASSET_DATA_TTL)

    if data is None:
        try:
            data = sb_rpc_public(
                "operahub_get_user_avatar",
                {"p_user_id": user_id},
            ) or ""
        except Exception:
            data = ""
        cache_set(cache_key, data)

    response = data_uri_response(
        data,
        max_age=2592000,
    )
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
        return redirect(
            url_for("login", next=url_for("configuracoes"))
        )

    if request.method == "POST":
        try:
            config_action = request.form.get(
                "config_action",
                "save_general",
            )

            if config_action == "create_user":
                username = normalize_username(
                    request.form.get("user_username", "")
                )
                full_name = request.form.get(
                    "user_full_name",
                    "",
                ).strip()
                email = request.form.get(
                    "user_email",
                    "",
                ).strip()
                password = request.form.get(
                    "user_password",
                    "",
                )
                role = request.form.get(
                    "user_role",
                    "user",
                )
                avatar_data = file_to_data_uri(
                    request.files.get("user_avatar"),
                    5 * 1024 * 1024,
                ) or ""

                if not username or not full_name or not password:
                    raise ValueError(
                        "Informe nome, usuário e senha para criar a conta."
                    )

                sb_rpc(
                    "operahub_create_user_v2",
                    {
                        "p_username": username,
                        "p_full_name": full_name,
                        "p_email": email,
                        "p_password": password,
                        "p_role": role,
                        "p_avatar_data": avatar_data,
                    },
                )
                flash(
                    "Usuário criado com sucesso.",
                    "success",
                )
                return redirect(
                    url_for("configuracoes", _anchor="login")
                )

            if config_action == "update_user_avatar":
                target_user_id = request.form.get(
                    "user_avatar_target",
                    "",
                ).strip()
                if not target_user_id:
                    raise ValueError("Usuário não identificado.")

                avatar_file = request.files.get(
                    f"user_avatar_{target_user_id}"
                )
                remove_avatar = request.form.get(
                    f"remove_user_avatar_{target_user_id}"
                ) == "on"

                avatar_data = (
                    ""
                    if remove_avatar
                    else (
                        file_to_data_uri(
                            avatar_file,
                            5 * 1024 * 1024,
                        )
                        or ""
                    )
                )

                if not remove_avatar and not avatar_data:
                    raise ValueError(
                        "Selecione uma foto antes de salvar."
                    )

                sb_rpc(
                    "operahub_update_user_avatar",
                    {
                        "p_user_id": target_user_id,
                        "p_avatar_data": avatar_data,
                    },
                )

                if session.get("user_id") == target_user_id:
                    session["user_has_avatar"] = bool(avatar_data)

                flash(
                    "Foto do usuário atualizada.",
                    "success",
                )
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

            if config_action == "save_login_visual":
                settings = load_settings()
                remove_login_image = (
                    request.form.get("remove_login_image") == "on"
                )
                new_login_image = file_to_data_uri(
                    request.files.get("login_image_upload"),
                    10 * 1024 * 1024,
                    optimize_banner=True,
                )
                update_login_image = (
                    remove_login_image
                    or new_login_image is not None
                )

                login_pos_x = max(
                    0,
                    min(
                        100,
                        int(
                            request.form.get(
                                "login_pos_x",
                                settings.get("login_pos_x", 50),
                            )
                        ),
                    ),
                )
                login_pos_y = 50
                login_zoom = max(
                    100,
                    min(
                        220,
                        int(
                            request.form.get(
                                "login_zoom",
                                settings.get("login_zoom", 100),
                            )
                        ),
                    ),
                )

                sb_rpc(
                    "operahub_save_login_visual",
                    {
                        "p_login_image_data": (
                            ""
                            if remove_login_image
                            else (new_login_image or "")
                        ),
                        "p_update_login_image": update_login_image,
                        "p_login_pos_x": login_pos_x,
                        "p_login_pos_y": login_pos_y,
                        "p_login_zoom": login_zoom,
                    },
                )
                flash(
                    "Imagem da tela de login atualizada.",
                    "success",
                )
                return redirect(
                    url_for("configuracoes", _anchor="identity")
                )

            bootstrap = load_bootstrap()
            settings = dict(bootstrap["settings"])
            nav_items = [
                dict(item)
                for item in bootstrap["nav"]
            ]
            applications = [
                dict(item)
                for item in bootstrap["applications"]
            ]

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
            valid_statuses = {
                "online",
                "development",
                "maintenance",
            }

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
                    optimize_app_icon=True,
                )
                update_image = (
                    remove_image
                    or new_image is not None
                )
                app_status = request.form.get(
                    f"app_status_{key}",
                    item.get("status", "online"),
                )
                if app_status not in valid_statuses:
                    app_status = "online"

                app_payload.append(
                    {
                        "key": key,
                        "url": safe_url(
                            request.form.get(
                                f"app_url_{key}",
                                "",
                            )
                        ),
                        "new_tab": request.form.get(
                            f"app_new_tab_{key}"
                        ) == "on",
                        "status": app_status,
                        "image_zoom": max(
                            100,
                            min(
                                220,
                                int(
                                    request.form.get(
                                        f"app_zoom_{key}",
                                        item.get(
                                            "image_zoom",
                                            142,
                                        ),
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

            remove_logo = request.form.get(
                "remove_logo"
            ) == "on"
            new_logo = file_to_data_uri(
                request.files.get("logo_upload"),
                10 * 1024 * 1024,
            )
            if new_logo:
                new_logo = optimize_brand_data_uri(
                    new_logo,
                    favicon=False,
                    force=True,
                )
            update_logo = (
                remove_logo
                or new_logo is not None
            )

            remove_favicon = (
                request.form.get("remove_favicon") == "on"
            )
            new_favicon = file_to_data_uri(
                request.files.get("favicon_upload"),
                10 * 1024 * 1024,
            )
            if new_favicon:
                new_favicon = optimize_brand_data_uri(
                    new_favicon,
                    favicon=True,
                    force=True,
                )
            update_favicon = (
                remove_favicon
                or new_favicon is not None
            )

            remove_hero = request.form.get(
                "remove_hero"
            ) == "on"
            new_hero = file_to_data_uri(
                request.files.get("hero_upload"),
                10 * 1024 * 1024,
                optimize_banner=True,
            )
            update_hero = (
                remove_hero
                or new_hero is not None
            )

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

            settings_payload = {
                "logo_data": (
                    ""
                    if remove_logo
                    else (new_logo or "")
                ),
                "favicon_data": (
                    ""
                    if remove_favicon
                    else (new_favicon or "")
                ),
                "logo_width": logo_width,
                "hero_data": (
                    ""
                    if remove_hero
                    else (new_hero or "")
                ),
                "update_logo": update_logo,
                "update_favicon": update_favicon,
                "update_hero": update_hero,
                "hero_pos_x": hero_pos_x,
                "hero_pos_y": hero_pos_y,
                "hero_zoom": hero_zoom,
            }

            sb_rpc(
                "operahub_save_general_v1",
                {
                    "p_settings": settings_payload,
                    "p_nav": nav_payload,
                    "p_apps": app_payload,
                },
            )

            flash(
                "Alterações salvas permanentemente no Supabase.",
                "success",
            )
            return redirect(url_for("configuracoes"))
        except Exception as exc:
            flash(
                humanize_save_error(exc),
                "error",
            )

    bootstrap = load_bootstrap()
    nav_items = [
        dict(item)
        for item in bootstrap["nav"]
    ]
    applications = [
        dict(item)
        for item in bootstrap["applications"]
    ]
    settings = dict(bootstrap["settings"])
    users = load_users()

    return render_template(
        "config.html",
        nav_items=nav_items,
        applications=applications,
        settings=settings,
        admin_enabled=admin_enabled(),
        auth_users_exist=bool(bootstrap.get("has_users")),
        users=users,
        current_user=current_user(),
        supabase_write_ready=bool(SUPABASE_WRITE_TOKEN),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or url_for("index")
    if (
        not next_url.startswith("/")
        or next_url.startswith("//")
    ):
        next_url = url_for("index")

    if request.method == "POST":
        login_id = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        auth_error = False
        try:
            rows = sb_rpc_public(
                "operahub_auth_user",
                {
                    "p_login": login_id,
                    "p_password": password,
                },
            )
        except Exception as exc:
            rows = []
            auth_error = True
            app.logger.warning(
                "Falha no serviço de autenticação: %s",
                exc,
            )

        if rows:
            user = rows[0]
            session.clear()
            session["user_id"] = str(user["id"])
            session["username"] = user["username"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user.get("email") or ""
            session["user_role"] = user["role"]
            session["user_has_avatar"] = bool(
                user.get("has_avatar")
            )
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

        if auth_error:
            flash(
                "O serviço de autenticação demorou para responder. "
                "Tente novamente em alguns instantes.",
                "error",
            )
        else:
            flash(
                "Usuário ou senha inválidos.",
                "error",
            )

    settings = load_settings()
    return render_template(
        "login.html",
        settings=settings,
        admin_enabled=admin_enabled(),
        auth_users_exist=auth_users_exist(),
        next_url=next_url,
        login_image=(
            url_for(
                "login_image_asset",
                v=settings.get("updated_at", ""),
            )
            if settings.get("has_login_image")
            else url_for(
                "hero_asset",
                v=settings.get("updated_at", ""),
            )
        ),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.before_request
def start_request_timer():
    g.request_started_at = time.perf_counter()


@app.after_request
def add_server_timing(response):
    started_at = getattr(
        g,
        "request_started_at",
        None,
    )
    if started_at is None:
        return response

    elapsed = time.perf_counter() - started_at
    elapsed_ms = round(elapsed * 1000)
    response.headers["Server-Timing"] = (
        f'app;dur={elapsed_ms}'
    )

    if (
        elapsed >= 1.0
        and request.path != "/healthz"
    ):
        app.logger.warning(
            "PERF request=%s method=%s duration_ms=%d",
            request.path,
            request.method,
            elapsed_ms,
        )

    return response


@app.route("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "opera-hub",
        "supabase_configured": bool(
            SUPABASE_URL and SUPABASE_KEY
        ),
        "admin_auth_configured": admin_enabled(),
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=True,
    )
