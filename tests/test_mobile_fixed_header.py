"""Opera Hub mobile: cabeçalho permanece visível enquanto cards rolam."""

from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def test_fixed_header_scroll_region_and_drawer_layering():
    html = (BASE / "templates/index.html").read_text(encoding="utf-8")
    css = (BASE / "static/mobile-fixed-header.css").read_text(encoding="utf-8")
    assert html.count('id="main-scroll"') == 1
    assert html.count('id="navOverlay"') == 1
    assert html.index('class="top-bar"') < html.index('id="main-scroll"') < html.index('class="hero"')
    assert html.index('id="main-scroll"') < html.index('class="opera-brand-footer"')
    assert html.index('mobile-fixed-header.css') > html.index('exterior-frame.css')
    assert "@media (max-width:860px)" in css
    assert ".home-page .main-area" in css
    assert "flex-direction:column" in css
    assert ".home-page .top-bar" in css
    assert "position:relative" in css
    assert "flex:0 0 auto" in css
    assert ".home-page .main-scroll" in css
    assert "overflow-y:auto" in css
    assert "overscroll-behavior-y:contain" in css
    assert ".home-page .side-nav" in css
    assert ".home-page .nav-overlay.show" in css
    assert css.count("{") == css.count("}")


def test_fixed_header_only_applies_to_authenticated_home_mobile():
    css = (BASE / "static/mobile-fixed-header.css").read_text(encoding="utf-8")
    assert "body.home-page" in css
    assert "body.login-page" not in css
    assert "background-image:" not in css
    assert "fetch(" not in css
    assert "max-width:860px" in css
