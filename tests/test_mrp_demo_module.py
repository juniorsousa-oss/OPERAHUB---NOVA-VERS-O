import unittest
from unittest.mock import patch

import app as opera
import mrp_demo_data

HOST_DEMO = {"Host": "demo.operahub.nexonlabs.com.br"}
HOST_SETTA = {"Host": "setta.operahub.nexonlabs.com.br"}

class MrpDemoModuleTests(unittest.TestCase):
    def setUp(self):
        self.client=opera.app.test_client()
        self.demo=patch.object(opera,"OPERAHUB_DEFAULT_ORG","opera-hub-demo")
        self.demo.start()
        self.addCleanup(self.demo.stop)
        self.config=patch.dict(opera.app.config,{"TESTING":True,"MRP_DEMO_ENABLED":True})
        self.config.start()
        self.addCleanup(self.config.stop)

    def login(self,role="user"):
        with self.client.session_transaction(headers=HOST_DEMO) as s:
            s.update(user_id="demo-test", username="tester", user_name="Usuário DEMO",
                     user_role=role, organization_slug="opera-hub-demo", organization_id=2,
                     organization_name="Opera Hub", organization_mode="demo")

    def test_disabled_by_default_or_client_deploy(self):
        self.login()
        with patch.dict(opera.app.config,{"MRP_DEMO_ENABLED":False}):
            self.assertEqual(self.client.get("/mrp",headers=HOST_DEMO).status_code,404)
        with patch.object(opera,"OPERAHUB_DEFAULT_ORG","setta"):
            self.assertEqual(self.client.get("/mrp/api/materials",headers=HOST_DEMO).status_code,404)
        self.assertEqual(self.client.get("/mrp/api/materials",headers=HOST_SETTA).status_code,404)

    def test_requires_hub_session(self):
        view=self.client.get("/mrp",headers=HOST_DEMO)
        self.assertEqual(view.status_code,302)
        self.assertIn("/login",view.location)
        self.assertEqual(self.client.get("/mrp/api/materials",headers=HOST_DEMO).status_code,401)

    def test_all_authenticated_demo_roles_are_read_only(self):
        for role in ("admin","user","operador","consulta"):
            with self.subTest(role=role):
                self.login(role)
                r=self.client.get("/mrp/api/materials",headers=HOST_DEMO)
                self.assertEqual(r.status_code,200)
                self.assertTrue(r.json["demo"])
                self.assertIn("no-store",r.headers["Cache-Control"])
                self.assertEqual(self.client.post("/mrp/api/materials",headers=HOST_DEMO).status_code,405)

    def test_pagination_search_and_detail(self):
        self.login()
        base="/mrp/api/materials"
        one=self.client.get(base,headers=HOST_DEMO).json
        two=self.client.get(base+"?page=2",headers=HOST_DEMO).json
        self.assertEqual(one["pages"],(len(mrp_demo_data.MATERIALS)+9)//10)
        self.assertEqual(two["page"],2)
        self.assertFalse({r["codigo"] for r in one["rows"]}&{r["codigo"] for r in two["rows"]})
        hit=self.client.get(base+"?q=rele&status=no_prazo",headers=HOST_DEMO).json
        self.assertEqual(hit["total"],3)
        code=hit["rows"][0]["codigo"]
        detail=self.client.get(base+"/"+code,headers=HOST_DEMO).json
        self.assertEqual(detail["codigo"],code)
        self.assertEqual(sum(x["quantidade"] for x in detail["necessidades"]),detail["demanda"])
        self.assertEqual(self.client.get(base+"/inexistente",headers=HOST_DEMO).status_code,404)
        self.assertEqual(self.client.get(base+"?page=0",headers=HOST_DEMO).status_code,400)
        self.assertEqual(self.client.get(base+"?page=x",headers=HOST_DEMO).status_code,400)
        self.assertEqual(len(mrp_demo_data.BY_CODE),len(mrp_demo_data.MATERIALS))

    def test_feature_visibility_is_respected(self):
        self.login()
        base=opera.load_bootstrap("opera-hub-demo")
        with patch.object(opera,"load_bootstrap",return_value={**base,"module_access":{"mrp-demo":{"enabled":False}}}):
            self.assertEqual(self.client.get("/mrp/api/materials",headers=HOST_DEMO).status_code,404)
