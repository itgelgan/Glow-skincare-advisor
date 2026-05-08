# 🌸 Glow — Skincare Advisor

Монголын онлайн дэлгүүрүүдээс арьс арчилгааны бүтээгдэхүүний мэдээлэл цуглуулж, хэрэглэгчид зориулсан зөвлөх систем.

---

## 📁 Файлын бүтэц

```
glow-skincare/
│
├── app.py                    # Streamlit веб апп (үндсэн UI)
├── auto_ingredients.py       # Бүтээгдэхүүний найрлага автоматаар таних
│
├── scraper.py                # Scraper v1 — эхний хувилбар
├── scraper_v2.py             # Scraper v2 — сайжруулсан хувилбар
│
├── beautysecrets_scraper.py  # BeautySecrets.mn зориулалтын scraper
├── cloudnine_scraper.py      # Cloudnine.mn зориулалтын scraper
├── mimicorner_scraper.py     # MimiCorner.mn зориулалтын scraper
│
├── glow-skincare-v2.html     # Статик HTML прототип (v2)
│
├── scraper.log               # Scraper v1 log
├── scraper_v2.log            # Scraper v2 log
│
└── README.md
```

> ⚠️ `skincare_project_updated.db` файлыг `.gitignore`-д нэмнэ үү — хэт том байж болно.

---

## 🗂️ Өгөгдлийн сан (SQLite)

**Хүснэгтүүд:**

| Хүснэгт | Тайлбар |
|---|---|
| `products` | Бүтээгдэхүүний нэр, үнэ, үнэлгээ, эх сурвалж |
| `brands` | Брэнд, улс |
| `categories` | Ангилал (Serum, Toner, Moisturizer...) |
| `ingredients` | Орц найрлага |

**Одоогийн өгөгдөл (2026-05-07):**
- Нийт бүтээгдэхүүн: **624+**
- Эх сурвалж: `miruskincare.com`, `beautysecrets.mn`, `cloudnine.mn`, `mimicorner.mn`

---

## 🕷️ Scraper-үүд

| Файл | Эх сурвалж | API |
|---|---|---|
| `beautysecrets_scraper.py` | beautysecrets.mn | `https://pink.beautysecrets.mn/api/p/list` |
| `cloudnine_scraper.py` | cloudnine.mn | `https://cloudnine.nextstore.mn/api/v2/shop/products` |
| `mimicorner_scraper.py` | mimicorner.mn | `https://mimicorner.mn/api/storefront/products` |
| `scraper_v2.py` | Олон сайт | Шууд HTML + JSON |

### Ажиллуулах:
```bash
python3 beautysecrets_scraper.py
python3 cloudnine_scraper.py
python3 mimicorner_scraper.py
python3 scraper_v2.py
```

---

## 🤖 auto_ingredients.py

Бүтээгдэхүүний нэрнээс орц найрлагыг автоматаар таньж `ingredients` болон `product_ingredients` хүснэгтэд оруулна.

```bash
python3 auto_ingredients.py
```

---

## 🖥️ Веб апп (Streamlit)

```bash
pip install streamlit pandas matplotlib
streamlit run app.py
```

**Функцүүд:**
- Бүтээгдэхүүн хайх, шүүх
- Үнийн харьцуулалт
- Ангилал, брэндээр харах
- Орц найрлагын мэдээлэл

---

## ⚙️ Суулгах

```bash
pip install requests sqlite3 pandas matplotlib streamlit
```

---

## 📊 Ангилалууд

`OilCleanser` · `Cleanser` · `Toner` · `Serum` · `Essence` · `Sunscreen` · `Moisturizer` · `Mask` · `Eye Care` · `Other`

---

*Гlow Skincare Advisor — Монгол хэрэглэгчдэд зориулсан K-beauty зөвлөх систем 🌸*
