"""Assinatura institucional: normalização de imagem e posição responsiva."""
import base64
from io import BytesIO
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

import app as opera

BASE = Path(__file__).resolve().parents[1]


class InstitutionalLogoScaleTests(unittest.TestCase):
    def test_login_signature_occupies_right_hand_column(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn(".login-page .login-security-note{", css)
        self.assertIn("grid-template-columns:minmax(0,1fr) 144px;", css)
        self.assertIn("justify-content:flex-end;", css)
        self.assertIn("width:144px;", css)
        self.assertIn("max-height:36px;", css)
        self.assertIn("object-fit:contain;", css)
        self.assertIn("height:auto;", css)

    def test_home_footer_logo_is_centered_without_stretching(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn(".home-page .opera-brand-footer img.nexon-mono-signature{", css)
        self.assertIn("width:min(168px,65vw);", css)
        self.assertIn("max-height:43px;", css)
        self.assertIn("height:auto;", css)
        self.assertIn("justify-content:center;", css)

    def test_mobile_uses_deliberate_centered_stack(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn("@media(max-width:560px)", css)
        self.assertIn("grid-template-columns:minmax(0,1fr);", css)
        self.assertIn("justify-items:center;", css)
        self.assertIn("width:146px;", css)
        self.assertIn("width:164px;", css)

    def test_css_and_asset_version_for_all_surfaces(self):
        for page in ("index.html", "login.html", "config.html"):
            html = (BASE / "templates" / page).read_text()
            expected_cache_key = (
                "institutional-desktop-axora-v1"
                if page == "login.html"
                else "institutional-crop-contextual-v4"
            )
            self.assertIn(expected_cache_key, html)
            self.assertIn("presentation='trim-v2'", html)

    def test_same_tenant_asset_is_used_in_login_and_home(self):
        for page in ("index.html", "login.html"):
            html = (BASE / "templates" / page).read_text()
            self.assertIn("institutional_logo_asset", html)
        self.assertIn('width="144" height="36"', (BASE / "templates/login.html").read_text())
        self.assertIn('width="168" height="43"', (BASE / "templates/index.html").read_text())

    def test_transparent_390x260_logo_gets_visible_horizontal_crop(self):
        original = Image.new("RGBA", (390, 260), (0, 0, 0, 0))
        brush = ImageDraw.Draw(original)
        brush.rounded_rectangle((65, 105, 325, 154), radius=7, fill=(35, 52, 79, 255))
        raw = BytesIO()
        original.save(raw, format="WEBP", lossless=True)
        data = "data:image/webp;base64," + base64.b64encode(raw.getvalue()).decode()
        with opera.app.test_request_context("/assets/institutional-logo"):
            response = opera.institutional_signature_response(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/webp")
        response.direct_passthrough = False
        with Image.open(BytesIO(response.get_data())) as cropped:
            self.assertGreater(cropped.width/cropped.height, 4)
            self.assertLess(cropped.width, original.width)
            self.assertLess(cropped.height, original.height)
            self.assertGreater(cropped.getchannel("A").getbbox()[2], 200)

    def test_solid_background_is_not_artificially_cropped(self):
        raw=BytesIO()
        Image.new("RGB",(390,260),"white").save(raw,format="JPEG")
        data="data:image/jpeg;base64," + base64.b64encode(raw.getvalue()).decode()
        with opera.app.test_request_context("/assets/institutional-logo"):
            response=opera.institutional_signature_response(data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,"image/jpeg")

    def test_empty_image_returns_none_to_enable_default_fallback(self):
        with opera.app.test_request_context("/assets/institutional-logo"):
            self.assertIsNone(opera.institutional_signature_response(""))


if __name__=="__main__":
    unittest.main()
