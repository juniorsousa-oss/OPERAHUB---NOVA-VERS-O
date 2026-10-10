"""Padrão de favicon 93% da suíte Nexon e título de aba do Opera Hub."""

import base64
from io import BytesIO
import unittest
from pathlib import Path

from PIL import Image, ImageDraw
import app as opera

BASE = Path(__file__).resolve().parents[1]


class BrowserIdentityTests(unittest.TestCase):
    def setUp(self):
        opera.app.config["TESTING"] = True
        self.client = opera.app.test_client()

    def test_all_pages_share_optical_favicon_revision(self):
        for page in ("login.html", "index.html", "config.html", "administracao.html"):
            html = (BASE / "templates" / page).read_text()
            self.assertIn("style='optical93-v1'", html)

    def test_login_title_is_uppercase(self):
        response = self.client.get(
            "/login",
            headers={"Host": "demo.operahub.nexonlabs.com.br"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<title>OPERA HUB | Acesso</title>", response.data)

    def test_favicon_normalizes_transparent_symbol_without_distortion(self):
        original = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
        ImageDraw.Draw(original).rectangle((200, 100, 400, 500), fill="#FFD020")
        buf = BytesIO()
        original.save(buf, format="PNG")
        data = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        mime, raw = opera.normalized_favicon_asset(data)
        self.assertEqual(mime, "image/png")
        with Image.open(BytesIO(raw)) as icon:
            self.assertEqual(icon.size, (512, 512))
            bounds = icon.getchannel("A").getbbox()
            self.assertEqual(bounds[3] - bounds[1], 476)
            self.assertLessEqual(bounds[2] - bounds[0], 239)

    def test_favicon_does_not_change_opaque_brand_color(self):
        source = Image.new("RGB", (400, 400), "#182d4e")
        buf = BytesIO()
        source.save(buf, format="PNG")
        data = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        mime, raw = opera.normalized_favicon_asset(data)
        self.assertEqual(mime, "image/png")
        with Image.open(BytesIO(raw)) as icon:
            self.assertEqual(icon.size, (512, 512))
            self.assertEqual(icon.getpixel((256, 256))[:3], (24, 45, 78))


if __name__ == "__main__":
    unittest.main()
