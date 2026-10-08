import unittest
from unittest.mock import patch

import app as opera


HOST_DEMO = {"Host": "demo.operahub.nexonlabs.com.br"}
HOST_SETTA = {"Host": "setta.operahub.nexonlabs.com.br"}

OVERVIEW = {
    "organizations": [
        {
            "id": 2,
            "name": "Opera Hub",
            "slug": "opera-hub-demo",
            "mode": "demo",
            "active": True,
            "modules": [
                {
                    "key": "planejamento",
                    "name": "PLANEJAMENTO",
                    "description": "Planejamento operacional",
                    "status": "development",
                    "sort_order": 1,
                    "enabled": True,
                    "show_home": True,
                    "show_menu": True,
                    "nav_key": "planejamento",
                }
            ],
        },
        {
            "id": 1,
            "name": "Setta",
            "slug": "setta",
            "mode": "client",
            "active": True,
            "modules": [],
        },
    ]
}


class OperaHubAdminTests(unittest.TestCase):
    def setUp(self):
        opera.app.config["TESTING"] = True
        self.client = opera.app.test_client()

    def authenticate_demo(self, role="admin"):
        with self.client.session_transaction(headers=HOST_DEMO) as session:
            session["user_id"] = "user-testing"
            session["username"] = "admin"
            session["user_name"] = "Administrador"
            session["user_role"] = role
            session["organization_slug"] = "opera-hub-demo"
            session["organization_mode"] = "demo"
            session["organization_name"] = "Opera Hub"
            session["organization_id"] = 2

    @staticmethod
    def fake_rpc(name, payload):
        if name == "operahub_admin_overview_v1":
            return OVERVIEW
        if name == "operahub_bootstrap_v2":
            return None
        if name == "operahub_admin_set_module_v1":
            return None
        raise AssertionError(name)

    def test_unlogged_user_cannot_open_admin(self):
        response = self.client.get("/administracao", headers=HOST_DEMO)
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_open_admin(self):
        self.authenticate_demo(role="user")
        response = self.client.get("/administracao", headers=HOST_DEMO)
        self.assertEqual(response.status_code, 403)

    def test_demo_admin_can_access_module_panel(self):
        self.authenticate_demo()
        with patch.object(opera, "sb_rpc", side_effect=self.fake_rpc):
            response = self.client.get("/administracao", headers=HOST_DEMO)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Administra", response.data)
        self.assertIn(b"PLANEJAMENTO", response.data)
        self.assertIn(b"Setta", response.data)

    def test_demo_admin_cannot_administer_from_setta_host(self):
        self.authenticate_demo()
        response = self.client.get("/administracao", headers=HOST_SETTA)
        self.assertEqual(response.status_code, 403)

    def test_csrf_required(self):
        self.authenticate_demo()
        response = self.client.post(
            "/administracao",
            headers=HOST_DEMO,
            data={
                "organization_slug": "setta",
                "module_key": "mrp",
                "enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_module_update_tenant_scoped(self):
        self.authenticate_demo()
        with patch.object(opera, "sb_rpc", side_effect=self.fake_rpc):
            self.client.get("/administracao", headers=HOST_DEMO)
            with self.client.session_transaction(headers=HOST_DEMO) as session:
                csrf = session["platform_admin_csrf"]
            response = self.client.post(
                "/administracao",
                headers=HOST_DEMO,
                data={
                    "csrf_token": csrf,
                    "organization_slug": "setta",
                    "module_key": "mrp",
                    "enabled": "on",
                    "show_home": "on",
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertIn("organization=setta", response.headers["Location"])

    def test_module_visibility_controls_nav_and_cards(self):
        data = {
            "applications": [
                {"key": "estoque", "name": "ESTOQUE"},
                {"key": "indicadores", "name": "INDICADORES"},
            ],
            "nav": [
                {"key": "inicio"},
                {"key": "estoque"},
                {"key": "indicadores"},
            ],
            "module_access": {
                "estoque": {
                    "enabled": False,
                    "show_home": True,
                    "show_menu": True,
                    "nav_key": "estoque",
                },
                "indicadores": {
                    "enabled": True,
                    "show_home": False,
                    "show_menu": True,
                    "nav_key": "indicadores",
                },
            },
        }
        nav, apps = opera.module_visibility(data)
        self.assertEqual([x["key"] for x in apps], [])
        self.assertEqual([x["key"] for x in nav], ["inicio", "indicadores"])


if __name__ == "__main__":
    unittest.main()
