"""Verificações de regressão visual e de isolamento de tenant.

Não dependem de credenciais reais e preservam os fluxos de login existentes.
"""
import unittest
from app import app


DEMO = {"Host": "demo.operahub.nexonlabs.com.br"}
SETTA = {"Host": "setta.operahub.nexonlabs.com.br"}


class OperaPremiumLayoutTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_demo_login_has_premium_layout_and_username_login(self):
        response = self.client.get("/login", headers=DEMO)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("premium.css", html)
        self.assertIn('class="login-shell"', html)
        self.assertIn('name="login"', html)
        self.assertIn('name="password"', html)
        self.assertIn('id="show-password"', html)
        self.assertIn("Mostrar senha digitada", html)
        self.assertIn("OPERA HUB • BASE / DEMO", html)

    def test_setta_login_keeps_username_or_email(self):
        response = self.client.get("/login", headers=SETTA)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("premium.css", html)
        self.assertIn("Usuário ou e-mail", html)
        self.assertIn('name="password"', html)

    def test_setta_home_preserves_modules_and_visual_assets(self):
        response = self.client.get("/", headers=SETTA)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("premium.css", html)
        self.assertIn('id="appsGrid"', html)
        self.assertIn('class="hero"', html)
        self.assertIn('id="sideNav"', html)

    def test_css_asset_is_served_and_contains_mobile_rules(self):
        response = self.client.get("/static/premium.css")
        self.assertEqual(response.status_code, 200)
        css = response.get_data(as_text=True)
        self.assertIn("body.login-page", css)
        self.assertIn("@media (max-width:600px)", css)
        self.assertIn(".opera-admin-page .oa-section", css)
        self.assertIn(".home-page .app-card", css)


if __name__ == "__main__":
    unittest.main()
