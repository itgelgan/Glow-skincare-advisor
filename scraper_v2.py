"""
╔══════════════════════════════════════════════════════════════╗
║   Glow Skincare — Scraper v2  (засварласан URL-ууд)         ║
║   python3 scraper_v2.py                                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import sqlite3, time, re, json, logging
from dataclasses import dataclass, field
from typing import Optional
import urllib3
urllib3.disable_warnings()

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper_v2.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# !! DB замаа тохируулна !!
DB_PATH = "/Users/nmutl/Downloads/skincare_project.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "mn,en-US;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

@dataclass
class Product:
    name: str
    price: Optional[float]
    brand: str
    category: str
    source: str
    rating: Optional[float] = None
    ingredients: list = field(default_factory=list)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def fetch(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        log.info(f"  ✓ {url} [{r.status_code}]")
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        log.warning(f"  ✗ {url} → {e}")
        return None

def fetch_json(url, timeout=20):
    """JSON API endpoint татах"""
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "application/json"},
                         timeout=timeout, verify=False)
        r.raise_for_status()
        log.info(f"  ✓ JSON {url} [{r.status_code}]")
        return r.json()
    except Exception as e:
        log.warning(f"  ✗ JSON {url} → {e}")
        return None

def clean_price(text):
    if not text: return None
    d = re.sub(r"[^\d.]", "", str(text).replace(",", ""))
    try: return float(d) if d else None
    except: return None

def clean(text):
    return " ".join(str(text).split()).strip() if text else ""

def guess_category(name):
    n = name.lower()
    if any(k in n for k in ["cleansing oil","oil clean","тосон цэвэрлэгч"]): return "OilCleanser"
    if any(k in n for k in ["cleanser","foam","wash","цэвэрлэгч","угаагч","gel wash"]): return "Cleanser"
    if any(k in n for k in ["toner","тонер","pad","пэд","mist"]): return "Toner"
    if any(k in n for k in ["serum","серум","ampoule","ампул","concentrate"]): return "Serum"
    if any(k in n for k in ["essence","эссенс","snail","mucin","емulsion","emulsion"]): return "Essence"
    if any(k in n for k in ["sun","spf","нарны","sunscreen","sunblock"]): return "Sunscreen"
    if any(k in n for k in ["moistur","cream","крем","lotion","лосьон","balm","бальзам","gel cream"]): return "Moisturizer"
    if any(k in n for k in ["mask","маск","sheet","пилинг","peeling","exfol"]): return "Mask"
    if any(k in n for k in ["eye","нүдний","lip","уруул"]): return "Eye Care"
    return "Other"


# ══════════════════════════════════════════════════════════════
# 1. CLOUDNINE.MN  — Shopify JSON API ашиглана
# ══════════════════════════════════════════════════════════════
def scrape_cloudnine():
    base = "https://cloudnine.mn"
    products = []
    seen = set()
    page = 1
    while True:
        # Shopify-ийн /products.json endpoint
        data = fetch_json(f"{base}/products.json?limit=250&page={page}")
        if not data or not data.get("products"):
            break
        items = data["products"]
        if not items:
            break
        for p in items:
            title = clean(p.get("title", ""))
            if not title or title in seen:
                continue
            seen.add(title)
            vendor = clean(p.get("vendor", title.split()[0]))
            # Үнэ — эхний variant
            variants = p.get("variants", [])
            price = None
            if variants:
                raw = variants[0].get("price", "0")
                price = clean_price(raw)
            # Бүтээгдэхүүний төрлөөс category
            ptype = p.get("product_type", "")
            cat = guess_category(ptype or title)
            products.append(Product(
                name=title, price=price, brand=vendor,
                category=cat, source="cloudnine.mn"
            ))
        log.info(f"  cloudnine page {page}: {len(items)} бүтээгдэхүүн")
        if len(items) < 250:
            break
        page += 1
        time.sleep(0.5)
    log.info(f"cloudnine.mn нийт: {len(products)}")
    return products


# ══════════════════════════════════════════════════════════════
# 2. COSE.MN  — Next.js/Custom platform
# ══════════════════════════════════════════════════════════════
def scrape_cose():
    base = "https://cose.mn"
    products = []
    seen = set()

    # Боломжит URL замууд
    urls = [
        f"{base}/mn/products",
        f"{base}/mn/shop",
        f"{base}/mn/skincare",
        f"{base}/mn",
    ]

    for start_url in urls:
        soup = fetch(start_url)
        if not soup:
            continue

        # Бүх product link-ийг ол
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/product/" in href or "/item/" in href or "/goods/" in href:
                full = base + href if href.startswith("/") else href
                links.add(full)

        log.info(f"  cose.mn {start_url}: {len(links)} link олдлоо")

        for link in list(links)[:100]:  # хэт олон хуудас уншихгүйн тулд
            psoup = fetch(link)
            if not psoup:
                continue
            # Нэр
            name_el = psoup.select_one("h1, h2, .product-title, [class*='product-name'], [class*='title']")
            if not name_el:
                continue
            name = clean(name_el.get_text())
            if not name or name in seen or len(name) < 3:
                continue
            seen.add(name)
            # Үнэ
            price_el = psoup.select_one("[class*='price'], .cost, [class*='amount']")
            price = clean_price(price_el.get_text()) if price_el else None
            # Брэнд
            brand_el = psoup.select_one("[class*='brand'], .vendor, [class*='maker']")
            brand = clean(brand_el.get_text()) if brand_el else name.split()[0]
            products.append(Product(
                name=name, price=price, brand=brand,
                category=guess_category(name), source="cose.mn"
            ))
            time.sleep(0.3)

        if products:
            break  # нэг URL амжилттай байвал зогсоно

    # Хэрэв үр дүнгүй бол ерөнхий HTML scrape
    if not products:
        for pg in range(1, 6):
            soup = fetch(f"{base}/mn/products?page={pg}")
            if not soup: break
            for card in soup.select("div[class*='product'], article, li[class*='item']"):
                name_el = card.select_one("h2,h3,h4,[class*='title'],[class*='name']")
                if not name_el: continue
                name = clean(name_el.get_text())
                if not name or name in seen or len(name) < 3: continue
                seen.add(name)
                price_el = card.select_one("[class*='price'],.cost")
                price = clean_price(price_el.get_text()) if price_el else None
                products.append(Product(
                    name=name, price=price, brand=name.split()[0],
                    category=guess_category(name), source="cose.mn"
                ))
            time.sleep(0.8)

    log.info(f"cose.mn нийт: {len(products)}")
    return products


# ══════════════════════════════════════════════════════════════
# 3. COSMIX.MN  — WooCommerce/WordPress
# ══════════════════════════════════════════════════════════════
def scrape_cosmix():
    base = "https://cosmix.mn"
    products = []
    seen = set()

    # WooCommerce REST API туршина
    api_urls = [
        f"{base}/wp-json/wc/v3/products?per_page=100&page=1",
        f"{base}/wp-json/wc/store/v1/products?per_page=100",
    ]
    for api_url in api_urls:
        data = fetch_json(api_url)
        if data and isinstance(data, list) and len(data) > 0:
            for p in data:
                name = clean(p.get("name", ""))
                if not name or name in seen: continue
                seen.add(name)
                price = clean_price(p.get("price") or p.get("regular_price", ""))
                brand = clean(p.get("brand", name.split()[0]))
                products.append(Product(
                    name=name, price=price, brand=brand,
                    category=guess_category(name), source="cosmix.mn"
                ))
            if products:
                log.info(f"  cosmix.mn API: {len(products)} бүтээгдэхүүн")
                break

    # API ажиллахгүй бол HTML scrape
    if not products:
        page_urls = [
            f"{base}/shop",
            f"{base}/product-category/skincare",
            f"{base}/product-category/face",
            f"{base}/бүтээгдэхүүн",
        ]
        for start_url in page_urls:
            for pg in range(1, 8):
                url = f"{start_url}/page/{pg}/" if pg > 1 else start_url
                soup = fetch(url)
                if not soup: break
                cards = soup.select("li.product, div.product, article.product")
                if not cards: break
                new = False
                for card in cards:
                    name_el = card.select_one("h2,h3,.woocommerce-loop-product__title,[class*='product-title']")
                    if not name_el: continue
                    name = clean(name_el.get_text())
                    if not name or name in seen or len(name) < 3: continue
                    seen.add(name); new = True
                    price_el = card.select_one(".price ins,.price bdi,.price,.amount")
                    price = clean_price(price_el.get_text()) if price_el else None
                    brand_el = card.select_one(".brand,.vendor,[class*='brand']")
                    brand = clean(brand_el.get_text()) if brand_el else name.split()[0]
                    products.append(Product(
                        name=name, price=price, brand=brand,
                        category=guess_category(name), source="cosmix.mn"
                    ))
                if not new: break
                time.sleep(0.8)
            if products: break

    log.info(f"cosmix.mn нийт: {len(products)}")
    return products


# ══════════════════════════════════════════════════════════════
# 4. BEAUTYSECRETS.MN  — Custom Next.js platform
# ══════════════════════════════════════════════════════════════
def scrape_beautysecrets():
    base = "https://beautysecrets.mn"
    products = []
    seen = set()

    # Next.js-ийн API endpoint-уудыг туршина
    api_candidates = [
        f"{base}/api/products?page=1&limit=100",
        f"{base}/api/v1/products?limit=100",
        f"{base}/api/items?category=skincare",
        f"{base}/_next/data/products.json",
    ]
    for api_url in api_candidates:
        data = fetch_json(api_url)
        if data:
            items = data if isinstance(data, list) else data.get("data", data.get("products", data.get("items", [])))
            if isinstance(items, list) and items:
                for p in items:
                    name = clean(p.get("name", p.get("title", p.get("product_name", ""))))
                    if not name or name in seen: continue
                    seen.add(name)
                    price = clean_price(p.get("price", p.get("sale_price", p.get("regular_price", ""))))
                    brand = clean(p.get("brand", p.get("vendor", p.get("brand_name", name.split()[0]))))
                    products.append(Product(
                        name=name, price=price, brand=brand,
                        category=guess_category(name), source="beautysecrets.mn"
                    ))
                log.info(f"  beautysecrets API: {len(products)} бүтээгдэхүүн")
                break

    # HTML scrape
    if not products:
        page_urls = [
            f"{base}/shop",
            f"{base}/products",
            f"{base}/skincare",
            f"{base}/category/skincare",
            f"{base}/brands",
        ]
        for start_url in page_urls:
            soup = fetch(start_url)
            if not soup: continue

            # Product card-ийг олох
            cards = soup.select(
                "div[class*='product'], article[class*='product'], "
                "div[class*='item'], li[class*='product'], "
                "div[class*='card'], [data-product]"
            )

            # Next.js JSON state хайх
            for script in soup.find_all("script", id="__NEXT_DATA__"):
                try:
                    nd = json.loads(script.string)
                    # props.pageProps доторх бүтээгдэхүүн хайх
                    def find_products(obj, depth=0):
                        if depth > 6: return []
                        if isinstance(obj, list):
                            for item in obj:
                                if isinstance(item, dict) and ("name" in item or "title" in item) and "price" in item:
                                    return obj
                                r = find_products(item, depth+1)
                                if r: return r
                        elif isinstance(obj, dict):
                            for v in obj.values():
                                r = find_products(v, depth+1)
                                if r: return r
                        return []
                    found = find_products(nd)
                    for p in found[:200]:
                        if not isinstance(p, dict): continue
                        name = clean(p.get("name", p.get("title", p.get("product_name", ""))))
                        if not name or name in seen or len(name) < 3: continue
                        seen.add(name)
                        price = clean_price(p.get("price", p.get("sale_price", "")))
                        brand = clean(p.get("brand", p.get("vendor", p.get("brand_name", name.split()[0]))))
                        products.append(Product(
                            name=name, price=price, brand=brand,
                            category=guess_category(name), source="beautysecrets.mn"
                        ))
                except: pass

            for card in cards:
                name_el = card.select_one("h2,h3,h4,[class*='title'],[class*='name'],[class*='product-name']")
                if not name_el: continue
                name = clean(name_el.get_text())
                if not name or name in seen or len(name) < 3: continue
                seen.add(name)
                price_el = card.select_one("[class*='price'],[class*='cost'],[class*='amount']")
                price = clean_price(price_el.get_text()) if price_el else None
                brand_el = card.select_one("[class*='brand'],[class*='vendor']")
                brand = clean(brand_el.get_text()) if brand_el else name.split()[0]
                products.append(Product(
                    name=name, price=price, brand=brand,
                    category=guess_category(name), source="beautysecrets.mn"
                ))
            if products: break

    log.info(f"beautysecrets.mn нийт: {len(products)}")
    return products


# ══════════════════════════════════════════════════════════════
# 5. MIMICORNER.MN  — Shopify (өөр subdomain/path)
# ══════════════════════════════════════════════════════════════
def scrape_mimicorner():
    base = "https://mimicorner.mn"
    products = []
    seen = set()

    # Shopify JSON API
    page = 1
    while True:
        data = fetch_json(f"{base}/products.json?limit=250&page={page}")
        if data and data.get("products"):
            for p in data["products"]:
                title = clean(p.get("title", ""))
                if not title or title in seen: continue
                seen.add(title)
                variants = p.get("variants", [])
                price = clean_price(variants[0].get("price", "0")) if variants else None
                vendor = clean(p.get("vendor", title.split()[0]))
                ptype = p.get("product_type", "")
                products.append(Product(
                    name=title, price=price, brand=vendor,
                    category=guess_category(ptype or title),
                    source="mimicorner.mn"
                ))
            log.info(f"  mimicorner page {page}: {len(data['products'])} бүтээгдэхүүн")
            if len(data["products"]) < 250: break
            page += 1
            time.sleep(0.5)
        else:
            break

    # Shopify JSON ажиллахгүй бол HTML
    if not products:
        cat_paths = ["/", "/skincare", "/face", "/k-beauty", "/shop"]
        for path in cat_paths:
            for pg in range(1, 6):
                url = f"{base}{path}?page={pg}" if pg > 1 else f"{base}{path}"
                soup = fetch(url)
                if not soup: break
                cards = soup.select(".product-item,.grid__item,li.grid__item,.product-card,div[class*='product']")
                if not cards: break
                new = False
                for card in cards:
                    name_el = card.select_one("h2,h3,h4,[class*='title'],.product-name")
                    if not name_el: continue
                    name = clean(name_el.get_text())
                    if not name or name in seen or len(name) < 3: continue
                    seen.add(name); new = True
                    price_el = card.select_one("[class*='price'],.money")
                    price = clean_price(price_el.get_text()) if price_el else None
                    products.append(Product(
                        name=name, price=price, brand=name.split()[0],
                        category=guess_category(name), source="mimicorner.mn"
                    ))
                if not new: break
                time.sleep(0.8)
            if products: break

    log.info(f"mimicorner.mn нийт: {len(products)}")
    return products


# ══════════════════════════════════════════════════════════════
# 6. CLOUDNINE.MN дахин — products.json ашиглан
#    (Дээрх функц бэлэн, энд зөвхөн log)
# ══════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════
# DB INSERT
# ══════════════════════════════════════════════════════════════
def get_or_create_brand(conn, brand_name, country="Unknown"):
    c = conn.cursor()
    c.execute("SELECT brand_id FROM brands WHERE brand_name = ?", (brand_name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO brands (brand_name, country) VALUES (?, ?)", (brand_name, country))
    conn.commit(); return c.lastrowid

def get_or_create(conn, table, col, value):
    c = conn.cursor()
    # id column нэрийг автоматаар ол
    c.execute(f"PRAGMA table_info({table})")
    cols = c.fetchall()
    id_col = cols[0][1]
    c.execute(f"SELECT {id_col} FROM {table} WHERE {col} = ?", (value,))
    r = c.fetchone()
    if r: return r[0]
    c.execute(f"INSERT INTO {table} ({col}) VALUES (?)", (value,))
    conn.commit(); return c.lastrowid

def insert_products(products, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    inserted = skipped = 0
    for p in products:
        if not p.name or not p.price or p.price <= 0:
            skipped += 1; continue
        c.execute("SELECT product_id FROM products WHERE product_name=? AND source=?", (p.name, p.source))
        if c.fetchone():
            skipped += 1; continue
        brand_id = get_or_create_brand(conn, p.brand)
        cat_id   = get_or_create(conn, "categories", "category_name", p.category)
        c.execute(
            "INSERT INTO products (brand_id,category_id,product_name,price_mnt,rating,source) VALUES (?,?,?,?,?,?)",
            (brand_id, cat_id, p.name, p.price, p.rating, p.source)
        )
        conn.commit(); inserted += 1
    conn.close()
    return inserted, skipped


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    log.info("=" * 60)
    log.info("Glow Scraper v2 эхэлж байна...")
    log.info("=" * 60)

    scrapers = [
        ("cloudnine.mn",     scrape_cloudnine),
        ("cose.mn",          scrape_cose),
        ("cosmix.mn",        scrape_cosmix),
        ("beautysecrets.mn", scrape_beautysecrets),
        ("mimicorner.mn",    scrape_mimicorner),
        # miruskincare.mn өмнөх scraper-т амжилттай ажиллаж байгаа тул хасав
    ]

    all_products = []
    for name, fn in scrapers:
        log.info(f"\n{'─'*50}")
        log.info(f"▶  {name}")
        log.info(f"{'─'*50}")
        try:
            ps = fn()
            all_products.extend(ps)
            log.info(f"  → {len(ps)} бүтээгдэхүүн олдлоо")
        except Exception as e:
            log.error(f"  ✗ {name} алдаа: {e}")
        time.sleep(1.5)

    log.info(f"\n{'='*60}")
    log.info(f"Нийт: {len(all_products)} | DB-д оруулж байна...")
    inserted, skipped = insert_products(all_products, DB_PATH)
    log.info(f"✓ Нэмэгдсэн: {inserted} | Алгасагдсан: {skipped}")

    # Дүн
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products")
    log.info(f"\n📦 DB нийт: {c.fetchone()[0]} бүтээгдэхүүн")
    c.execute("SELECT source, COUNT(*) FROM products WHERE source IS NOT NULL GROUP BY source ORDER BY 2 DESC")
    log.info("📊 Сайтаар:")
    for src, cnt in c.fetchall():
        log.info(f"   {src:35s} → {cnt}")
    conn.close()

if __name__ == "__main__":
    main()
