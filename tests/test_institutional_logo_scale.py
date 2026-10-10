"""Evita regressão no tamanho da assinatura institucional do Opera Hub."""
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class InstitutionalLogoScaleTests(unittest.TestCase):
    def test_desktop_login_footer_logo_scale(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn(".login-page .login-security-note .nexon-mono-signature{", css)
        self.assertIn("width:170px;", css)
        self.assertIn("max-height:40px;", css)
        self.assertIn("object-fit:contain;", css)
        self.assertIn("flex:0 0 auto;", css)

    def test_home_footer_logo_scale_and_proportions(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn(".home-page .opera-brand-footer img.nexon-mono-signature{", css)
        self.assertIn("width:180px;", css)
        self.assertIn("max-height:42px;", css)
        self.assertIn("height:auto;", css)
        self.assertIn("object-position:center;", css)

    def test_mobile_rules_prevent_overflow_without_shrinking_too_far(self):
        css = (BASE / "static/brand-refinements.css").read_text()
        self.assertIn("@media(max-width:560px)", css)
        self.assertIn("width:148px;max-height:36px", css)
        self.assertIn("width:165px;max-width:80vw;max-height:39px", css)
        self.assertIn("max-width:min(148px,44vw)", css)

    def test_cache_buster_on_login_home_and_settings(self):
        for page in ("index.html", "login.html", "config.html"):
            html = (BASE / "templates" / page).read_text()
            self.assertIn("institutional-scale-20261010-v3", html)
            self.assertIn("brand-refinements.css", html)

    def test_custom_image_endpoint_is_preserved(self):
        for page in ("index.html", "login.html"):
            html = (BASE / "templates" / page).read_text()
            self.assertIn("institutional_logo_asset", html)
        self.assertIn('width="170" height="40"', (BASE / "templates/login.html").read_text())
        self.assertIn('width="180" height="42"', (BASE / "templates/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
