"""
beautysecrets_scraper.py
python3 beautysecrets_scraper.py
"""
import requests, sqlite3, time, logging
import urllib3
urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
    handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

DB_PATH = "/Users/nmutl/Downloads/skincare_project.db"
API_BASE = "https://pink.beautysecrets.mn/api"
SOURCE   = "beautysecrets.mn"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://beautysecrets.mn",
    "Referer": "https://beautysecrets.mn/",
}

def guess_category(name, brand=""):
    n = name.lower()
    if any(k in n for k in ["cleansing oil","oil clean","클렌징 오일"]): return "OilCleanser"
    if any(k in n for k in ["cleanser","foam","wash","cleansing milk","cleansing cream","цэвэрлэгч","угаагч"]): return "Cleanser"
    if any(k in n for k in ["toner","тонер","pad","mist","lotion toner"]): return "Toner"
    if any(k in n for k in ["serum","серум","ampoule","concentrate","booster"]): return "Serum"
    if any(k in n for k in ["essence","эссенс","snail","mucin","emulsion"]): return "Essence"
    if any(k in n for k in ["sun","spf","нарны","sunscreen","sunblock","uv"]): return "Sunscreen"
    if any(k in n for k in ["moistur","cream","крем","lotion","балм","balm","gel cream"]): return "Moisturizer"
    if any(k in n for k in ["mask","маск","sheet","peel","exfol","scrub"]): return "Mask"
    if any(k in n for k in ["eye","нүдний","lip","уруул"]): return "Eye Care"
    return "Other"

def get_or_create_brand(conn, name):
    c = conn.cursor()
    c.execute("SELECT brand_id FROM brands WHERE brand_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO brands (brand_name, country) VALUES (?,?)", (name, "Korea"))
    conn.commit(); return c.lastrowid

def get_or_create_cat(conn, name):
    c = conn.cursor()
    c.execute("SELECT category_id FROM categories WHERE category_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
    conn.commit(); return c.lastrowid

def get_or_create_ingredient(conn, name):
    c = conn.cursor()
    c.execute("SELECT ingredient_id FROM ingredients WHERE ingredient_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO ingredients (ingredient_name) VALUES (?)", (name,))
    conn.commit(); return c.lastrowid

def main():
    log.info("=== BeautySecrets.mn scraper эхэлж байна ===")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    inserted = skipped = 0
    page = 1

    while True:
        log.info(f"Page {page} татаж байна...")
        try:
            r = requests.get(
                f"{API_BASE}/p/list",
                params={"page": page, "limit": 100},
                headers=HEADERS, timeout=20, verify=False
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning(f"✗ {e}")
            break

        if not data.get("success"):
            log.warning(f"success=false: {data}")
            break

        products_data = data.get("products", {})
        items = products_data.get("data", [])

        if not items:
            log.info("Хоосон — дуусав")
            break

        log.info(f"  → {len(items)} бүтээгдэхүүн")

        for p in items:
            name = (p.get("name") or "").strip()
            if not name or len(name) < 2:
                skipped += 1; continue

            # Давхардал шалгах
            c.execute("SELECT product_id FROM products WHERE product_name=? AND source=?",
                      (name, SOURCE))
            if c.fetchone():
                skipped += 1; continue

            # Үнэ — sale_price байвал тэр, үгүй бол regular_price
            price = p.get("sale_price") or p.get("price") or p.get("regular_price")
            try: price = float(price)
            except: price = None
            if not price or price <= 0:
                skipped += 1; continue

            # Брэнд
            brand = "Unknown"
            if isinstance(p.get("brand"), dict):
                brand = p["brand"].get("name", "Unknown")

            # Ангилал
            cat = guess_category(name, brand)

            # Үнэлгээ
            rating = None
            avg = p.get("average_rating")
            if avg:
                try: rating = float(avg)
                except: pass

            # DB-д оруулах
            brand_id = get_or_create_brand(conn, brand)
            cat_id   = get_or_create_cat(conn, cat)
            c.execute(
                "INSERT INTO products (brand_id,category_id,product_name,price_mnt,rating,source) VALUES (?,?,?,?,?,?)",
                (brand_id, cat_id, name, price, rating, SOURCE)
            )
            conn.commit()
            prod_id = c.lastrowid
            inserted += 1
            log.info(f"  ✓ {name[:50]} | {brand} | {price:,.0f}₮")

        # Дараагийн хуудас байгаа эсэх
        last_page = products_data.get("last_page", 1)
        log.info(f"  Page {page}/{last_page}")
        if page >= last_page:
            break
        page += 1
        time.sleep(0.8)

    conn.close()
    log.info(f"\n✓ Нэмэгдсэн: {inserted} | Алгасагдсан: {skipped}")

    # Дүн харуулах
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products WHERE source=?", (SOURCE,))
    log.info(f"  beautysecrets.mn нийт DB-д: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM products")
    log.info(f"  DB нийт бүтээгдэхүүн: {c.fetchone()[0]}")
    conn.close()
    log.info("=== Дууслаа ===")

if __name__ == "__main__":
    main()
