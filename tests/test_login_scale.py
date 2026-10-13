"""Regressão: login desktop proporcional ao AXORA sem impactar mobile."""

import unittest
from app import app


class OperaLoginScaleTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_login_assets_updated_for_cache_refresh(self):
        for host in (
            "demo.operahub.nexonlabs.com.br",
            "setta.operahub.nexonlabs.com.br",
        ):
            with self.subTest(host=host):
                result = self.client.get("/login", headers={"Host": host})
                self.assertEqual(result.status_code, 200)
                html = result.get_data(as_text=True)
                self.assertIn("opera-login-ambient-nexon-v4", html)
                self.assertIn("institutional-desktop-axora-v1", html)
                self.assertIn('class="login-shell"', html)
                self.assertIn('name="password"', html)

    def test_desktop_card_does_not_use_zoom_or_scale(self):
        response = self.client.get("/static/premium.css")
        self.assertEqual(response.status_code, 200)
        css = response.get_data(as_text=True)
        self.assertIn("--opera-login-width:960px", css)
        self.assertIn("@media (min-width:861px)", css)
        self.assertIn("height:min(550px,calc(100dvh - 50px))", css)
        self.assertIn("height:min(510px,calc(100dvh - 20px))", css)
        self.assertIn("width:min(960px,100%)", css)
        self.assertIn("font-size:33px", css)
        self.assertIn("font-size:27px", css)
        self.assertIn("height:45px", css)
        self.assertIn("@media (max-width:600px)", css)

    def test_login_easter_egg_is_soft_and_non_repeating(self):
        response = self.client.get("/static/premium.css")
        self.assertEqual(response.status_code, 200)
        css = response.get_data(as_text=True)
        desktop = css.split("/* Login — atmosfera institucional exclusiva", 1)[1].split(".login-page .login-shell{", 1)[0]
        self.assertIn("body.login-page::before", desktop)
        self.assertIn("background-repeat:no-repeat", desktop)
        self.assertIn("background-image:url('/static/opera-login-atmosphere-v2.svg')", desktop)
        self.assertIn("background-size:cover", desktop)
        self.assertIn("opacity:1", desktop)
        self.assertIn("background-image:url('/static/nexon-connections.svg')", css)
        self.assertNotIn("center/560px auto repeat", desktop)
        self.assertEqual(css.count("{"), css.count("}"))
        artwork = self.client.get("/static/opera-login-atmosphere-v2.svg")
        self.assertEqual(artwork.status_code, 200)
        svg = artwork.get_data(as_text=True)
        self.assertIn('viewBox="0 0 1672 941"', svg)
        self.assertIn('id="amberGlow"', svg)
        self.assertIn('id="blueGlow"', svg)
        self.assertIn('</svg>', svg)

    def test_brand_keeps_aspect_ratio_and_mobile_breakpoints(self):
        css = self.client.get("/static/brand-refinements.css")
        self.assertEqual(css.status_code, 200)
        body = css.get_data(as_text=True)
        self.assertIn("object-fit:contain", body)
        self.assertIn("@media(max-width:560px)", body)
        self.assertIn("@media (min-width:861px)", body)
        self.assertIn("max-height:68px", body)


if __name__ == "__main__":
    unittest.main()
