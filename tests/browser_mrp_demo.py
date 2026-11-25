"""End-to-end on an isolated Hub with demo-only in-memory material examples."""
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def check(browser, url, password, width):
    with browser.new_context(viewport={"width":width,"height":900 if width>800 else 844}) as context:
        p=context.new_page()
        p.route("**/*", lambda route: route.continue_() if route.request.url.startswith(url+"/") else route.abort())
        p.goto(url+"/mrp",wait_until="domcontentloaded")
        p.locator('input[name="login"]').fill("admin")
        p.locator('input[name="password"]').fill(password)
        p.locator('button[type="submit"]').click()
        expect(p.get_by_role("heading",name="MRP atual")).to_be_visible()
        expect(p.get_by_text("Dados fictícios",exact=False)).to_be_visible()
        assert p.evaluate("document.documentElement.scrollWidth")<=width+2
        first=p.get_by_role("button",name="Detalhar material 00841021")
        expect(first).to_be_visible()
        if width<=800:
            assert first.evaluate("(b)=>b.getBoundingClientRect().right<=window.innerWidth"), "Detalhe cortado no celular"
        first.click()
        detail=p.get_by_role("dialog")
        expect(detail.get_by_role("heading",name="Contator tripolar 32 A")).to_be_visible()
        detail.get_by_role("button",name="Compras",exact=True).click()
        expect(detail.get_by_role("cell",name="P.C.",exact=True)).to_be_visible()
        p.keyboard.press("Escape")
        expect(detail).not_to_be_visible()
        p.get_by_role("button",name="Próxima página").click()
        expect(p.get_by_text("2 / 5",exact=True)).to_be_visible()
        p.get_by_role("searchbox",name="Buscar por código ou descrição").fill("00841021")
        p.get_by_role("button",name="Buscar",exact=True).click()
        expect(p.get_by_text("1–1 de 1 material",exact=True)).to_be_visible()
        expect(p.get_by_role("button",name="Próxima página")).to_be_disabled()
        if os.getenv("MRP_SCREENSHOTS"):
            p.screenshot(path=f"{os.environ['MRP_SCREENSHOTS']}/mrp-opera-{width}.png")
        print(f"Opera Hub MRP: sessão, busca, segunda página e detalhe em {width}px OK",flush=True)


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port=sock.getsockname()[1]
    root=Path(__file__).resolve().parents[1]
    url=f"http://127.0.0.1:{port}"
    password=secrets.token_urlsafe(24)
    env=dict(os.environ, OPERAHUB_DEFAULT_ORG="opera-hub-demo", OPERAHUB_MRP_DEMO="1",
             SUPABASE_WRITE_TOKEN="", SECRET_KEY=secrets.token_hex(32),ADMIN_PASSWORD=password)
    server=subprocess.Popen([sys.executable,"-m","flask","--app","app","run","--port",str(port)],cwd=root,env=env,
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                with urlopen(url+"/healthz",timeout=1): break
            except OSError:
                time.sleep(.25)
        else: raise RuntimeError("Servidor de teste não iniciou")
        chrome=os.environ.get("MRP_CHROME") or shutil.which("google-chrome") or shutil.which("chromium")
        with sync_playwright() as p:
            b=p.chromium.launch(executable_path=chrome,args=["--no-sandbox","--disable-dev-shm-usage"])
            try:
                for width in (1440,390):check(b,url,password,width)
            finally:b.close()
    finally:
        server.terminate()
        server.wait(timeout=10)

if __name__=="__main__":
    main()
