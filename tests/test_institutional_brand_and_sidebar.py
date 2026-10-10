"""Opera Hub: rolagem independente, papel de parede idêntico ao login e marca por tenant."""
import io
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

import app as opera

ROOT=Path(__file__).resolve().parents[1]
DEMO={"Host":"demo.operahub.nexonlabs.com.br"}
SETTA={"Host":"setta.operahub.nexonlabs.com.br"}


class BrandAndSidebarTests(TestCase):
    def setUp(self):
        opera.app.config["TESTING"]=True
        self.client=opera.app.test_client()

    def authenticate(self):
        with self.client.session_transaction(headers=DEMO) as session:
            session["user_id"]="test-brand-administrator"
            session["username"]="admin"
            session["user_name"]="Administrador"
            session["user_role"]="admin"
            session["organization_slug"]="opera-hub-demo"
            session["organization_mode"]="demo"
            session["organization_name"]="Opera Hub"
            session["organization_id"]=2

    def test_scrollable_sidebar_groups_do_not_shrink(self):
        css=(ROOT/"static/exterior-frame.css").read_text()
        self.assertIn("overflow-y:auto",css)
        self.assertIn("scrollbar-gutter:stable",css)
        self.assertIn(".home-page .side-nav > .nav-primary",css)
        self.assertIn(".home-page .side-nav > .nav-secondary",css)
        self.assertIn("flex-shrink:0",css)
        self.assertIn("::-webkit-scrollbar",css)
        self.assertIn("@media(max-width:860px)",css)
        self.assertEqual(css.count("{"),css.count("}"))

    def test_external_wallpaper_exactly_matches_login_color_and_motif(self):
        premium=(ROOT/"static/premium.css").read_text()
        exterior=(ROOT/"static/exterior-frame.css").read_text()
        for color in (
            "rgba(255,204,88,.38)",
            "rgba(235,165,36,.27)",
            "rgba(70,49,22,.22)",
            "#46341b 0%,#312b25 47%,#192a3d 100%",
        ):
            self.assertIn(color,premium)
            self.assertIn(color,exterior)
        self.assertIn("background:url(\"/static/nexon-connections.svg\") center/560px auto repeat",exterior)
        self.assertIn("opacity:.12",exterior)
        self.assertIn("pointer-events:none",exterior)
        self.assertIn("isolation:isolate",exterior)
        self.assertIn("position:relative",exterior)

    def test_same_institutional_asset_used_on_both_pages(self):
        for path in ("templates/login.html","templates/index.html"):
            html=(ROOT/path).read_text()
            self.assertIn("url_for('institutional_logo_asset', v=settings['updated_at'], presentation='trim-v2')",html)
            self.assertNotIn("filename='nexon-monochrome-dark.svg'",html)
        config=(ROOT/"templates/config.html").read_text()
        self.assertIn("id=\"institutionalBrandSettings\"",config)
        self.assertIn('name="institutional_brand_upload"',config)
        self.assertIn('name="remove_institutional_brand"',config)
        self.assertIn('value="save_institutional_brand"',config)
        self.assertIn('type="submit" formnovalidate',config)
        self.assertIn('name="institutional_csrf_token"',config)
        self.assertIn("has_institutional_brand",config)

    def test_route_returns_asset_for_resolved_tenant(self):
        def data_for_tenant(asset_type,key=None):
            self.assertEqual(asset_type,"institutional_logo")
            self.assertEqual(opera.active_organization_slug(),"opera-hub-demo")
            return "data:image/png;base64,iVBORw0KGgo="
        with patch.object(opera,"asset_data",side_effect=data_for_tenant):
            r=self.client.get("/assets/institutional-logo?v=demo",headers=DEMO)
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.headers["Content-Type"].startswith("image/png"))
        with patch.object(opera,"asset_data",return_value=""):
            r=self.client.get("/assets/institutional-logo",headers=SETTA)
        self.assertEqual(r.status_code,302)
        self.assertIn("nexon-monochrome-dark.svg",r.headers["Location"])

    def test_not_authenticated_cannot_update_brand(self):
        r=self.client.post("/configuracoes",data={"config_action":"save_institutional_brand"},headers=DEMO)
        self.assertEqual(r.status_code,302)
        self.assertIn("/login",r.headers["Location"])

    def test_authenticated_admin_can_upload_for_demo_tenant_only(self):
        self.authenticate()
        with self.client.session_transaction(headers=DEMO) as session:
            session["platform_admin_csrf"]="test-csrf-institutional"
        payload=io.BytesIO()
        Image.new("RGBA",(300,100),(20,60,90,255)).save(payload,"PNG")
        writes=[]
        def fake_rpc(name,vals):
            writes.append((name,vals))
            return None
        with patch.object(opera,"sb_rpc",side_effect=fake_rpc), patch.object(opera,"load_bootstrap",return_value={
            "organization":{"id":2,"slug":"opera-hub-demo","name":"Opera Hub","mode":"demo"},
            "settings":dict(opera.DEFAULT_SETTINGS),"nav":[],"applications":[],"has_users":True
        }):
            r=self.client.post("/configuracoes",data={
                "config_action":"save_institutional_brand",
                "institutional_csrf_token":"test-csrf-institutional",
                "institutional_brand_upload":(payload,"brand.png"),
            },headers=DEMO,content_type="multipart/form-data")
        self.assertEqual(r.status_code,302)
        self.assertEqual(len(writes),1)
        self.assertEqual(writes[0][0],"operahub_set_institutional_brand_v1")
        self.assertEqual(writes[0][1]["p_organization_id"],2)
        self.assertTrue(writes[0][1]["p_image_data"].startswith("data:image/"))

    def test_csrf_rejects_unauthorized_post(self):
        self.authenticate()
        r=self.client.post("/configuracoes",data={
            "config_action":"save_institutional_brand","institutional_csrf_token":"incorrect",
        },headers=DEMO)
        self.assertEqual(r.status_code,400)

    def test_save_without_upload_or_reset_is_rejected(self):
        self.authenticate()
        with self.client.session_transaction(headers=DEMO) as session:
            session["platform_admin_csrf"]="test-csrf-institutional"
        with patch.object(opera,"load_bootstrap",return_value={
            "organization":{"id":2,"slug":"opera-hub-demo","name":"Opera Hub","mode":"demo"},
            "settings":dict(opera.DEFAULT_SETTINGS),"nav":[],"applications":[],"has_users":True
        }), patch.object(opera,"sb_rpc") as rpc, patch.object(opera,"load_users",return_value=[]), patch.object(opera,"asset_data",return_value=""):
            r=self.client.post("/configuracoes",data={
                "config_action":"save_institutional_brand",
                "institutional_csrf_token":"test-csrf-institutional",
            },headers=DEMO)
            self.assertEqual(r.status_code,200)
            rpc.assert_not_called()
