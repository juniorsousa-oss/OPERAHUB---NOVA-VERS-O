"""Marca Nexon Labs compartilhada: edição exclusiva da Base/Demo."""
from pathlib import Path
import io
from unittest import TestCase
from unittest.mock import patch
from PIL import Image
import app as opera

BASE=Path(__file__).resolve().parents[1]
DEMO={"Host":"demo.operahub.nexonlabs.com.br"}
SETTA={"Host":"setta.operahub.nexonlabs.com.br"}


def bootstrap_for(slug):
    is_base=slug=="opera-hub-demo"
    return {
        "organization":{
            "id":2 if is_base else 1,
            "slug":slug,
            "name":"Opera Hub" if is_base else "Setta",
            "mode":"demo" if is_base else "client"
        },
        "settings":dict(opera.DEFAULT_SETTINGS),
        "nav":[],
        "applications":[],
        "has_users":True,
        "module_access":{},
    }


class GlobalInstitutionalBrandTests(TestCase):
    def setUp(self):
        opera.app.config["TESTING"]=True
        self.client=opera.app.test_client()
        opera.RUNTIME_CACHE.clear()

    def signin(self,slug):
        host=DEMO if slug=="opera-hub-demo" else SETTA
        is_base=slug=="opera-hub-demo"
        with self.client.session_transaction(headers=host) as session:
            session["user_id"]="admin-test-"+slug
            session["username"]="admin"
            session["user_name"]="Administrador"
            session["user_role"]="admin"
            session["organization_slug"]=slug
            session["organization_mode"]="demo" if is_base else "client"
            session["organization_name"]="Opera Hub" if is_base else "Setta"
            session["organization_id"]=2 if is_base else 1
            session["platform_admin_csrf"]="example-csrf"

    def test_client_admin_cannot_view_brand_edit_option(self):
        self.signin("setta")
        with patch.object(opera,"load_bootstrap",return_value=bootstrap_for("setta")), \
             patch.object(opera,"load_users",return_value=[]), \
             patch.object(opera,"asset_data",return_value=""):
            response=self.client.get("/configuracoes",headers=SETTA)
        self.assertEqual(response.status_code,200)
        page=response.get_data(as_text=True)
        self.assertNotIn('id="institutionalBrandSettings"',page)
        self.assertNotIn('name="institutional_brand_upload"',page)
        self.assertNotIn('value="save_institutional_brand"',page)
        # Cliente continua podendo configurar sua identidade própria.
        self.assertIn('name="logo_upload"',page)

    def test_base_platform_admin_can_view_brand_edit_option(self):
        self.signin("opera-hub-demo")
        with patch.object(opera,"load_bootstrap",return_value=bootstrap_for("opera-hub-demo")), \
             patch.object(opera,"load_users",return_value=[]), \
             patch.object(opera,"asset_data",return_value=""):
            response=self.client.get("/configuracoes",headers=DEMO)
        self.assertEqual(response.status_code,200)
        page=response.get_data(as_text=True)
        self.assertIn('id="institutionalBrandSettings"',page)
        self.assertIn('name="institutional_brand_upload"',page)
        self.assertIn("todos os clientes",page)

    def test_client_admin_direct_post_cannot_modify_institutional_brand(self):
        self.signin("setta")
        with patch.object(opera,"load_bootstrap",return_value=bootstrap_for("setta")), \
             patch.object(opera,"sb_rpc") as rpc:
            response=self.client.post("/configuracoes",headers=SETTA,data={
                "config_action":"save_institutional_brand",
                "institutional_csrf_token":"example-csrf",
                "remove_institutional_brand":"on",
            })
        self.assertEqual(response.status_code,403)
        rpc.assert_not_called()

    def test_base_admin_can_still_update_global_asset(self):
        self.signin("opera-hub-demo")
        data=io.BytesIO()
        Image.new("RGBA",(260,80),(20,90,120,255)).save(data,format="PNG")
        writes=[]
        def capture(name,params):
            writes.append((name,params))
        with patch.object(opera,"load_bootstrap",return_value=bootstrap_for("opera-hub-demo")), \
             patch.object(opera,"sb_rpc",side_effect=capture):
            response=self.client.post("/configuracoes",headers=DEMO,data={
                "config_action":"save_institutional_brand",
                "institutional_csrf_token":"example-csrf",
                "institutional_brand_upload":(data,"brand.png"),
            },content_type="multipart/form-data")
        self.assertEqual(response.status_code,302)
        self.assertEqual(len(writes),1)
        self.assertEqual(writes[0][0],"operahub_set_institutional_brand_v1")
        self.assertEqual(writes[0][1]["p_organization_id"],2)

    def test_asset_cache_refresh_is_fast_and_browser_must_revalidate(self):
        data="data:image/png;base64,iVBORw0KGgo="
        with patch.object(opera,"asset_data",return_value=data):
            for host in (DEMO,SETTA):
                response=self.client.get("/assets/institutional-logo",headers=host)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.headers["Cache-Control"],
                                 "public, max-age=60, must-revalidate")
        source=(BASE/"app.py").read_text()
        self.assertIn('asset_ttl = 60 if asset_type == "institutional_logo" else ASSET_DATA_TTL',source)

    def test_database_migration_enforces_shared_base_asset_and_denies_client_updates(self):
        sql=(BASE/"migrations/20261010_global_institutional_brand.sql").read_text()
        self.assertIn("when 'institutional_logo' then",sql)
        self.assertIn("o.slug='opera-hub-demo'",sql)
        self.assertIn("o.mode='demo'",sql)
        self.assertIn("raise exception 'institutional_brand_read_only'",sql)
        self.assertIn("p_organization_id bigint",sql)
        self.assertNotIn("delete from public.operahub_tenant_settings",sql.lower())

    def test_other_brand_assets_remain_per_tenant(self):
        sql=(BASE/"migrations/20261010_global_institutional_brand.sql").read_text()
        for asset in ("'logo'","'favicon'","'hero'","'login'","'app_image'"):
            self.assertIn("when "+asset+" then",sql)
        self.assertIn("where organization_id=p_organization_id and id='main'",sql)


if __name__=="__main__":
    import unittest
    unittest.main()
