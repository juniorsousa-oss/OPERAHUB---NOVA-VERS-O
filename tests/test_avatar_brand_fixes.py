"""Regressão do upload de avatar e padrão de marca institucional Opera Hub."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class OperaBrandAvatarTests(unittest.TestCase):
    def test_avatar_upload_ignores_required_fields_from_other_tabs(self):
        page=(ROOT/"templates/config.html").read_text(encoding="utf-8")
        server=(ROOT/"app.py").read_text(encoding="utf-8")
        self.assertIn('HTMLFormElement.prototype.submit.call(form)',page)
        self.assertIn('name="user_avatar_target"',page)
        self.assertIn('name="user_avatar_',page)
        self.assertIn('enctype="multipart/form-data"',page)
        self.assertIn('RUNTIME_CACHE.pop(f"users:{organization_id}"',server)
        self.assertIn('RUNTIME_CACHE.pop(f"asset:{organization_id}:user_avatar:{target_user_id}"',server)
        self.assertIn('session["user_avatar_version"] = str(time.time_ns())',server)
        self.assertIn("current_user.get('avatar_version', 'initial')",page)

    def test_monochrome_assets_login_and_footer(self):
        login=(ROOT/"templates/login.html").read_text(encoding="utf-8")
        home=(ROOT/"templates/index.html").read_text(encoding="utf-8")
        for html in (login,home):
            self.assertIn('nexon-monochrome-dark.svg',html)
            self.assertIn("brand-refinements.css",html)
        self.assertIn("brand-refinements.css",(ROOT/"templates/config.html").read_text(encoding="utf-8"))
        assert (ROOT/"static/nexon-monochrome-dark.svg").exists()
        assert (ROOT/"static/nexon-monochrome-light.svg").exists()
        self.assertIn("max-height:76px",(ROOT/"static/brand-refinements.css").read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
