"""
mimicorner_scraper.py
python3 mimicorner_scraper.py
"""
import re
import sqlite3
import time
import json
from datetime import datetime
from pathlib import Path
import requests

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

API_URL  = "https://mimicorner.mn/api/storefront/products"
DB_PATH  = Path.home() / "Downloads" / "skincare_project.db"
DELAY    = 0.8
PER_PAGE = 48

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://mimicorner.mn/products",
    "X-Requested-With": "XMLHttpRequest",
}
session = requests.Session()
session.headers.update(HEADERS)


def clean_price(text):
    if not text: return None
    s = re.sub(r"[^\d.]", "", str(text))
    try: return float(s) if s else None
    except: return None


def guess_category(name, cats=[]):
    n = name.lower()
    if cats:
        return cats[0] if isinstance(cats[0], str) else cats[0].get("name", "Other")
    if any(k in n for k in ["cleansing oil","oil clean"]): return "OilCleanser"
    if any(k in n for k in ["cleanser","foam","wash","cleansing milk"]): return "Cleanser"
    if any(k in n for k in ["toner","pad","mist"]): return "Toner"
    if any(k in n for k in ["serum","ampoule","concentrate"]): return "Serum"
    if any(k in n for k in ["essence","snail","mucin","emulsion"]): return "Essence"
    if any(k in n for k in ["sun","spf","sunscreen"]): return "Sunscreen"
    if any(k in n for k in ["moistur","cream","lotion","balm"]): return "Moisturizer"
    if any(k in n for k in ["mask","sheet","peel","scrub"]): return "Mask"
    return "Other"


def get_or_create_brand(conn, name):
    c = conn.cursor()
    name = name or "Unknown"
    c.execute("SELECT brand_id FROM brands WHERE brand_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO brands (brand_name, country) VALUES (?,?)", (name, "Korea"))
    conn.commit(); return c.lastrowid


def get_or_create_cat(conn, name):
    c = conn.cursor()
    name = name or "Other"
    c.execute("SELECT category_id FROM categories WHERE category_name=?", (name,))
    r = c.fetchone()
    if r: return r[0]
    c.execute("INSERT INTO categories (category_name) VALUES (?)", (name,))
    conn.commit(); return c.lastrowid


def fetch_all_products():
    print("Mimicorner API татаж байна...")
    # Эхний хуудас
    r = session.get(API_URL, params={"page": 1, "per_page": PER_PAGE}, timeout=15)
    print(f"  Status: {r.status_code}")

    if r.status_code != 200:
        print(f"  ✗ API хариу өгсөнгүй: {r.status_code}")
        return []

    try:
        data = r.json()
    except Exception as e:
        print(f"  ✗ JSON parse алдаа: {e}")
        print(f"  Response: {r.text[:200]}")
        return []

    print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

    # Products key олох
    prods_key = None
    if isinstance(data, list):
        all_prods = data
        print(f"  Нийт (list): {len(all_prods)}")
        return all_prods
    elif isinstance(data, dict):
        for k in ["products", "data", "items", "result"]:
            if isinstance(data.get(k), list):
                prods_key = k; break
        if not prods_key:
            print(f"  ✗ products key олдсонгүй. Keys: {list(data.keys())}")
            print(f"  Raw: {str(data)[:300]}")
            return []

    total     = data.get("total", 0)
    last_page = data.get("lastPage", data.get("last_page", data.get("pages", 1)))
    all_prods = list(data[prods_key])
    print(f"  Нийт: {total} | {last_page} хуудас | Эхний хуудас: {len(all_prods)}")

    pages = range(2, last_page + 1)
    if HAS_TQDM:
        pages = tqdm(pages, desc="  Хуудас", unit="p")

    for page in pages:
        time.sleep(DELAY)
        try:
            resp = session.get(API_URL, params={"page": page, "per_page": PER_PAGE}, timeout=15)
            if resp.status_code == 200:
                d = resp.json()
                batch = d.get(prods_key, []) if isinstance(d, dict) else d
                if not batch: break
                all_prods.extend(batch)
                print(f"  Page {page}: +{len(batch)}")
            else:
                print(f"  HTTP {resp.status_code} page {page}")
        except Exception as e:
            print(f"  Алдаа page {page}: {e}")

    return all_prods


def save_products(conn, products):
    c = conn.cursor()
    inserted = skipped = 0

    for p in products:
        try:
            name = (p.get("name") or "").strip()
            if not name or len(name) < 2:
                skipped += 1; continue

            # Давхардал
            c.execute("SELECT product_id FROM products WHERE product_name=? AND source=?",
                      (name, "mimicorner.mn"))
            if c.fetchone():
                skipped += 1; continue

            # Үнэ
            fmt_disc = p.get("formatted_discount")
            fmt_orig = p.get("formatted_original", "")
            price = clean_price(fmt_disc if fmt_disc else fmt_orig)
            if not price:
                price = clean_price(p.get("price") or p.get("price_mnt") or p.get("sale_price"))
            if not price or price <= 0:
                skipped += 1; continue

            # Брэнд
            brand = p.get("brand", "")
            if isinstance(brand, dict):
                brand = brand.get("name", "Unknown")
            brand = brand or "Unknown"

            # Ангилал
            cats = p.get("categories", [])
            cat_name = guess_category(name, cats)

            # Үнэлгээ
            rating = None
            try: rating = float(p.get("rating") or p.get("average_rating") or 0) or None
            except: pass

            brand_id = get_or_create_brand(conn, brand)
            cat_id   = get_or_create_cat(conn, cat_name)

            c.execute(
                "INSERT INTO products (brand_id,category_id,product_name,price_mnt,rating,source) VALUES (?,?,?,?,?,?)",
                (brand_id, cat_id, name, price, rating, "mimicorner.mn")
            )
            conn.commit()
            inserted += 1
            print(f"  ✓ {name[:45]} | {brand} | {price:,.0f}₮")

        except Exception as e:
            print(f"  ✗ Алдаа: {e} | {p.get('name','')}")

    return inserted, skipped


def main():
    print("=" * 55)
    print("  Mimicorner.mn → skincare_project.db")
    print("=" * 55)

    if not DB_PATH.exists():
        print(f"✗ DB олдсонгүй: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    print(f"DB: {DB_PATH}")

    products = fetch_all_products()
    if not products:
        print("✗ Бүтээгдэхүүн олдсонгүй")
        conn.close()
        return

    print(f"\n{len(products)} бүтээгдэхүүн хадгалж байна...")
    inserted, skipped = save_products(conn, products)

    # Дүн
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products WHERE source='mimicorner.mn'")
    mimi_total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    db_total = c.fetchone()[0]
    conn.close()

    print("\n" + "=" * 55)
    print(f"  ✓ Нэмэгдсэн  : {inserted}")
    print(f"  Алгасагдсан  : {skipped}")
    print(f"  mimicorner.mn DB-д : {mimi_total}")
    print(f"  DB нийт      : {db_total}")
    print("=" * 55)


if __name__ == "__main__":
    main()
