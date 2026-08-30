"""
Libya B2B Platform - Frontend Server (I18N)
Port 3000 - Template-basiert mit Sprachunterstuetzung
Projektversion: v2.0
"""

import http.server
import json
import os
import re
import socketserver
import urllib.request
from urllib.parse import urlparse

PORT = 3000
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


# Sprach-Dateien laden
def load_locale(lang):
    """Sprach-Datei laden"""
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def rewrite_nav_links(content, lang):
    """Navigation-Links dynamisch basierend auf Sprache anpassen"""
    # Step 1: Rewrite lang-btn hrefs.
    # Templates always use English paths (no /ar/ prefix).
    # On EN pages: lang-btn shows "AR" → link to Arabic version (/ar/...)
    # On AR pages: lang-btn shows "EN" → link to English version (keep English path)
    def rewrite_lang_switch(match):
        href = match.group(1)
        attrs = match.group(2)  # class="lang-btn" data-lang-switch
        # If href already has /ar prefix (from _lang_switch), keep it as-is
        if href.startswith("/ar"):
            return match.group(0)
        if lang == "ar":
            return match.group(0)  # Keep English path for EN switch
        # English page: prefix with /ar/ for AR switch
        if href == "/":
            return f'href="/ar/"{attrs}'
        return f'href="/ar{href}"{attrs}'

    content = re.sub(
        r'href="(/[^"]*?)"(\s+class="lang-btn(?:-top)?"\s+data-lang-switch)',
        rewrite_lang_switch,
        content,
    )

    # Step 2: Rewrite all other internal links (skip lang-btn, already handled)
    if lang == "ar":
        # On AR pages: add /ar/ prefix to English links (but not lang-btn)
        def add_ar_prefix(match):
            tag = match.group(0)  # full <a ...> tag
            href = match.group(1)
            # Skip lang-btn links (they are handled separately)
            if 'lang-btn' in tag or 'data-lang-switch' in tag:
                return tag
            if href == "/":
                return tag.replace(href, '/ar/')
            elif (
                href.startswith("/")
                and not href.startswith("/ar/")
                and href not in ["/health", "/docs", "/api"]
            ):
                return tag.replace(f'href="{href}"', f'href="/ar{href}"')
            return tag

        content = re.sub(
            r'<a\s[^>]*href="(/[^"]*)"[^>]*>',
            add_ar_prefix,
            content,
        )
    else:
        # On EN pages: strip /ar/ prefix from Arabic links (but not lang-btn)
        def remove_ar_prefix(match):
            tag = match.group(0)
            href = match.group(1)
            # Skip lang-btn links (they are handled separately)
            if 'lang-btn' in tag or 'data-lang-switch' in tag:
                return tag
            if href.startswith("/ar/"):
                return tag.replace(f'href="{href}"', f'href="{href[3:]}"')
            return tag

        content = re.sub(
            r'<a\s[^>]*href="(/ar/[^"]*)"[^>]*>',
            remove_ar_prefix,
            content,
        )

    return content


def render_template(template_name, lang="en"):
    """Template mit Sprach-Variablen rendern"""
    locale = load_locale(lang)
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.html")

    if not os.path.exists(template_path):
        return None

    # SEO: Inject generic title, meta_description, canonical_url
    # so nav.html can use {{title}}, {{meta_description}}, {{canonical_url}}
    tpl_data = locale.get(template_name, {})
    locale["title"] = tpl_data.get("title", locale.get("landing", {}).get("title", "Libya B2B"))
    locale["meta_description"] = tpl_data.get("meta_description", locale.get("landing", {}).get("meta_description", ""))
    # _base: "/ar" for Arabic pages, empty for English — used in nav links
    locale["_base"] = "/ar" if lang == "ar" else ""
    # _lang_switch: URL to switch language ("/ar" on EN, "/" on AR)
    locale["_lang_switch"] = "/" if lang == "ar" else "/ar"
    # Map template_name back to URL path for canonical URL
    _tpl_to_path = {"landing": "", "b2b_products": "b2b/products", "b2b_suppliers": "b2b/suppliers"}
    _path = _tpl_to_path.get(template_name, template_name)
    locale["canonical_url"] = f"http://localhost:3000/{'' if lang == 'en' else 'ar/'}{_path}"
    # hreflang: alternate URLs for EN/AR
    if lang == "ar":
        locale["hreflang_en"] = f"http://localhost:3000/{_path}"
        locale["hreflang_ar"] = locale["canonical_url"]
    else:
        locale["hreflang_en"] = locale["canonical_url"]
        locale["hreflang_ar"] = f"http://localhost:3000/ar/{_path}"

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Template-Includes: <!-- NAV_INCLUDE --> und <!-- NAV_CSS_INCLUDE -->
    nav_html_path = os.path.join(TEMPLATES_DIR, "nav.html")
    nav_css_path = os.path.join(os.path.dirname(TEMPLATES_DIR), "static", "nav.css")
    nav_js_path = os.path.join(os.path.dirname(TEMPLATES_DIR), "static", "nav.js")
    if os.path.exists(nav_html_path):
        with open(nav_html_path, "r", encoding="utf-8") as f:
            nav_content = f.read()
        content = content.replace("<!-- NAV_INCLUDE -->", nav_content)
    if os.path.exists(nav_css_path):
        with open(nav_css_path, "r", encoding="utf-8") as f:
            nav_css_content = f.read()
        # Append shared component styles (btn, tab, form, badge)
        components_css_path = os.path.join(os.path.dirname(TEMPLATES_DIR), "static", "components.css")
        if os.path.exists(components_css_path):
            with open(components_css_path, "r", encoding="utf-8") as f:
                nav_css_content += "\n" + f.read()
        content = content.replace("<!-- NAV_CSS_INCLUDE -->", "<style>" + nav_css_content + "</style>")
    if os.path.exists(nav_js_path):
        content = content.replace("<!-- NAV_JS_INCLUDE -->", '<script src="/static/nav.js"></script>')

    # Variablen ersetzen: {{nav.home}}, {{landing.title}}, etc.
    def replace_var(match):
        var_path = match.group(1)
        keys = var_path.split(".")
        value = locale
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return match.group(0)  # Original zurueckgeben
        return str(value)

    content = re.sub(r"\{\{(\w+(?:\.\w+)*)\}\}", replace_var, content)

    # Navigation-Links dynamisch anpassen
    content = rewrite_nav_links(content, lang)

    # CSS fuer RTL hinzufuegen
    if lang == "ar":
        content = content.replace('<html lang="en">', '<html lang="ar" dir="rtl">')
        # Direction: rtl am Ende der body-CSS Regel einfuegen
        content = re.sub(r"(body\s*\{[^}]*)(})", r"\1 direction: rtl; }", content)

    return content


class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _generate_sitemap(self):
        """Generate dynamic sitemap.xml with products and suppliers from backend API"""
        base = "http://localhost:3000"
        today = "2026-08-27"
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
            urls_xml += f'  <url><loc>{base}{path}</loc><lastmod>{today}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>\n'
        # Dynamic: fetch products from backend API
        try:
            req = urllib.request.Request(f"{BACKEND_URL}/api/products")
            with urllib.request.urlopen(req, timeout=5) as resp:
                products = json.loads(resp.read().decode())
                for p in products[:50]:  # Limit to 50 products
                    pid = p.get("id", "")
                    urls_xml += f'  <url><loc>{base}/products#{pid}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>\n'
        except Exception:
            pass
        # Dynamic: fetch suppliers from backend API
        try:
            req = urllib.request.Request(f"{BACKEND_URL}/api/b2b/suppliers")
            with urllib.request.urlopen(req, timeout=5) as resp:
                suppliers = json.loads(resp.read().decode())
                if isinstance(suppliers, list):
                    for s in suppliers[:30]:  # Limit to 30 suppliers
                        sid = s.get("id", "")
                        urls_xml += f'  <url><loc>{base}/supplier/{sid}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>\n'
        except Exception:
            pass
        return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>'

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API-Proxy
        if path.startswith("/api/"):
            self.proxy_request("GET", path, parsed.query)
            return

        # Health-Check
        if path == "/health":
            self.proxy_request("GET", "/health", "")
            return

        # Redirect /ar → /ar/ (trailing slash)
        if path == "/ar":
            self.send_response(301)
            self.send_header("Location", "/ar/")
            self.end_headers()
            return

        # Sprache erkennen
        is_arabic = path.startswith("/ar/")
        lang = "ar" if is_arabic else "en"

        # Pfad bereinigen
        clean_path = path.replace("/ar/", "/") if is_arabic else path

        # Template-Routing
        template_map = {
            "/": "landing",
            "/landing": "landing",
            "/products": "products",
            "/cart": "cart",
            "/checkout": "checkout",
            "/seller": "seller",
            "/tracking": "tracking",
            "/b2b": "b2b",
            "/b2b/products": "b2b_products",
            "/b2b/suppliers": "suppliers",
            "/b2b/rfq": "rfq",
            "/b2b/rfq/new": "rfq_new",
            "/b2b/messages": "messages",
            "/buyer": "buyer",
            "/faq": "faq",
            "/terms": "terms",
            "/privacy": "privacy",
            "/cookie": "cookie",
            "/about": "about",
            "/careers": "careers",
            "/register": "register",
            "/login": "landing",
            "/welcome": "welcome",
            "/guide": "guide",
            "/support": "support",
            "/import": "import",
            "/admin/suppliers": "admin_suppliers",
            "/forgot-password": "forgot-password",
            "/verify-email": "verify-email",
            "/2fa": "2fa",
            "/escrow": "escrow",
            "/escrow/admin": "escrow_admin",
        }

        # Product-Detail mit ID-Parameter
        if re.match(r"^/b2b/products/\d+$", clean_path):
            template_name = "product_detail"
            content = render_template(template_name, lang)
            if content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        # Supplier-Detail mit ID-Parameter
        if re.match(r"^/b2b/suppliers/\d+$", clean_path):
            template_name = "supplier_detail"
            content = render_template(template_name, lang)
            if content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        # RFQ-Detail mit ID-Parameter
        if re.match(r"^/b2b/rfq/\d+$", clean_path):
            template_name = "rfq_detail"
            content = render_template(template_name, lang)
            if content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        # Konversation mit ID-Parameter
        if re.match(r"^/b2b/messages/\d+$", clean_path):
            template_name = "conversation"
            content = render_template(template_name, lang)
            if content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        # SEO + PWA: robots.txt, sitemap.xml, manifest.json at root
        if clean_path in ("/robots.txt", "/manifest.json"):
            seo_file = os.path.join(STATIC_DIR, clean_path.lstrip("/"))
            if os.path.exists(seo_file):
                content_type = "text/plain" if clean_path.endswith(".txt") else "application/json"
                with open(seo_file, "r") as f:
                    seo_content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type + "; charset=utf-8")
                self.end_headers()
                self.wfile.write(seo_content.encode("utf-8"))
                return

        # Dynamic sitemap.xml — fetches products/suppliers from backend API
        if clean_path == "/sitemap.xml":
            try:
                sitemap = self._generate_sitemap()
                self.send_response(200)
                self.send_header("Content-Type", "application/xml; charset=utf-8")
                self.end_headers()
                self.wfile.write(sitemap.encode("utf-8"))
            except Exception:
                # Fallback to static file
                static_sitemap = os.path.join(STATIC_DIR, "sitemap.xml")
                if os.path.exists(static_sitemap):
                    with open(static_sitemap, "r") as f:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/xml; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(f.read().encode("utf-8"))
            return

        if clean_path in template_map:
            template_name = template_map[clean_path]
            content = render_template(template_name, lang)
            if content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        # Static Files
        if path.startswith("/static/"):
            # Strip /static/ prefix - directory is already /app/static
            self.path = "/" + path[len("/static/") :]
            super().do_GET()
            return

        if not os.path.splitext(path)[1]:
            # Fallback: statische Datei
            if is_arabic:
                page = path.replace("/ar/", "").strip("/")
                for ext in ["_ar.html", ".html"]:
                    html_path = os.path.join(STATIC_DIR, page + ext)
                    if os.path.exists(html_path):
                        self.path = "/" + page + ext
                        super().do_GET()
                        return
            else:
                html_path = os.path.join(STATIC_DIR, path.lstrip("/") + ".html")
                if os.path.exists(html_path):
                    self.path = path + ".html"

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            self.proxy_request("POST", parsed.path, "", post_data)
            return
        super().do_POST()

    # Headers that should NOT be forwarded between hops
    HOP_BY_HOP = frozenset(
        [
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        ]
    )

    def proxy_request(self, method, path, query="", body=None):
        try:
            url = f"{BACKEND_URL}{path}"
            if query:
                url += f"?{query}"

            req = urllib.request.Request(url, method=method)
            req.add_header("Content-Type", "application/json")

            # Forward cookies from browser to backend (session auth)
            cookie_header = self.headers.get("Cookie")
            if cookie_header:
                req.add_header("Cookie", cookie_header)

            if body:
                req.data = body

            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                # Forward all response headers (incl. Set-Cookie) from backend
                for header, value in response.getheaders():
                    if header.lower() not in self.HOP_BY_HOP:
                        self.send_header(header, value)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # Note: CORS headers are added per-response in proxy_request and
    # do_GET/do_POST. No need to inject them here (was causing duplicates).


def run_server():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    print(f"Frontend Server gestartet auf Port {PORT}")
    print(f"URL: http://localhost:{PORT}")
    print(f"Backend: {BACKEND_URL}")

    with socketserver.TCPServer(("", PORT), FrontendHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
