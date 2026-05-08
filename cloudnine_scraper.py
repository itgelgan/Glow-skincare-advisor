"""
cloudnine_scraper.py  —  Terminal-д ажиллуулна:
python3 cloudnine_scraper.py
"""
import requests, sqlite3, time, logging
import urllib3
urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

DB_PATH = "/Users/nmutl/Downloads/skincare_project.db"

# Жинхэнэ API + шаардлагатай header-үүд
API_BASE = "https://cloudnine.nextstore.mn/api/v2/shop"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://cloudnine.mn",
    "Referer": "https://cloudnine.mn/",
    "X-Client-Source": "web",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}

def fetch_products(page=1, per_page=100):
    url = f"{API_BASE}/products?page={page}&itemsPerPage={per_page}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"✗ page {page}: {e}")
        return None

def fetch_product_detail(code):
    url = f"{API_BASE}/products/{code}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        r.raise_for_status()
        return r.json()
    except:
        return None

def guess_category(name, ptype=""):
    n = (name + " " + ptype).lower()
    if any(k in n for k in ["cleansing oil","oil clean"]): return "OilCleanser"
    if any(k in n for k in ["cleanser","foam","wash","gel wash"]): return "Cleanser"
    if any(k in n for k in ["toner","pad","mist"]): return "Toner"
    if any(k in n for k in ["serum","ampoule","concentrate"]): return "Serum"
    if any(k in n for k in ["essence","snail","mucin","emulsion"]): return "Essence"
    if any(k in n for k in ["sun","spf","sunscreen","sunblock"]): return "Sunscreen"
    if any(k in n for k in ["moistur","cream","lotion","balm"]): return "Moisturizer"
    if any(k in n for k in ["mask","sheet","peeling","exfol"]): return "Mask"
    return "Other"

def get_or_create_brand(conn, name):
    c = conn.cursor()
    c.execute("SELECT brand_id FROM brands WHERE brand_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO brands (brand_name, country) VALUES (?,?)", (name, "Unknown"))
    conn.commit(); return c.lastrowid

def get_or_create_cat(conn, name):
    c = conn.cursor()
    c.execute("SELECT category_id FROM categories WHERE category_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
    conn.commit(); return c.lastrowid

def main():
    log.info("=== Cloudnine.mn scraper эхэлж байна ===")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    inserted = skipped = 0
    page = 1

    while True:
        log.info(f"Page {page} татаж байна...")
        data = fetch_products(page=page, per_page=100)

        if not data:
            log.warning("Өгөгдөл ирсэнгүй, зогсоно")
            break

        # API response бүтцийг олох
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = (data.get("hydra:member") or data.get("member") or
                     data.get("items") or data.get("products") or
                     data.get("data") or [])

        if not items:
            log.info(f"Хоосон response — дуусав. Raw: {str(data)[:200]}")
            break

        log.info(f"  → {len(items)} бүтээгдэхүүн")

        for p in items:
            # Нэр
            name = (p.get("name") or p.get("title") or p.get("shortDescription") or "").strip()
            if not name or len(name) < 2:
                skipped += 1; continue

            # Давхардал шалгах
            c.execute("SELECT product_id FROM products WHERE product_name=? AND source=?",
                      (name, "cloudnine.mn"))
            if c.fetchone():
                skipped += 1; continue

            # Үнэ
            price = None
            for price_key in ["price", "originalPrice", "discountedPrice", "lowestPriceVariant"]:
                raw = p.get(price_key)
                if raw:
                    try: price = float(str(raw).replace(",","").replace("₮","").strip()); break
                    except: pass
            if not price or price <= 0:
                skipped += 1; continue

            # Брэнд
            brand = "Unknown"
            if isinstance(p.get("brand"), dict):
                brand = p["brand"].get("name") or p["brand"].get("code") or "Unknown"
            elif isinstance(p.get("vendor"), str):
                brand = p["vendor"]
            elif name:
                brand = name.split()[0]

            # Ангилал
            ptype = ""
            if isinstance(p.get("mainTaxon"), dict):
                ptype = p["mainTaxon"].get("name", "")
            elif isinstance(p.get("taxons"), list) and p["taxons"]:
                ptype = p["taxons"][0].get("name", "") if isinstance(p["taxons"][0], dict) else ""
            cat = guess_category(name, ptype)

            # Үнэлгээ
            rating = None
            avg = p.get("averageRating") or p.get("rating")
            if avg:
                try: rating = float(avg)
                except: pass

            # DB-д оруулах
            brand_id = get_or_create_brand(conn, brand)
            cat_id   = get_or_create_cat(conn, cat)
            c.execute(
                "INSERT INTO products (brand_id,category_id,product_name,price_mnt,rating,source) VALUES (?,?,?,?,?,?)",
                (brand_id, cat_id, name, price, rating, "cloudnine.mn")
            )
            conn.commit()
            inserted += 1
            log.info(f"  ✓ {name} | {brand} | {price}₮")

        # Дараагийн хуудас байгаа эсэх
        total_pages = 1
        if isinstance(data, dict):
            total = data.get("hydra:totalItems") or data.get("totalItems") or data.get("total", 0)
            if total:
                import math
                total_pages = math.ceil(int(total) / 100)
        if page >= total_pages:
            break
        page += 1
        time.sleep(1)

    conn.close()
    log.info(f"\n✓ Нэмэгдсэн: {inserted} | Алгасагдсан: {skipped}")
    log.info("=== Дууслаа ===")

if __name__ == "__main__":
    main()
