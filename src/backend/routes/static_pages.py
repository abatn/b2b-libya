"""
Libya B2B Platform - Static Pages (Jinja2 Templates)
Migrated from src/frontend/server.py — single FastAPI process.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["static"])

# Paths
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_FRONTEND_DIR = _BACKEND_DIR.parent / "frontend"
_TEMPLATES_DIR = _FRONTEND_DIR / "templates"
_LOCALES_DIR = _FRONTEND_DIR / "locales"
_STATIC_DIR = _FRONTEND_DIR / "static"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# ============================================================
# Helpers
# ============================================================


def _load_locale(lang: str) -> dict:
    path = _LOCALES_DIR / f"{lang}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _rewrite_nav_links(content: str, lang: str) -> str:
    """Rewrite navigation links based on language (ported from server.py)."""

    def _rewrite_lang_switch(match):
        href = match.group(1)
        attrs = match.group(2)
        if href.startswith("/ar"):
            return match.group(0)
        if lang == "ar":
            return match.group(0)
        if href == "/":
            return f'href="/ar/"{attrs}'
        return f'href="/ar{href}"{attrs}'

    content = re.sub(
        r'href="(/[^"]*?)"(\s+class="lang-btn(?:-top)?"\s+data-lang-switch)',
        _rewrite_lang_switch,
        content,
    )

    if lang == "ar":

        def _add_ar_prefix(match):
            tag = match.group(0)
            href = match.group(1)
            if "lang-btn" in tag or "data-lang-switch" in tag:
                return tag
            if href == "/":
                return tag.replace(href, "/ar/")
            if (
                href.startswith("/")
                and not href.startswith("/ar/")
                and href not in ["/health", "/docs", "/api"]
            ):
                return tag.replace(f'href="{href}"', f'href="/ar{href}"')
            return tag

        content = re.sub(
            r'<a\s[^>]*href="(/[^"]*)"[^>]*>', _add_ar_prefix, content
        )
    else:

        def _remove_ar_prefix(match):
            tag = match.group(0)
            href = match.group(1)
            if "lang-btn" in tag or "data-lang-switch" in tag:
                return tag
            if href.startswith("/ar/"):
                return tag.replace(f'href="{href}"', f'href="{href[3:]}"')
            return tag

        content = re.sub(
            r'<a\s[^>]*href="(/ar/[^"]*)"[^>]*>', _remove_ar_prefix, content
        )

    return content


def _render(template_name: str, lang: str, request: Request) -> HTMLResponse:
    """Render a template with locale injection, nav include, and post-processing."""
    locale = _load_locale(lang)

    tpl_data = locale.get(template_name, {})
    locale["title"] = tpl_data.get(
        "title", locale.get("landing", {}).get("title", "Libya B2B")
    )
    locale["meta_description"] = tpl_data.get(
        "meta_description",
        locale.get("landing", {}).get("meta_description", ""),
    )

    base_url = str(request.base_url).rstrip("/")
    locale["_base"] = "/ar" if lang == "ar" else ""
    locale["_lang_switch"] = "/" if lang == "ar" else "/ar"

    _tpl_to_path = {
        "landing": "",
        "b2b_products": "b2b/products",
        "b2b_suppliers": "b2b/suppliers",
    }
    _path = _tpl_to_path.get(template_name, template_name)
    locale["canonical_url"] = f"{base_url}/{'' if lang == 'en' else 'ar/'}{_path}"
    if lang == "ar":
        locale["hreflang_en"] = f"{base_url}/{_path}"
        locale["hreflang_ar"] = locale["canonical_url"]
    else:
        locale["hreflang_en"] = locale["canonical_url"]
        locale["hreflang_ar"] = f"{base_url}/ar/{_path}"

    # Read template file
    tpl_path = _TEMPLATES_DIR / f"{template_name}.html"
    if not tpl_path.exists():
        return HTMLResponse(f"<h1>Template not found: {template_name}</h1>", status_code=404)

    content = tpl_path.read_text(encoding="utf-8")

    # Inject nav includes
    nav_html_path = _TEMPLATES_DIR / "nav.html"
    nav_css_path = _FRONTEND_DIR / "static" / "nav.css"
    nav_js_path = _FRONTEND_DIR / "static" / "nav.js"
    components_css_path = _FRONTEND_DIR / "static" / "components.css"

    if nav_html_path.exists():
        content = content.replace("<!-- NAV_INCLUDE -->", nav_html_path.read_text(encoding="utf-8"))
    if nav_css_path.exists():
        nav_css = nav_css_path.read_text(encoding="utf-8")
        if components_css_path.exists():
            nav_css += "\n" + components_css_path.read_text(encoding="utf-8")
        content = content.replace("<!-- NAV_CSS_INCLUDE -->", f"<style>{nav_css}</style>")
    if nav_js_path.exists():
        nav_js_tag = '<script src="/static/nav.js"></script>'
        content = content.replace("<!-- NAV_JS_INCLUDE -->", nav_js_tag)

    # Render Jinja2 from the in-memory content (with nav includes already injected)
    jinja_tpl = templates.env.from_string(content)
    html = jinja_tpl.render(**locale)

    # Post-process: rewrite nav links
    html = _rewrite_nav_links(html, lang)

    # Post-process: RTL for Arabic
    if lang == "ar":
        html = html.replace('<html lang="en">', '<html lang="ar" dir="rtl">')
        html = re.sub(r"(body\s*\{[^}]*)(})", r"\1 direction: rtl; }", html)

    return HTMLResponse(content=html)


# ============================================================
# Redirect /ar → /ar/
# ============================================================


@router.get("/ar")
def redirect_ar():
    return RedirectResponse(url="/ar/", status_code=301)


# ============================================================
# Landing pages
# ============================================================


@router.get("/")
def landing_en(request: Request):
    return _render("landing", "en", request)


@router.get("/ar/")
def landing_ar(request: Request):
    return _render("landing", "ar", request)


@router.get("/landing")
def landing_page(request: Request):
    return _render("landing", "en", request)


@router.get("/ar/landing")
def landing_page_ar(request: Request):
    return _render("landing", "ar", request)


# ============================================================
# Products
# ============================================================


@router.get("/products")
def products_page(request: Request):
    return _render("products", "en", request)


# NOTE: /ar/products is an API endpoint (returns JSON), not an HTML page.
# See the API endpoints section at the bottom of this file.


@router.get("/suppliers")
def suppliers_redirect():
    return RedirectResponse(url="/b2b/suppliers", status_code=301)


@router.get("/ar/suppliers")
def suppliers_redirect_ar():
    return RedirectResponse(url="/ar/b2b/suppliers", status_code=301)


# ============================================================
# Cart & Checkout
# ============================================================


@router.get("/cart")
def cart_page(request: Request):
    return _render("cart", "en", request)


@router.get("/ar/cart")
def cart_page_ar(request: Request):
    return _render("cart", "ar", request)


@router.get("/checkout")
def checkout_page(request: Request):
    return _render("checkout", "en", request)


@router.get("/ar/checkout")
def checkout_page_ar(request: Request):
    return _render("checkout", "ar", request)


# ============================================================
# Seller
# ============================================================


@router.get("/seller")
def seller_page(request: Request):
    return _render("seller", "en", request)


@router.get("/ar/seller")
def seller_page_ar(request: Request):
    return _render("seller", "ar", request)


# ============================================================
# Tracking & Buyer
# ============================================================


@router.get("/tracking")
def tracking_page(request: Request):
    return _render("tracking", "en", request)


@router.get("/ar/tracking")
def tracking_page_ar(request: Request):
    return _render("tracking", "ar", request)


@router.get("/buyer")
def buyer_page(request: Request):
    return _render("buyer", "en", request)


@router.get("/ar/buyer")
def buyer_page_ar(request: Request):
    return _render("buyer", "ar", request)


# ============================================================
# B2B pages
# ============================================================


@router.get("/b2b")
def b2b_page(request: Request):
    return _render("b2b", "en", request)


@router.get("/ar/b2b")
def b2b_page_ar(request: Request):
    return _render("b2b", "ar", request)


@router.get("/b2b/products")
def b2b_products_page(request: Request):
    return _render("b2b_products", "en", request)


@router.get("/ar/b2b/products")
def b2b_products_page_ar(request: Request):
    return _render("b2b_products", "ar", request)


@router.get("/b2b/suppliers")
def suppliers_page(request: Request):
    return _render("suppliers", "en", request)


@router.get("/ar/b2b/suppliers")
def suppliers_page_ar(request: Request):
    return _render("suppliers", "ar", request)


@router.get("/b2b/rfq")
def rfq_page(request: Request):
    return _render("rfq", "en", request)


@router.get("/ar/b2b/rfq")
def rfq_page_ar(request: Request):
    return _render("rfq", "ar", request)


@router.get("/b2b/rfq/new")
def rfq_new_page(request: Request):
    return _render("rfq_new", "en", request)


@router.get("/ar/b2b/rfq/new")
def rfq_new_page_ar(request: Request):
    return _render("rfq_new", "ar", request)


@router.get("/b2b/rfq/{rfq_id}")
def rfq_detail_page(request: Request):
    return _render("rfq_detail", "en", request)


@router.get("/ar/b2b/rfq/{rfq_id}")
def rfq_detail_page_ar(request: Request):
    return _render("rfq_detail", "ar", request)


@router.get("/b2b/messages")
def messages_page(request: Request):
    return _render("messages", "en", request)


@router.get("/ar/b2b/messages")
def messages_page_ar(request: Request):
    return _render("messages", "ar", request)


@router.get("/b2b/messages/{conversation_id}")
def conversation_page(request: Request):
    return _render("conversation", "en", request)


@router.get("/ar/b2b/messages/{conversation_id}")
def conversation_page_ar(request: Request):
    return _render("conversation", "ar", request)


# ============================================================
# Product & Supplier Detail
# ============================================================


@router.get("/b2b/products/{product_id}")
def product_detail_page(request: Request):
    return _render("product_detail", "en", request)


@router.get("/ar/b2b/products/{product_id}")
def product_detail_page_ar(request: Request):
    return _render("product_detail", "ar", request)


@router.get("/b2b/suppliers/{supplier_id}")
def supplier_detail_page(request: Request):
    return _render("supplier_detail", "en", request)


@router.get("/ar/b2b/suppliers/{supplier_id}")
def supplier_detail_page_ar(request: Request):
    return _render("supplier_detail", "ar", request)


# ============================================================
# Auth pages
# ============================================================


@router.get("/register")
def register_page(request: Request):
    return _render("register", "en", request)


@router.get("/ar/register")
def register_page_ar(request: Request):
    return _render("register", "ar", request)


@router.get("/login")
def login_page(request: Request):
    return _render("landing", "en", request)


@router.get("/ar/login")
def login_page_ar(request: Request):
    return _render("landing", "ar", request)


@router.get("/welcome")
def welcome_page(request: Request):
    return _render("welcome", "en", request)


@router.get("/ar/welcome")
def welcome_page_ar(request: Request):
    return _render("welcome", "ar", request)


@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return _render("forgot-password", "en", request)


@router.get("/ar/forgot-password")
def forgot_password_page_ar(request: Request):
    return _render("forgot-password", "ar", request)


@router.get("/verify-email")
def verify_email_page(request: Request):
    return _render("verify-email", "en", request)


@router.get("/ar/verify-email")
def verify_email_page_ar(request: Request):
    return _render("verify-email", "ar", request)


@router.get("/2fa")
def two_fa_page(request: Request):
    return _render("2fa", "en", request)


@router.get("/ar/2fa")
def two_fa_page_ar(request: Request):
    return _render("2fa", "ar", request)


# ============================================================
# Escrow pages
# ============================================================


@router.get("/escrow")
def escrow_page(request: Request):
    return _render("escrow", "en", request)


@router.get("/ar/escrow")
def escrow_page_ar(request: Request):
    return _render("escrow", "ar", request)


@router.get("/escrow/admin")
def escrow_admin_page(request: Request):
    return _render("escrow_admin", "en", request)


@router.get("/ar/escrow/admin")
def escrow_admin_page_ar(request: Request):
    return _render("escrow_admin", "ar", request)


# ============================================================
# Guide & Support
# ============================================================


@router.get("/guide")
def guide_page(request: Request):
    return _render("guide", "en", request)


@router.get("/ar/guide")
def guide_page_ar(request: Request):
    return _render("guide", "ar", request)


@router.get("/support")
def support_page(request: Request):
    return _render("support", "en", request)


@router.get("/ar/support")
def support_page_ar(request: Request):
    return _render("support", "ar", request)


@router.get("/import")
def import_page(request: Request):
    return _render("import", "en", request)


@router.get("/ar/import")
def import_page_ar(request: Request):
    return _render("import", "ar", request)


# ============================================================
# Admin pages
# ============================================================


@router.get("/admin/suppliers")
def admin_suppliers_page(request: Request):
    return _render("admin_suppliers", "en", request)


@router.get("/ar/admin/suppliers")
def admin_suppliers_page_ar(request: Request):
    return _render("admin_suppliers", "ar", request)


# ============================================================
# Info pages
# ============================================================


@router.get("/faq")
def faq_page(request: Request):
    return _render("faq", "en", request)


@router.get("/ar/faq")
def faq_page_ar(request: Request):
    return _render("faq", "ar", request)


@router.get("/terms")
def terms_page(request: Request):
    return _render("terms", "en", request)


@router.get("/ar/terms")
def terms_page_ar(request: Request):
    return _render("terms", "ar", request)


@router.get("/privacy")
def privacy_page(request: Request):
    return _render("privacy", "en", request)


@router.get("/ar/privacy")
def privacy_page_ar(request: Request):
    return _render("privacy", "ar", request)


@router.get("/cookie")
def cookie_page(request: Request):
    return _render("cookie", "en", request)


@router.get("/ar/cookie")
def cookie_page_ar(request: Request):
    return _render("cookie", "ar", request)


@router.get("/about")
def about_page(request: Request):
    return _render("about", "en", request)


@router.get("/ar/about")
def about_page_ar(request: Request):
    return _render("about", "ar", request)


@router.get("/careers")
def careers_page(request: Request):
    return _render("careers", "en", request)


@router.get("/ar/careers")
def careers_page_ar(request: Request):
    return _render("careers", "ar", request)


# ============================================================
# SEO: robots.txt, sitemap.xml, manifest.json
# ============================================================


@router.get("/robots.txt")
def robots_txt():
    robots_path = _STATIC_DIR / "robots.txt"
    if robots_path.exists():
        return HTMLResponse(
            content=robots_path.read_text(encoding="utf-8"),
            media_type="text/plain",
        )
    return HTMLResponse(content="User-agent: *\nAllow: /", media_type="text/plain")


@router.get("/manifest.json")
def manifest_json():
    manifest_path = _STATIC_DIR / "manifest.json"
    if manifest_path.exists():
        return HTMLResponse(
            content=manifest_path.read_text(encoding="utf-8"),
            media_type="application/json",
        )
    return HTMLResponse(content="{}", media_type="application/json")


@router.get("/sitemap.xml")
def sitemap_xml():
    from datetime import date

    from fastapi.responses import Response

    from config import get_db
    from models import Product, Supplier

    base = "http://localhost:8000"
    today = date.today().isoformat()

    static_urls = [
        ("/", "1.0", "daily"),
        ("/ar/", "0.9", "daily"),
        ("/products", "0.9", "daily"),
        ("/ar/products", "0.8", "daily"),
        ("/b2b/products", "0.9", "daily"),
        ("/ar/b2b/products", "0.8", "daily"),
        ("/b2b/suppliers", "0.8", "weekly"),
        ("/ar/b2b/suppliers", "0.7", "weekly"),
        ("/b2b", "0.7", "weekly"),
        ("/ar/b2b", "0.7", "weekly"),
        ("/b2b/rfq", "0.7", "weekly"),
        ("/ar/b2b/rfq", "0.6", "weekly"),
        ("/buyer", "0.7", "weekly"),
        ("/seller", "0.7", "weekly"),
        ("/cart", "0.8", "daily"),
        ("/ar/cart", "0.7", "daily"),
        ("/checkout", "0.8", "daily"),
        ("/tracking", "0.6", "weekly"),
        ("/escrow", "0.6", "weekly"),
        ("/b2b/messages", "0.5", "daily"),
        ("/about", "0.5", "monthly"),
        ("/faq", "0.5", "monthly"),
        ("/careers", "0.4", "monthly"),
        ("/terms", "0.3", "yearly"),
        ("/privacy", "0.3", "yearly"),
        ("/cookie", "0.2", "yearly"),
    ]

    urls_xml = ""
    for path, priority, changefreq in static_urls:
        urls_xml += (
            f'  <url><loc>{base}{path}</loc><lastmod>{today}</lastmod>'
            f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>\n"
        )

    try:
        db = next(get_db())
        for p in db.query(Product).limit(50).all():
            urls_xml += (
                f'  <url><loc>{base}/products#{p.id}</loc><lastmod>{today}</lastmod>'
                f"<changefreq>weekly</changefreq><priority>0.6</priority></url>\n"
            )
        for s in db.query(Supplier).limit(30).all():
            urls_xml += (
                f'  <url><loc>{base}/supplier/{s.id}</loc><lastmod>{today}</lastmod>'
                f"<changefreq>weekly</changefreq><priority>0.6</priority></url>\n"
            )
    except Exception:
        pass

    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>'
    return Response(content=xml, media_type="application/xml; charset=utf-8")


# ============================================================
# Arabic API endpoints (kept from original static_pages.py)
# ============================================================

from datetime import datetime, timezone  # noqa: E402
from typing import List  # noqa: E402

from fastapi import Depends  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from config import get_db  # noqa: E402
from models import (  # noqa: E402
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Order,
    OrderCreate,
    OrderResponse,
    Product,
)


@router.get("/ar/products", response_model=List)
def list_products_arabic(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()


@router.post("/ar/orders", response_model=OrderResponse)
def create_order_arabic(order: OrderCreate, db: Session = Depends(get_db)):
    import random  # noqa: E402
    import string  # noqa: E402

    order_number = (
        f"LYB-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=6))}"
    )
    order_data = order.model_dump(exclude={"items"}, exclude_unset=True)
    db_order = Order(order_number=order_number, **order_data)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.post("/ar/chat", response_model=ChatResponse)
def chat_arabic(request: ChatRequest, db: Session = Depends(get_db)):
    from chatbot import get_chatbot  # noqa: E402

    chatbot_instance = get_chatbot()
    result = chatbot_instance.process_message(
        session_id=request.session_id, message=request.message, is_arabic=True
    )
    db_message = ChatMessage(
        session_id=request.session_id,
        user_message=request.message,
        bot_response=result["response"],
        is_arabic=True,
    )
    db.add(db_message)
    db.commit()
    return ChatResponse(
        session_id=request.session_id,
        response=result["response"],
        is_arabic=True,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/ar/errors")
def get_arabic_errors():
    from errors_ar import get_all_errors  # noqa: E402

    return get_all_errors("ar")


@router.get("/ar/success")
def get_arabic_success():
    from errors_ar import get_all_success  # noqa: E402

    return get_all_success("ar")
