# 🌸 Glow — Монголын Skincare Advisor

> Орц найрлагын дүн шинжилгээнд суурилсан арьс арчилгааны зөвлөгч систем

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-pink)](LICENSE)

---

## 📌 Төслийн тухай

**Glow** нь Монголын онлайн гоо сайхны дэлгүүрүүдээс бүтээгдэхүүний мэдээллийг цуглуулж, орц найрлагын шинжлэх ухааны дүн шинжилгээнд тулгуурлан хэрэглэгчийн арьсны төрөлд хамгийн тохирох бүтээгдэхүүнийг зөвлөдөг систем юм.

Энэхүү төсөл нь **эдийн засгийн судалгааны зорилгоор** хийгдсэн бөгөөд Монголын гоо сайхны зах зээлийн бүтэц, үнийн тархалт, платформ хоорондын харьцуулалт зэрэг эдийн засгийн шинжилгээг агуулдаг.

---

## 📊 Мэдээллийн сан

### Цуглуулсан өгөгдөл

| Эх сурвалж | Бүтээгдэхүүн | Арга |
|------------|-------------|------|
| beautysecrets.mn | 1,712 | REST API |
| mimicorner.mn | 790 | REST API |
| miruskincare.com | 609 | Web scraping |
| cloudnine.mn | 14 | Web scraping |
| **Нийт** | **3,105** | |

### Өгөгдлийн бүтэц (ERD)

```
products ──── brands
    │    └─── categories
    │
    ├── product_ingredients ──── ingredients
    │                               │
    │                    ┌──────────┤
    │                    │          │
    │              ingredient_  ingredient_
    │              concerns    skin_types
    │                    │          │
    │              skin_concerns  skin_types
    └──────────────────────────────────────
```

**9 хүснэгт:**
- `products` — 3,105 бүтээгдэхүүн (нэр, үнэ, үнэлгээ, эх сурвалж)
- `brands` — 138 брэнд
- `categories` — 10 ангилал (Serum, Toner, Moisturizer, гэх мэт)
- `ingredients` — 49 орц найрлага
- `product_ingredients` — бүтээгдэхүүн-орц холбоос
- `ingredient_concerns` — орц-арьсны асуудал харьцаа
- `ingredient_skin_types` — орц-арьсны төрөл харьцаа
- `skin_concerns` — 4 арьсны асуудал
- `skin_types` — 5 арьсны төрөл

---

## 🗂️ Файлын бүтэц

```
Glow-skincare-advisor/
│
├── 📄 glow-skincare-v3.html      # Үндсэн вэб апп (3,105 бүтээгдэхүүн)
├── 📊 app.py                     # Streamlit эдийн засгийн шинжилгээ
├── 🧪 auto_ingredients.py        # Орц найрлага автоматаар таних скрипт
│
├── 🕷️ scraper_v2.py              # Үндсэн scraping скрипт
├── 🕷️ beautysecrets_scraper.py   # beautysecrets.mn API scraper
├── 🕷️ mimicorner_scraper.py      # mimicorner.mn API scraper
├── 🕷️ cloudnine_scraper.py       # cloudnine.mn scraper
│
├── 🗄️ skincare_project_updated.db # SQLite өгөгдлийн сан
└── 📋 README.md
```

---

## ✨ Үндсэн функцүүд

### 🌸 Вэб апп (`glow-skincare-v3.html`)
- **Арьсны төрлөөр зөвлөгөө** — Хуурай / Тослог / Холимог / Эмзэг / Хэвийн арьс тус бүрт routine болон орцны зөвлөмж
- **Орц найрлагын гарын авлага** — 20 орцны тайлбар, хослол, ямар арьсны төрлд тохирох
- **AI-д суурилсан шүүлт** — Арьсны төрөл + асуудлаар оноо тооцоолж эрэмбэлнэ
- **Claude AI чат** — Мэргэжлийн skincare зөвлөгөө
- **Судалгааны булан** — Эрдмийн нотолгоо, эдийн засгийн шинжилгээ

### 📊 Streamlit апп (`app.py`)
- Ангилалаар дундаж үнэ + Box plot
- Платформ хоорондын харьцуулалт (Pie chart, Bar chart)
- Үнийн тархалт (Histogram, дундаж vs медиан)
- Үнийн сегментчлэл (Budget / Mid / Premium / Luxury)
- Үнэ ба үнэлгээний корреляц (Scatter plot + trend line)
- Топ брэндүүдийн үнийн байрлал

---

## 🚀 Ажиллуулах заавар

### Вэб апп
HTML файлыг browser-т нээхэд л болно — нэмэлт суулгалт шаардлагагүй.

```bash
# Эсвэл Netlify Drop ашиглана
# https://app.netlify.com/drop → файл чирж тавина
```

### Streamlit шинжилгээ

```bash
# Суулгах
pip install streamlit pandas matplotlib numpy

# DB замыг тохируулах (app.py дотор)
DB_PATH = str(Path.home() / "Downloads" / "skincare_project.db")

# Ажиллуулах
streamlit run app.py
```

### Scraper ажиллуулах

```bash
pip install requests beautifulsoup4 selenium

# beautysecrets.mn
python3 beautysecrets_scraper.py

# mimicorner.mn
python3 mimicorner_scraper.py

# Орц найрлага автоматаар нэмэх
python3 auto_ingredients.py
```

---

## 🧪 Орц таних алгоритм

`auto_ingredients.py` нь бүтээгдэхүүний нэрнээс **regex pattern matching** ашиглан 49 орцыг автоматаар тодорхойлно.

```python
# Жишээ
detect_ingredients("ANUA Niacinamide 10% + TXA 4% Serum", "Serum")
# → ['Niacinamide', 'Tranexamic Acid', 'Hyaluronic Acid']
```

**Оноо тооцоолох томьёо:**
```
Score = (Concern орц × 2) + (Skin type орц × 1) + (Rating × 0.5) + (Орцтой бол +0.5)
```

---

## 📈 Эдийн засгийн дүн шинжилгээ

| Шинжилгээ | Үр дүн |
|-----------|--------|
| Нийт бүтээгдэхүүн | 3,105 |
| Дундаж үнэ | ~43,768₮ |
| Медиан үнэ | ~25,000₮ |
| Хамгийн олон бүтээгдэхүүнтэй платформ | beautysecrets.mn (55%) |
| Хамгийн өндөр дундаж үнэтэй ангилал | Serum |
| Үнэ-чанарын корреляц | Сул эерэг (r ≈ 0.1–0.2) |

**Гол дүгнэлт:** Монголын skincare зах зээлд үнэ нь чанарын хүчтэй дохио болдоггүй — "price-quality relationship" сул. Хэрэглэгчид орц найрлага биш брэндийн нэр хүнд, K-pop соёлын нөлөөгөөр худалдан авалтын шийдвэр гаргадаг байна.

---

## 🛠️ Технологийн стек

| Технологи | Хэрэглээ |
|-----------|---------|
| Python 3.12 | Scraping, DB, шинжилгээ |
| SQLite | Өгөгдлийн сан |
| Streamlit | Шинжилгээний дашбоард |
| Matplotlib | Визуализаци |
| HTML/CSS/JS | Вэб апп (vanilla, no framework) |
| Claude API | AI чат зөвлөгч |
| Requests + BS4 | Web scraping |

---

## 👩‍💻 Зохиогч

**itgelgan** — Эдийн засгийн оюутан

Энэхүү төсөл нь Монголын гоо сайхны зах зээлийн **эдийн засгийн судалгаа** болон хэрэглэгчдэд **мэдлэгт суурилсан худалдан авалтын шийдвэр** гаргахад туслах зорилготой хийгдсэн.

---

*🌸 Glow — Орц найрлага мэдэж, ухаалгаар сонго*
