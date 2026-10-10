"""Regressão da moldura Opera Hub (desktop + mobile), sem alterar módulos."""
from pathlib import Path
import unittest

from app import app

ROOT=Path(__file__).resolve().parents[1]
SETTA={"Host":"setta.operahub.nexonlabs.com.br"}


class ExteriorFrameTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"]=True
        self.client=app.test_client()

    def test_new_css_is_served(self):
        response=self.client.get("/static/exterior-frame.css")
        self.assertEqual(response.status_code,200)
        css=response.get_data(as_text=True)
        self.assertIn('body.home-page{',css)
        self.assertIn('url("/static/nexon-connections.svg")',css)
        self.assertIn("linear-gradient(145deg,#46341b 0%,#312b25 47%,#192a3d 100%)",css)
        self.assertIn("center/560px auto repeat",css)
        self.assertIn("height:calc(100dvh - (2 * var(--opera-frame-gap)))",css)
        self.assertIn("overflow:hidden",css)
        self.assertIn("overflow-y:auto",css)
        self.assertIn("@media(max-width:860px)",css)
        self.assertIn("@media(max-width:600px)",css)
        self.assertIn("background-attachment:scroll",css)
        self.assertIn("overflow:visible",css)
        self.assertEqual(css.count("{"),css.count("}"))

    def test_css_loaded_after_premium_on_main_config_and_admin(self):
        for path in ["index.html","config.html","administracao.html"]:
            html=(ROOT/"templates"/path).read_text()
            self.assertEqual(html.count("exterior-frame.css"),1,path)
            self.assertGreater(html.index("exterior-frame.css"),html.index("premium.css"),path)
            self.assertIn("opera-login-wallpaper-navfix-20261010-v2",html)

    def test_original_login_remains_untouched(self):
        login=(ROOT/"templates/login.html").read_text()
        self.assertNotIn("exterior-frame.css",login)
        self.assertIn('class="login-shell"',login)
        self.assertIn('name="password"',login)

    def test_client_home_retains_logo_banner_and_modules(self):
        response=self.client.get("/",headers=SETTA)
        self.assertEqual(response.status_code,200)
        html=response.get_data(as_text=True)
        self.assertIn("exterior-frame.css",html)
        self.assertIn('class="app-shell"',html)
        self.assertIn('id="sideNav"',html)
        self.assertIn('id="mobileMenu"',html)
        self.assertIn('id="appsGrid"',html)
        self.assertIn('class="hero"',html)
        self.assertIn('class="nav-overlay"',html)
        self.assertIn("nexon-connections.svg",(ROOT/"static/exterior-frame.css").read_text())

    def test_tenant_agnostic_styles_are_presentation_only(self):
        css=(ROOT/"static/exterior-frame.css").read_text()
        self.assertNotIn("fetch(",css)
        self.assertNotIn("url('http",css)
        self.assertNotIn("https://",css)
        self.assertNotIn("opacity:0",css)
        self.assertIn(".home-page .side-nav",css)
        self.assertIn(".home-page .top-bar",css)
        self.assertIn(".home-page .main-area",css)


if __name__=="__main__":
    unittest.main()
