"""
auto_ingredients.py
Бүтээгдэхүүний нэрнээс орц найрлагыг автоматаар таньж DB-д оруулна.

python3 auto_ingredients.py
"""
import sqlite3
import re
from pathlib import Path

DB_PATH = str(Path.home() / "Downloads" / "skincare_project.db")

# ═══════════════════════════════════════════════════════════════
# ОРЦНЫ МЭДЛЭГИЙН САН
# Бүтээгдэхүүний нэр дотор хайх keyword → (орц нэр, функц тайлбар)
# ═══════════════════════════════════════════════════════════════
INGREDIENT_RULES = [
    # ── Brightening / Нөсөө толбо ─────────────────────────────
    (r"\bniacinamide\b",          "Niacinamide",        "Гялалзалт тэгшлэх / тос хянах"),
    (r"\bvitamin\s*c\b|vit\.?\s*c\b|ascorbic\b|glutathione\b|gluta\b",
                                   "Vitamin C",          "Гялалзуулах / нөсөө толбо арилгах"),
    (r"\barbutin\b",               "Arbutin",            "Нөсөө толбо арилгах / гялалзуулах"),
    (r"\btranexamic|txa\b",        "Tranexamic Acid",    "Нөсөө толбо, улайлт тэгшлэх"),
    (r"\bkojic\b",                 "Kojic Acid",         "Нөсөө толбо арилгах / гялалзуулах"),
    (r"\bazelaic\b",               "Azelaic Acid",       "Нөсөө толбо / батгатай тэмцэх"),
    (r"\blicorice|glycyrrhiz\b",   "Licorice Root",      "Гялалзуулах / тайвшруулах"),
    (r"\bturmeric|curcumin\b",     "Turmeric",           "Гялалзуулах / үрэвслийн эсрэг"),
    (r"\bright|radianc|glow|illumin", "Brightening Complex", "Гялалзуулах цогцолбор"),

    # ── Hydrating / Чийгшүүлэх ────────────────────────────────
    (r"\bhyaluronic|hyal\b|ha\b(?=\s*(acid|serum|toner|cream|essence))",
                                   "Hyaluronic Acid",    "Гүнзгий чийгшүүлэх"),
    (r"\bglycer\b",                "Glycerin",           "Чийг татах / чийгшүүлэх"),
    (r"\bsqualane\b",              "Squalane",           "Чийгшүүлэх / арьс зөөлрүүлэх"),
    (r"\bpanthenol|pro-vitamin\s*b5", "Panthenol",       "Тайвшруулах / хамгаалалтын давхарга"),
    (r"\baqua\b(?=\s*(toner|cream|gel|serum|essence))",
                                   "Hyaluronic Acid",    "Гүнзгий чийгшүүлэх"),
    (r"\bsodium\s*pca\b",          "Sodium PCA",         "Чийг барих / чийгшүүлэх"),
    (r"\bsea\s*buckthorn\b",       "Sea Buckthorn",      "Чийгшүүлэх / антиоксидант"),
    (r"\birish\s*moss|algae|seaweed", "Algae Extract",   "Чийгшүүлэх / эрдэс бодис нөхөх"),
    (r"\bbirch\b",                 "Birch Juice",        "Чийгшүүлэх / эрдэс бодис нөхөх"),

    # ── Barrier / Ceramide ─────────────────────────────────────
    (r"\bcerami[cd]e\b",           "Ceramide",           "Хамгаалалтын давхарга сэргээх"),
    (r"\bceramd\b|ceramd\b",       "Ceramide",           "Хамгаалалтын давхарга сэргээх"),
    (r"\bocta\b(?=peptide|decyl)|cholesterol\b", "Barrier Complex", "Арьсны тусгаар байдал"),

    # ── Acne / Батгатай тэмцэх ────────────────────────────────
    (r"\bsalic[iy]lic|bha\b",      "Salicylic Acid",     "Нүх цэвэрлэх / батгатай тэмцэх"),
    (r"\btea\s*tree\b",            "Tea Tree Oil",        "Батгатай тэмцэх / нян устгах"),
    (r"\bzinc\b",                  "Zinc",               "Тос хянах / үрэвсэл намдаах"),
    (r"\bbenzoyl\b",               "Benzoyl Peroxide",   "Батга устгах / нян эсрэг"),
    (r"\bsulfur\b",                "Sulfur",             "Батгатай тэмцэх / нүх цэвэрлэх"),
    (r"\bacne\b",                  "Salicylic Acid",     "Нүх цэвэрлэх / батгатай тэмцэх"),
    (r"\bblemish|blemi\b",         "Salicylic Acid",     "Нүх цэвэрлэх / батгатай тэмцэх"),
    (r"\bpore\b",                  "Niacinamide",        "Гялалзалт тэгшлэх / тос хянах"),
    (r"\bpurif|purif\w+",          "Salicylic Acid",     "Нүх цэвэрлэх / батгатай тэмцэх"),
    (r"\bheartleaf|houttuynia\b",  "Heartleaf Extract",  "Батга / үрэвслийн эсрэг / тайвшруулах"),
    (r"\bkombucha\b",              "Kombucha Ferment",   "Нян эсрэг / антиоксидант"),
    (r"\bmugwort|artemisia\b",     "Mugwort Extract",    "Тайвшруулах / батга / улайлтын эсрэг"),

    # ── Soothing / Тайвшруулах ────────────────────────────────
    (r"\bcentella|cica\b|madeca\b|tigeca\b|teca\b",
                                   "Centella Asiatica",  "Тайвшруулах / үрэвслийг намдаах"),
    (r"\ballantoin\b",             "Allantoin",          "Арьс тайвшруулах / нөхөн сэргэлт"),
    (r"\baloe\s*(vera|barbadensis)?\b", "Aloe Vera",     "Тайвшруулах / чийгшүүлэх"),
    (r"\bchamomile|bisabolol\b",   "Chamomile",          "Тайвшруулах / улайлт намдаах"),
    (r"\bgreen\s*tea|camellia\b",  "Green Tea",          "Исэлдэлтийн эсрэг / тайвшруулах"),
    (r"\brose\s*(water|hip|extract)?\b|rosehip\b",
                                   "Rose Extract",       "Тайвшруулах / чийгшүүлэх / антиоксидант"),
    (r"\blocal\b(?=\s*anest|\s*relief|\s*sooth)|sooth\w+",
                                   "Centella Asiatica",  "Тайвшруулах / үрэвслийг намдаах"),
    (r"\boat\b(?=\s*(ceram|extract|milk|mask|\s))",
                                   "Oat Extract",        "Тайвшруулах / эмзэг арьсанд тохиромжтой"),
    (r"\bcalendul\b",              "Calendula",          "Тайвшруулах / нян эсрэг"),
    (r"\bladle?r\b",               "Centella Asiatica",  "Тайвшруулах / үрэвслийг намдаах"),

    # ── Anti-aging / Насжилттай тэмцэх ───────────────────────
    (r"\bretinol\b|retin-a\b|retinal\b|tretinoin\b",
                                   "Retinol",            "Эс шинэчлэх / насжилттай тэмцэх"),
    (r"\bbakuchiol\b",             "Bakuchiol",          "Retinol орлуулагч / эс шинэчлэх"),
    (r"\bpeptide|pdrn\b|nad\+?\b|nad[0-9]|adenosine\b",
                                   "Peptide",            "Арьс нягтруулах / эсийн тэжээл"),
    (r"\bcollagen\b",              "Collagen",           "Арьсны уян хатан чанар нэмэх"),
    (r"\bcoq10|coenzyme\b",        "CoQ10",              "Исэлдэлтийн эсрэг / эсийн эрч"),
    (r"\bresveratrol\b",           "Resveratrol",        "Насжилттай тэмцэх / антиоксидант"),
    (r"\bastaxanthin\b",           "Astaxanthin",        "Хүчтэй антиоксидант / гялалзуулах"),
    (r"\bferment|lactobacillus\b", "Ferment Filtrate",   "Эсийн сэргэлт / антиоксидант"),

    # ── Exfoliating / Аргасах ─────────────────────────────────
    (r"\baha\b|glycolic|lactic\s*acid\b|mandelic\b",
                                   "AHA",                "Гадна эс арилгах / гялалзуулах"),
    (r"\bpha\b|gluconolactone\b",  "PHA",                "Зөөлөн аргасах / чийгшүүлэх"),
    (r"\bexfoli|peeling|peel\b(?!\s*mask)\b",
                                   "AHA",                "Гадна эс арилгах / гялалзуулах"),
    (r"\bpapaya|papain\b",         "Papaya Enzyme",      "Эсийн гадна давхарга арилгах"),
    (r"\bpineapple|bromelain\b",   "Pineapple Enzyme",   "Зөөлөн аргасах ферментийн орц"),

    # ── Sun / Нарны хамгаалалт ────────────────────────────────
    (r"\bspf\s*\d+\b|sunscreen|sunblock|uv\b(?=\s*(block|filter|prot))",
                                   "UV Filter",          "Нарны хамгаалалт"),
    (r"\bzinc\s*oxide\b",          "Zinc Oxide",         "Физик нарны хамгаалалт"),
    (r"\btitanium\s*dioxide\b",    "Titanium Dioxide",   "Физик нарны хамгаалалт"),

    # ── Moisturizing Complex ──────────────────────────────────
    (r"\bsnail\s*(mucin|secre|filtrate|repa)?\b|mucin\b",
                                   "Snail Mucin",        "Нөхөн сэргэлт / чийгшүүлэх"),
    (r"\bbee\s*venom\b",           "Bee Venom",          "Тонус нэмэх / арьс нягтруулах"),
    (r"\bhoney\b",                 "Honey Extract",      "Чийгшүүлэх / нян эсрэг"),
    (r"\bpropolis\b",              "Propolis",           "Нян эсрэг / нөхөн сэргэлт"),
    (r"\broyaljelly|royal\s*jelly\b", "Royal Jelly",     "Тэжээллэг / чийгшүүлэх"),
    (r"\bcaviar\b",                "Caviar Extract",     "Тэжээллэг / насжилттай тэмцэх"),
    (r"\bstem\s*cell\b",           "Stem Cell Extract",  "Эс нөхөн сэргэх / насжилттай тэмцэх"),
    (r"\bprotein\b(?=\s*(serum|cream|toner))",
                                   "Protein Complex",    "Арьс бэхжүүлэх / тэжээллэг"),

    # ── Oil / Тос ─────────────────────────────────────────────
    (r"\brosehip\s*(oil|seed)?\b", "Rosehip Oil",        "Тэжээллэг / насжилттай тэмцэх"),
    (r"\bjojoba\b",                "Jojoba Oil",         "Чийгшүүлэх / тос тэнцвэржүүлэх"),
    (r"\bmarula\b",                "Marula Oil",         "Тэжээллэг / чийгшүүлэх"),
    (r"\bargan\b",                 "Argan Oil",          "Тэжээллэг / уян хатан чанар"),
    (r"\bneem\b",                  "Neem Oil",           "Нян эсрэг / батгатай тэмцэх"),
    (r"\bbaob?ab\b",               "Baobab Oil",         "Тэжээллэг / чийгшүүлэх"),
    (r"\bavocado\b",               "Avocado Oil",        "Тэжээллэг / чийгшүүлэх"),
    (r"\bsea\s*buckthorn\b",       "Sea Buckthorn Oil",  "Антиоксидант / тэжээллэг"),

    # ── Специфик брэнд/бүтээгдэхүүн keyword ─────────────────
    (r"\bpdrn\b",                  "PDRN",               "Арьс нөхөн сэргэх / нягтруулах"),
    (r"\bexosome\b",               "Exosome",            "Эсийн харилцаа / нөхөн сэргэлт"),
    (r"\bvt\s*reedle\b|reedle\b",  "Microneedle Complex","Гүнзгий тэжээлт / нөхөн сэргэлт"),
    (r"\beel\s*gfa\b|gfa\b",       "GFA Complex",        "Арьс бэхжүүлэх"),

    # ── Category based defaults ───────────────────────────────
    # (категориос орц нэмэх — сүүлд хэрэглэнэ)
]

# Категориор анхдагч орц (нэрт keyword олдоогүй үед)
CATEGORY_DEFAULTS = {
    "Serum":       ["Hyaluronic Acid", "Niacinamide"],
    "Toner":       ["Hyaluronic Acid", "Glycerin"],
    "Moisturizer": ["Hyaluronic Acid", "Ceramide"],
    "Cleanser":    ["Glycerin"],
    "OilCleanser": ["Glycerin", "Squalane"],
    "Essence":     ["Hyaluronic Acid", "Glycerin"],
    "Sunscreen":   ["UV Filter", "Glycerin"],
    "Mask":        ["Hyaluronic Acid"],
    "Eye Care":    ["Peptide", "Hyaluronic Acid"],
    "Other":       [],
}


def detect_ingredients(product_name: str, category: str) -> list[str]:
    """Бүтээгдэхүүний нэрнээс орц таньна."""
    name_lower = product_name.lower()
    found = []
    seen = set()

    for pattern, ing_name, _ in INGREDIENT_RULES:
        if re.search(pattern, name_lower, re.IGNORECASE):
            if ing_name not in seen:
                found.append(ing_name)
                seen.add(ing_name)

    # Орц олдоогүй бол категориор анхдагч орц нэмнэ
    if not found and category in CATEGORY_DEFAULTS:
        for ing in CATEGORY_DEFAULTS[category]:
            if ing not in seen:
                found.append(ing)
                seen.add(ing)

    return found


def get_or_create_ingredient(c, conn, name: str, func_desc: str) -> int:
    c.execute("SELECT ingredient_id FROM ingredients WHERE ingredient_name=?", (name,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute("INSERT INTO ingredients (ingredient_name, function_desc) VALUES (?,?)", (name, func_desc))
    conn.commit()
    return c.lastrowid


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Орцны функц тайлбар map
    ing_funcs = {ing: func for _, ing, func in INGREDIENT_RULES}
    # Нэмэлт defaults
    for cat_ings in CATEGORY_DEFAULTS.values():
        for ing in cat_ings:
            if ing not in ing_funcs:
                ing_funcs[ing] = "Арьсны арчилгаа"

    # Бүх бүтээгдэхүүн татах
    c.execute("""SELECT p.product_id, p.product_name, cat.category_name
        FROM products p
        LEFT JOIN categories cat ON p.category_id=cat.category_id
        WHERE p.price_mnt > 0""")
    products = c.fetchall()

    print(f"Нийт бүтээгдэхүүн: {len(products)}")
    print("Орц таньж байна...")

    inserted_total = 0
    skipped = 0
    products_with_ings = 0

    for pid, name, cat in products:
        if not name:
            skipped += 1
            continue

        ings = detect_ingredients(name, cat or "Other")
        if not ings:
            skipped += 1
            continue

        products_with_ings += 1

        for order, ing_name in enumerate(ings, 1):
            # Орц ID авах/үүсгэх
            func = ing_funcs.get(ing_name, "Арьсны арчилгаа")
            ing_id = get_or_create_ingredient(c, conn, ing_name, func)

            # product_ingredients-д нэмэх (давхардлаас зайлсхийх)
            c.execute("""SELECT 1 FROM product_ingredients
                WHERE product_id=? AND ingredient_id=?""", (pid, ing_id))
            if not c.fetchone():
                c.execute("""INSERT INTO product_ingredients
                    (product_id, ingredient_id, ingredient_order) VALUES (?,?,?)""",
                    (pid, ing_id, order))
                inserted_total += 1

        if products_with_ings % 100 == 0:
            conn.commit()
            print(f"  {products_with_ings} бүтээгдэхүүн боловсруулагдлаа...")

    conn.commit()

    # Дүн
    c.execute("SELECT COUNT(*) FROM product_ingredients")
    total_pi = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT product_id) FROM product_ingredients")
    prods_with = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ingredients")
    total_ings = c.fetchone()[0]

    print("\n" + "="*50)
    print(f"✓ Нэмэгдсэн орц холбоос: {inserted_total}")
    print(f"✓ Орцтой болсон бүтээгдэхүүн: {prods_with}")
    print(f"✓ Орцгүй бүтээгдэхүүн: {skipped}")
    print(f"✓ Нийт орц найрлага: {total_ings}")
    print(f"✓ Нийт product_ingredients: {total_pi}")
    print("="*50)

    # Хамгийн олон орцтой бүтээгдэхүүн
    print("\nХамгийн олон орцтой бүтээгдэхүүн (топ 10):")
    c.execute("""SELECT p.product_name, COUNT(pi.ingredient_id) n
        FROM products p JOIN product_ingredients pi ON p.product_id=pi.product_id
        GROUP BY p.product_id ORDER BY n DESC LIMIT 10""")
    for row in c.fetchall():
        print(f"  {row[0][:50]:50s} → {row[1]} орц")

    # Хамгийн түгээмэл орц
    print("\nХамгийн түгээмэл орцнууд (топ 15):")
    c.execute("""SELECT i.ingredient_name, COUNT(pi.product_id) n
        FROM ingredients i JOIN product_ingredients pi ON i.ingredient_id=pi.ingredient_id
        GROUP BY i.ingredient_id ORDER BY n DESC LIMIT 15""")
    for row in c.fetchall():
        print(f"  {row[0]:30s} → {row[1]} бүтээгдэхүүн")

    conn.close()
    print("\n✓ Дууслаа! DB шинэчлэгдсэн.")


if __name__ == "__main__":
    main()
