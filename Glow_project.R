# ─────────────────────────────────────────────────────────────────────────────
#  Glow Analytics — Skincare Dashboard  (v3 — clean)
# ─────────────────────────────────────────────────────────────────────────────
suppressPackageStartupMessages({
  library(shiny)
  library(DBI)
  library(RSQLite)
  library(dplyr)
  library(tidyr)
  library(plotly)
  library(DT)
  library(randomForest)
})

# ── Palette ───────────────────────────────────────────────────────────────────
PLUM  <- "#a85570"; MAUVE <- "#d4849a"; ROSE  <- "#f9bfca"
BLUSH <- "#fde6ec"; MIST  <- "#c4adb5"; INK   <- "#2d1520"
CREAM <- "#fffaf8"
PAL9  <- c(PLUM,"#b86a84",MAUVE,"#c47a90","#9a4560","#e8a0b4","#7a3550",ROSE,"#d898ae")

gl <- function(p) {
  p |> plotly::config(displayModeBar=FALSE) |>
    plotly::layout(
      paper_bgcolor=CREAM, plot_bgcolor=CREAM,
      font=list(family="Noto Sans,sans-serif", color=INK, size=13),
      margin=list(l=8,r=8,t=32,b=8)
    )
}
rpal <- function(n, a=PLUM, b=ROSE) colorRampPalette(c(a,b))(n)

# ── DB path ───────────────────────────────────────────────────────────────────
DB <- local({
  cands <- c(file.path(getwd(),"skincare_project_updated.db"),
             "skincare_project_updated.db")
  f <- Filter(file.exists, cands)
  if (!length(f)) stop("skincare_project_updated.db олдсонгүй! setwd() хийнэ үү. Dir: ", getwd())
  normalizePath(f[1])
})

# ── Load data ─────────────────────────────────────────────────────────────────
load_data <- function() {
  con <- dbConnect(SQLite(), DB); on.exit(dbDisconnect(con))
  
  prods <- dbGetQuery(con, "
    SELECT p.product_id, p.product_name, p.price_mnt, p.rating, p.source,
           b.brand_name, b.country, c.category_name
    FROM products p
    LEFT JOIN brands     b ON p.brand_id    = b.brand_id
    LEFT JOIN categories c ON p.category_id = c.category_id
    WHERE p.price_mnt IS NULL OR p.price_mnt < 1000000
  ")
  
  ings <- dbGetQuery(con, "
    SELECT i.ingredient_id, i.ingredient_name, i.function_desc,
           COUNT(pi.product_id) AS product_count
    FROM ingredients i
    LEFT JOIN product_ingredients pi ON i.ingredient_id = pi.ingredient_id
    GROUP BY i.ingredient_id ORDER BY product_count DESC
  ")
  
  ing_skin <- dbGetQuery(con, "
    SELECT i.ingredient_name, st.skin_type_name, ist.suitability
    FROM ingredient_skin_types ist
    JOIN ingredients i  ON ist.ingredient_id = i.ingredient_id
    JOIN skin_types  st ON ist.skin_type_id  = st.skin_type_id
  ")
  
  brands <- dbGetQuery(con, "
    SELECT b.brand_name, b.country,
           COUNT(p.product_id) AS n, AVG(p.rating) AS avg_rating
    FROM products p JOIN brands b ON p.brand_id = b.brand_id
    WHERE b.brand_name NOT IN ('Unknown', 'Miru')
      AND b.brand_name IS NOT NULL
    GROUP BY b.brand_name HAVING COUNT(p.product_id) >= 10
    ORDER BY n DESC LIMIT 30
  ")
  
  list(prods=prods, ings=ings, ing_skin=ing_skin, brands=brands)
}
DAT <- load_data()

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS <- "
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&display=swap');
:root{--rose:#f9bfca;--blush:#fde6ec;--petal:#fff4f6;--cream:#fffaf8;
  --mauve:#d4849a;--plum:#a85570;--ink:#2d1520;--mist:#c4adb5;
  --glass:rgba(255,255,255,0.78);--shadow:0 8px 40px rgba(168,85,112,.11);}
*{font-family:'Noto Sans',sans-serif!important;box-sizing:border-box}
body{background:var(--petal);color:var(--ink);margin:0}
body::before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:radial-gradient(ellipse 70% 50% at 85% -10%,#fbc8d430 0%,transparent 60%),
             radial-gradient(ellipse 50% 40% at -10% 80%,#edd5f030 0%,transparent 60%)}
.gh{background:rgba(255,244,246,.94);backdrop-filter:blur(24px);
  border-bottom:1px solid rgba(212,132,154,.18);padding:14px 32px;
  display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200}
.glogo{font-family:'Cormorant Garamond',serif!important;font-size:27px;color:var(--plum);font-weight:600}
.glogo em{color:var(--mauve);font-style:italic}
.gsub{font-size:11px;color:var(--mist);font-weight:600;letter-spacing:1px;text-transform:uppercase}
.bpill{background:rgba(249,191,202,.22);border:1px solid rgba(249,191,202,.6);color:var(--plum);
  font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
  padding:5px 14px;border-radius:100px;display:inline-block}
.krow{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 32px 4px}
.kpi{background:var(--glass);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.92);
  border-radius:20px;padding:20px 22px;box-shadow:var(--shadow);transition:transform .2s}
.kpi:hover{transform:translateY(-3px)}
.ki{font-size:20px;margin-bottom:8px}
.kv{font-family:'Cormorant Garamond',serif!important;font-size:30px;color:var(--plum);font-weight:600;line-height:1}
.kn{font-size:12px;color:var(--mist);margin-top:4px;font-weight:500}
.nav-tabs{border-bottom:2px solid rgba(212,132,154,.2);margin-bottom:0;
  padding:0 32px;background:rgba(255,244,246,.72);backdrop-filter:blur(12px)}
.nav-tabs>li>a{font-size:12px!important;font-weight:700!important;color:var(--mist)!important;
  letter-spacing:1px!important;border:none!important;border-radius:0!important;
  padding:13px 20px!important;background:transparent!important;text-transform:uppercase!important}
.nav-tabs>li.active>a,.nav-tabs>li>a:hover{color:var(--plum)!important;
  border-bottom:3px solid var(--plum)!important;background:transparent!important}
.tab-content{padding:24px 32px;background:transparent}
.gc{background:var(--glass);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.92);
  border-radius:22px;box-shadow:var(--shadow);padding:22px 26px;margin-bottom:20px}
.gt{font-family:'Cormorant Garamond',serif!important;font-size:19px;color:var(--ink);font-weight:600;margin-bottom:3px}
.gs{font-size:12px;color:var(--mist);margin-bottom:14px;font-weight:500}
.sl{font-size:11px;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;color:var(--mauve);margin-bottom:5px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:860px){.g2{grid-template-columns:1fr}.krow{grid-template-columns:repeat(2,1fr)}}
.form-control,.selectize-input{border:1.5px solid rgba(212,132,154,.25)!important;
  border-radius:12px!important;font-size:13px!important;color:var(--ink)!important}
.form-control:focus,.selectize-input.focus{border-color:var(--mauve)!important;
  box-shadow:0 0 0 3px rgba(212,132,154,.12)!important}
.irs--shiny .irs-bar,.irs--shiny .irs-bar--single{background:var(--mauve);border-color:var(--mauve)}
.irs--shiny .irs-handle{background:var(--plum);border:2px solid var(--plum)}
.irs--shiny .irs-from,.irs--shiny .irs-to,.irs--shiny .irs-single{background:var(--plum)}
table.dataTable{font-size:13px!important;border-collapse:collapse!important}
table.dataTable thead th{background:var(--blush)!important;color:var(--plum)!important;
  font-size:11px!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.5px;
  border-bottom:2px solid rgba(212,132,154,.22)!important}
table.dataTable tbody tr:hover{background:rgba(249,191,202,.1)!important}
#tbl_desc_stats table.dataTable tbody td{color:#2d1520!important;font-size:13px!important;font-weight:600!important}
#tbl_desc_stats table.dataTable tbody tr:nth-child(odd){background:rgba(253,230,236,.2)!important}
.dataTables_wrapper .dataTables_info,.dataTables_wrapper .dataTables_length label,
.dataTables_wrapper .dataTables_filter label{color:var(--mist);font-size:12px}
.tbox{background:rgba(253,230,236,.3);border:1px solid rgba(212,132,154,.2);
  border-radius:14px;padding:16px 20px;margin-top:8px;line-height:1.8}
.tres{font-family:monospace!important;background:rgba(168,85,112,.07);
  border-radius:8px;padding:10px 14px;font-size:13px;color:#2d1520;white-space:pre-wrap}
.mlnote{font-size:12px;color:var(--mist);margin-bottom:10px;line-height:1.7}
.bglow{background:linear-gradient(135deg,#d4849a,#a85570)!important;color:#fff!important;
  border:none!important;border-radius:100px!important;padding:10px 26px!important;
  font-size:13px!important;font-weight:700!important;cursor:pointer;
  box-shadow:0 6px 20px rgba(168,85,112,.28);margin-bottom:14px}
"

# ── UI ────────────────────────────────────────────────────────────────────────
CATS <- c("Бүгд", sort(unique(na.omit(DAT$prods$category_name))))
SRCS <- c("Бүгд", sort(na.omit(unique(DAT$prods$source))))

ui <- fluidPage(
  tags$head(tags$style(HTML(CSS))),
  
  div(class="gh",
      div(div(class="glogo", HTML("Glow <em>Analytics</em>")),
          div(class="gsub", "Skincare Database — Data Studio")),
      div(class="bpill","✦ 3,124 Бүтээгдэхүүн")
  ),
  
  div(class="krow",
      div(class="kpi",div(class="ki","🫙"),div(class="kv","3,124"),div(class="kn","Нийт Бүтээгдэхүүн")),
      div(class="kpi",div(class="ki","🏷"), div(class="kv","138"),  div(class="kn","Брэнд")),
      div(class="kpi",div(class="ki","✨"), div(class="kv","49"),   div(class="kn","Орц")),
      div(class="kpi",div(class="ki","⭐"), div(class="kv","4.46"), div(class="kn","Дундаж Рейтинг"))
  ),
  
  tabsetPanel(id="tabs",
              
              # ══ EDA ═══════════════════════════════════════════════════════════════════
              tabPanel("📊 EDA",
                       div(class="g2",
                           div(class="gc",div(class="sl","Ангилал"),div(class="gt","Бүтээгдэхүүний тоо"),
                               div(class="gs","Ангиллаар"),plotlyOutput("p_cat",height="300px")),
                           div(class="gc",div(class="sl","Гарал үүсэл"),div(class="gt","Улсаар хуваарилалт"),
                               div(class="gs","Брэндийн гарал"),plotlyOutput("p_country",height="300px"))
                       ),
                       div(class="g2",
                           div(class="gc",div(class="sl","Үнэ"),div(class="gt","Үнийн тархалт"),
                               div(class="gs","Хязгаар тохируулна уу"),
                               sliderInput("price_cap","Дээд үнэ (₮):",min=20000,max=200000,
                                           value=120000,step=5000,pre="₮",sep=",",width="100%"),
                               plotlyOutput("p_price_hist",height="240px")),
                           div(class="gc",div(class="sl","Рейтинг"),div(class="gt","Рейтингийн тархалт"),
                               div(class="gs","1–5 оноо"),plotlyOutput("p_rating_hist",height="300px"))
                       ),
                       div(class="gc",
                           div(class="sl","Орц"),div(class="gt","Хамгийн их хэрэглэгддэг орцууд"),
                           div(class="gs","Хэдэн орцыг харах вэ"),
                           sliderInput("top_n","Тоо:",min=5,max=20,value=12,width="280px"),
                           plotlyOutput("p_top_ing",height="360px")
                       )
              ),
              
              # ══ DATA ANALYSIS ═════════════════════════════════════════════════════════
              tabPanel("🔍 Data Analysis",
                       div(class="g2",
                           div(class="gc",div(class="sl","Үнэ"),div(class="gt","Ангиллаар дундаж үнэ"),
                               div(class="gs","200,000₮ хүртэл"),plotlyOutput("p_price_cat",height="300px")),
                           div(class="gc",div(class="sl","Рейтинг"),div(class="gt","Ангиллаар дундаж рейтинг"),
                               div(class="gs","Рейтинг бүртгэгдсэн бүтээгдэхүүн"),plotlyOutput("p_rating_cat",height="300px"))
                       ),
                       div(class="gc",
                           div(class="sl","Violin"),div(class="gt","Ангиллаар рейтингийн хуваарилалт"),
                           div(class="gs","Тархалтын дүрслэл — violin + outlier цэгүүд"),
                           plotlyOutput("p_violin",height="380px")
                       ),
                       div(class="g2",
                           div(class="gc",div(class="sl","Брэнд"),div(class="gt","Шилдэг брэндүүд"),
                               div(class="gs","≥10 бүтээгдэхүүнтэй"),
                               selectInput("brand_sort","Эрэмбэлэх:",width="220px",
                                           choices=c("Бүтээгдэхүүний тоо"="n","Дундаж рейтинг"="avg_rating")),
                               plotlyOutput("p_brands",height="360px")),
                           div(class="gc",div(class="sl","Эх сурвалж"),div(class="gt","Дэлгүүрээр хуваарилалт"),
                               div(class="gs","Платформ бүрийн бүтээгдэхүүний тоо"),
                               plotlyOutput("p_source",height="360px"))
                       ),
                       div(class="gc",
                           div(class="sl","Орц × Арьс"),div(class="gt","Тохиромжийн heatmap"),
                           div(class="gs","Орц — арьсны төрлийн нийцэл (2=тохиромжтой · 1=болгоомж · -1=зайлсхий)"),
                           plotlyOutput("p_ing_heat",height="340px")
                       ),
                       div(class="gc",
                           div(class="sl","Дата"),div(class="gt","Бүтээгдэхүүний хүснэгт"),div(class="gs","Шүүж хайх"),
                           div(style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px",
                               div(style="width:200px",selectInput("tbl_cat","Ангилал:",choices=CATS)),
                               div(style="width:220px",selectInput("tbl_src","Дэлгүүр:",choices=SRCS))
                           ),
                           DTOutput("tbl_prods")
                       )
              ),
              
              # ══ STATISTICS ════════════════════════════════════════════════════════════
              tabPanel("📐 Statistics",
                       div(class="g2",
                           div(class="gc",
                               div(class="sl","Дескриптив"),div(class="gt","Тодорхойлох статистик"),
                               div(class="gs","Ангилал сонгоод харна уу"),
                               selectInput("stat_cat","Ангилал:",choices=CATS,width="220px"),
                               DTOutput("tbl_desc_stats")
                           ),
                           div(class="gc",div(class="sl","Boxplot — Үнэ"),div(class="gt","Үнийн хайрцаг диаграм"),
                               div(class="gs","Медиан · IQR · extreme утгууд"),plotlyOutput("p_box_price",height="340px"))
                       ),
                       div(class="g2",
                           div(class="gc",div(class="sl","Scatter + OLS"),div(class="gt","Үнэ ↔ Рейтинг"),
                               div(class="gs","OLS тренд шугамтай"),
                               selectInput("scat_cat","Ангилал:",choices=CATS,width="220px"),
                               plotlyOutput("p_scat",height="300px")),
                           div(class="gc",div(class="sl","Boxplot — Рейтинг"),div(class="gt","Рейтингийн хайрцаг диаграм"),
                               div(class="gs","Ангиллаар"),plotlyOutput("p_box_rating",height="340px"))
                       ),
                       div(class="gc",
                           div(class="sl","Корреляц"),div(class="gt","Корреляцийн матриц"),
                           div(class="gs","Үнэ × Рейтинг — Pearson r (2 хувьсагч)"),
                           plotlyOutput("p_corr",height="300px")
                       ),
                       div(class="gc",
                           div(class="sl","Статистик тест"),div(class="gt","Тестийн үр дүн"),
                           div(class="gs","Ангилал хооронд рейтингийн ялгаа байна уу?"),
                           div(class="g2",
                               div(class="tbox",
                                   tags$b(style="color:#a85570","Kruskal–Wallis тест — Рейтинг ~ Ангилал"),
                                   uiOutput("test_kw")),
                               div(class="tbox",
                                   tags$b(style="color:#a85570","Spearman корреляц — Үнэ ~ Рейтинг"),
                                   uiOutput("test_sp"))
                           )
                       ),
                       div(class="g2",
                           div(class="gc",
                               div(class="sl","Random Forest"),div(class="gt","Рейтинг таамаглах"),
                               div(class="mlnote","Хувьсагч: үнэ · ангилал · брэнд (label encoded). ntree=200"),
                               actionButton("run_rf","▶ Загвар ажиллуулах",class="bglow btn"),
                               uiOutput("rf_out"),
                               plotlyOutput("p_rf_imp",height="260px")
                           ),
                           div(class="gc",
                               div(class="sl","K-Means Clustering"),div(class="gt","Бүтээгдэхүүний кластер"),
                               div(class="mlnote","Хувьсагч: normalized үнэ · рейтинг"),
                               sliderInput("k_val","k (кластер тоо):",min=2,max=6,value=3,width="240px"),
                               actionButton("run_km","▶ Кластер ажиллуулах",class="bglow btn"),
                               uiOutput("km_out"),
                               plotlyOutput("p_km",height="280px")
                           )
                       )
              )
  )
)

# ── Server ────────────────────────────────────────────────────────────────────
server <- function(input, output, session) {
  
  P <- DAT$prods
  I <- DAT$ings
  B <- DAT$brands
  
  # ── EDA ──────────────────────────────────────────────────────────────────
  output$p_cat <- renderPlotly({
    df <- P |> count(category_name) |> arrange(n) |>
      mutate(category_name=factor(category_name,levels=category_name))
    plot_ly(df, x=~n, y=~category_name, type="bar", orientation="h",
            marker=list(color=rpal(nrow(df)), line=list(color="white",width=.8)),
            hovertemplate="<b>%{y}</b>: %{x}<extra></extra>") |>
      gl() |> layout(xaxis=list(title="Тоо",gridcolor="#f0dde4"), yaxis=list(title=""))
  })
  
  output$p_country <- renderPlotly({
    con <- dbConnect(SQLite(),DB)
    df  <- dbGetQuery(con,"
      SELECT COALESCE(NULLIF(NULLIF(b.country,''),'Unknown'),'Other') AS country,
             COUNT(DISTINCT p.product_id) AS n
      FROM products p JOIN brands b ON p.brand_id=b.brand_id
      GROUP BY country ORDER BY n DESC")
    dbDisconnect(con)
    nc <- nrow(df)
    cols <- rep_len(PAL9, nc)
    plot_ly(df, labels=~country, values=~n, type="pie",
            marker=list(colors=cols, line=list(color="white",width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b>: %{value}<extra></extra>") |>
      gl() |> layout(showlegend=TRUE)
  })
  
  output$p_price_hist <- renderPlotly({
    df <- P |> filter(!is.na(price_mnt), price_mnt>=1000, price_mnt<=input$price_cap)
    plot_ly(df, x=~price_mnt, type="histogram", nbinsx=40,
            marker=list(color=MAUVE, line=list(color=BLUSH,width=.6)),
            hovertemplate="₮%{x:,}<br>%{y} бүтээгдэхүүн<extra></extra>") |>
      gl() |> layout(bargap=.04,
                     xaxis=list(title="Үнэ (₮)",tickformat=",.0f",gridcolor="#f0dde4"),
                     yaxis=list(title="Тоо",gridcolor="#f0dde4"))
  })
  
  output$p_rating_hist <- renderPlotly({
    df <- P |> filter(!is.na(rating))
    plot_ly(df, x=~rating, type="histogram", nbinsx=20,
            marker=list(color=PLUM, line=list(color=BLUSH,width=.6)),
            hovertemplate="Рейтинг %{x}<br>%{y}<extra></extra>") |>
      gl() |> layout(bargap=.04,
                     xaxis=list(title="Рейтинг",gridcolor="#f0dde4"),
                     yaxis=list(title="Тоо",gridcolor="#f0dde4"))
  })
  
  output$p_top_ing <- renderPlotly({
    df <- I |> arrange(desc(product_count)) |> head(input$top_n) |>
      mutate(ingredient_name=factor(ingredient_name,levels=rev(ingredient_name)))
    plot_ly(df, x=~product_count, y=~ingredient_name, type="bar", orientation="h",
            marker=list(color=rpal(nrow(df)), line=list(color="white",width=.8)),
            hovertemplate="<b>%{y}</b>: %{x} бүтээгдэхүүн<extra></extra>") |>
      gl() |> layout(xaxis=list(title="Бүтээгдэхүүний тоо",gridcolor="#f0dde4"), yaxis=list(title=""))
  })
  
  # ── Data Analysis ─────────────────────────────────────────────────────────
  output$p_price_cat <- renderPlotly({
    df <- P |> filter(!is.na(price_mnt),price_mnt<200000) |>
      group_by(category_name) |> summarise(avg=mean(price_mnt),.groups="drop") |>
      arrange(avg) |> mutate(category_name=factor(category_name,levels=category_name))
    plot_ly(df, x=~avg, y=~category_name, type="bar", orientation="h",
            marker=list(color=rpal(nrow(df))),
            hovertemplate="<b>%{y}</b>: ₮%{x:,.0f}<extra></extra>") |>
      gl() |> layout(xaxis=list(title="Дундаж үнэ (₮)",tickformat=",.0f",gridcolor="#f0dde4"),
                     yaxis=list(title=""))
  })
  
  output$p_rating_cat <- renderPlotly({
    df <- P |> filter(!is.na(rating)) |>
      group_by(category_name) |> summarise(avg=mean(rating),.groups="drop") |>
      arrange(avg) |> mutate(category_name=factor(category_name,levels=category_name))
    plot_ly(df, x=~avg, y=~category_name, type="bar", orientation="h",
            marker=list(color=rpal(nrow(df))),
            hovertemplate="<b>%{y}</b>: %{x:.2f}<extra></extra>") |>
      gl() |> layout(xaxis=list(title="Дундаж рейтинг",range=c(3.8,5),gridcolor="#f0dde4"),
                     yaxis=list(title=""))
  })
  
  # Violin — ажлын зөв арга: нэг plot_ly() дотор loop хийж add_trace
  output$p_violin <- renderPlotly({
    df <- P |> filter(!is.na(rating), !is.na(category_name))
    # ангиллыг медианаар эрэмбэл
    ord <- df |> group_by(category_name) |>
      summarise(med=median(rating),.groups="drop") |>
      arrange(desc(med)) |> pull(category_name)
    nc   <- length(ord)
    cols <- setNames(rpal(nc), ord)
    
    p <- plot_ly()
    for (cat in ord) {
      vals <- df$rating[df$category_name == cat]
      p <- add_trace(p,
                     y           = vals,
                     type        = "violin",
                     name        = cat,
                     box         = list(visible=TRUE),
                     meanline    = list(visible=TRUE, color=INK, width=1.5),
                     line        = list(color=cols[[cat]], width=1.5),
                     fillcolor   = paste0(cols[[cat]],"55"),
                     points      = "outliers",
                     marker      = list(color=cols[[cat]], size=3, opacity=.5),
                     showlegend  = FALSE,
                     hovertemplate = paste0("<b>",cat,"</b><br>%{y:.2f}<extra></extra>")
      )
    }
    gl(p) |> layout(
      violingap      = 0.15,
      violingroupgap = 0.1,
      yaxis = list(title="Рейтинг", gridcolor="#f0dde4"),
      xaxis = list(title="")
    )
  })
  
  output$p_brands <- renderPlotly({
    df <- B |> filter(!is.na(avg_rating))
    if (input$brand_sort=="n") {
      df <- df |> arrange(desc(n)) |> head(15) |>
        mutate(brand_name=factor(brand_name,levels=rev(brand_name)))
      xv <- ~n; xt <- "Бүтээгдэхүүний тоо"
    } else {
      df <- df |> arrange(desc(avg_rating)) |> head(15) |>
        mutate(brand_name=factor(brand_name,levels=rev(brand_name)))
      xv <- ~avg_rating; xt <- "Дундаж рейтинг"
    }
    plot_ly(df, x=xv, y=~brand_name, type="bar", orientation="h",
            marker=list(color=rpal(nrow(df),MAUVE,PLUM)),
            hovertemplate="<b>%{y}</b>: %{x}<extra></extra>") |>
      gl() |> layout(xaxis=list(title=xt,gridcolor="#f0dde4"), yaxis=list(title=""))
  })
  
  output$p_source <- renderPlotly({
    df <- P |>
      mutate(src = case_when(
        is.na(source) | source == "" ~ "Бусад",
        source == "beautysecrets.mn"  ~ "beautysecrets.mn",
        source == "mimicorner.mn"     ~ "mimicorner.mn",
        source == "miruskincare.com"  ~ "miruskincare.com",
        TRUE                          ~ "Бусад"
      )) |>
      count(src) |>
      arrange(desc(n)) |>
      mutate(src=factor(src, levels=rev(src)))
    cols <- rpal(nrow(df), ROSE, PLUM)
    plot_ly(df, x=~n, y=~src, type="bar", orientation="h",
            marker=list(color=cols, line=list(color="white", width=.8)),
            text=~n, textposition="outside",
            hovertemplate="<b>%{y}</b>: %{x} бүтээгдэхүүн<extra></extra>") |>
      gl() |> layout(
        xaxis=list(title="Бүтээгдэхүүний тоо", gridcolor="#f0dde4"),
        yaxis=list(title=""),
        uniformtext=list(minsize=11, mode="show"))
  })
  
  # Heatmap — pivot_wider-г аюулгүй хийх
  output$p_ing_heat <- renderPlotly({
    suit_n <- function(s) case_when(
      s=="suitable" ~ 2L, s=="caution" ~ 1L, s=="avoid" ~ -1L, TRUE ~ 0L)
    
    df <- DAT$ing_skin |>
      mutate(score=suit_n(suitability)) |>
      # нэг орц-арьс хосд олон утга байж болох тул дундаж авна
      group_by(ingredient_name, skin_type_name) |>
      summarise(score=mean(score),.groups="drop") |>
      pivot_wider(names_from=skin_type_name, values_from=score, values_fill=0)
    
    # matrix болгох
    ing_names <- df$ingredient_name
    mat <- as.matrix(df[, -1, drop=FALSE])
    rownames(mat) <- ing_names
    skin_names <- colnames(mat)
    
    # annotation text
    ann_x <- rep(skin_names, each=nrow(mat))
    ann_y <- rep(ing_names, times=ncol(mat))
    ann_t <- as.character(as.vector(mat))
    
    plot_ly(
      x=skin_names, y=ing_names, z=mat,
      type="heatmap", zmin=-1, zmax=2,
      colorscale=list(
        list(0,"#b03030"), list(0.33,BLUSH), list(0.67,ROSE), list(1,PLUM)),
      hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Оноо: %{z}<extra></extra>"
    ) |>
      add_annotations(x=ann_x, y=ann_y, text=ann_t, showarrow=FALSE,
                      font=list(color=INK, size=12)) |>
      gl() |> layout(xaxis=list(title=""), yaxis=list(title="", autorange="reversed"))
  })
  
  output$tbl_prods <- renderDT({
    df <- P
    if (!is.null(input$tbl_cat) && input$tbl_cat!="Бүгд") df <- df|>filter(category_name==input$tbl_cat)
    if (!is.null(input$tbl_src) && input$tbl_src!="Бүгд") df <- df|>filter(source==input$tbl_src)
    df |> select(`Бүтээгдэхүүн`=product_name, `Брэнд`=brand_name,
                 `Ангилал`=category_name, `Үнэ ₮`=price_mnt,
                 `Рейтинг`=rating, `Дэлгүүр`=source) |>
      datatable(options=list(pageLength=12,scrollX=TRUE,
                             language=list(search="🔍 Хайх:")), rownames=FALSE, class="stripe hover") |>
      formatCurrency("Үнэ ₮",currency="₮",digits=0,mark=",",before=TRUE)
  })
  
  # ── Statistics ────────────────────────────────────────────────────────────
  output$tbl_desc_stats <- renderDT({
    df <- P
    if (!is.null(input$stat_cat)&&input$stat_cat!="Бүгд")
      df <- df|>filter(category_name==input$stat_cat)
    p_df <- df|>filter(!is.na(price_mnt),price_mnt<1000000)
    r_df <- df|>filter(!is.na(rating))
    tbl <- bind_rows(
      tibble(Хувьсагч="Үнэ (₮)", N=nrow(p_df),
             Дундаж=round(mean(p_df$price_mnt),0), Медиан=round(median(p_df$price_mnt),0),
             SD=round(sd(p_df$price_mnt),0), Min=min(p_df$price_mnt), Max=max(p_df$price_mnt),
             Q1=round(quantile(p_df$price_mnt,.25),0), Q3=round(quantile(p_df$price_mnt,.75),0)),
      tibble(Хувьсагч="Рейтинг", N=nrow(r_df),
             Дундаж=round(mean(r_df$rating),3), Медиан=round(median(r_df$rating),2),
             SD=round(sd(r_df$rating),3), Min=min(r_df$rating), Max=max(r_df$rating),
             Q1=round(quantile(r_df$rating,.25),2), Q3=round(quantile(r_df$rating,.75),2))
    )
    datatable(tbl, options=list(dom="t",ordering=FALSE), rownames=FALSE, class="stripe") |>
      formatStyle(names(tbl), color="#2d1520", fontWeight="600", fontSize="13px",
                  backgroundColor=styleRow(1:2,c("rgba(253,230,236,.2)","rgba(255,255,255,.4)")))
  })
  
  output$p_box_price <- renderPlotly({
    df <- P|>filter(!is.na(price_mnt),price_mnt<200000,price_mnt>1000)
    cats <- df|>count(category_name)|>arrange(desc(n))|>pull(category_name)
    cols <- setNames(rpal(length(cats)),cats)
    p <- plot_ly()
    for (cat in cats) {
      vals <- df$price_mnt[df$category_name==cat]
      p <- add_trace(p, y=vals, type="box", name=cat, boxpoints="outliers",
                     marker=list(color=cols[[cat]],size=3), line=list(color=cols[[cat]]),
                     fillcolor=paste0(cols[[cat]],"44"),
                     hovertemplate=paste0("<b>",cat,"</b><br>₮%{y:,}<extra></extra>"))
    }
    gl(p)|>layout(showlegend=FALSE,
                  yaxis=list(title="Үнэ (₮)",tickformat=",.0f",gridcolor="#f0dde4"),xaxis=list(title=""))
  })
  
  output$p_box_rating <- renderPlotly({
    df <- P|>filter(!is.na(rating))
    cats <- df|>count(category_name)|>arrange(desc(n))|>pull(category_name)
    cols <- setNames(rpal(length(cats),ROSE,PLUM),cats)
    p <- plot_ly()
    for (cat in cats) {
      vals <- df$rating[df$category_name==cat]
      p <- add_trace(p, y=vals, type="box", name=cat, boxpoints="outliers",
                     marker=list(color=cols[[cat]],size=3), line=list(color=cols[[cat]]),
                     fillcolor=paste0(cols[[cat]],"44"),
                     hovertemplate=paste0("<b>",cat,"</b><br>%{y:.2f}<extra></extra>"))
    }
    gl(p)|>layout(showlegend=FALSE,
                  yaxis=list(title="Рейтинг",gridcolor="#f0dde4"),xaxis=list(title=""))
  })
  
  output$p_scat <- renderPlotly({
    df <- P|>filter(!is.na(price_mnt),!is.na(rating),price_mnt<200000)
    if (!is.null(input$scat_cat)&&input$scat_cat!="Бүгд")
      df <- df|>filter(category_name==input$scat_cat)
    fit <- lm(rating~price_mnt,data=df)
    xr  <- range(df$price_mnt)
    tr  <- data.frame(price_mnt=seq(xr[1],xr[2],length.out=100))
    tr$rating <- predict(fit,tr)
    plot_ly() |>
      add_trace(data=df, x=~price_mnt, y=~rating, type="scatter", mode="markers",
                marker=list(color=MAUVE,size=5,opacity=.5), name="Бүтээгдэхүүн",
                hovertemplate="<b>%{customdata}</b><br>₮%{x:,} · ⭐%{y:.1f}<extra></extra>",
                customdata=df$product_name) |>
      add_trace(data=tr, x=~price_mnt, y=~rating, type="scatter", mode="lines",
                line=list(color=PLUM,width=2.5), name="OLS trend", hoverinfo="skip") |>
      gl() |> layout(
        xaxis=list(title="Үнэ (₮)",tickformat=",.0f",gridcolor="#f0dde4"),
        yaxis=list(title="Рейтинг",gridcolor="#f0dde4"),
        legend=list(orientation="h",y=-0.2))
  })
  
  # Correlation — зөвхөн price+rating, comedogenic байхгүй тул хасав
  output$p_corr <- renderPlotly({
    df <- P |> filter(!is.na(price_mnt),!is.na(rating),price_mnt<1000000) |>
      select(price_mnt, rating)
    
    # category-тай Pearson r
    cor_df <- P |> filter(!is.na(rating)) |>
      mutate(cat_id=as.numeric(factor(category_name))) |>
      filter(!is.na(cat_id)) |>
      select(price_mnt, rating, cat_id) |>
      filter(!is.na(price_mnt), price_mnt<1000000)
    
    cm  <- round(cor(cor_df, use="pairwise.complete.obs"), 3)
    vn  <- c("Үнэ","Рейтинг","Ангилал (encoded)")
    colnames(cm) <- vn; rownames(cm) <- vn
    
    ann_x <- rep(vn, each=length(vn))
    ann_y <- rep(vn, times=length(vn))
    ann_t <- as.character(as.vector(cm))
    
    plot_ly(x=vn, y=vn, z=cm, type="heatmap", zmin=-1, zmax=1,
            colorscale=list(list(0,"#7a3550"),list(0.5,CREAM),list(1,PLUM)),
            hovertemplate="%{x} × %{y}<br><b>r = %{z}</b><extra></extra>") |>
      add_annotations(x=ann_x, y=ann_y, text=ann_t, showarrow=FALSE,
                      font=list(color=INK,size=14)) |>
      gl() |> layout(xaxis=list(title=""), yaxis=list(title="",autorange="reversed"))
  })
  
  # Statistical tests
  output$test_kw <- renderUI({
    df  <- P|>filter(!is.na(rating),!is.na(category_name))
    res <- kruskal.test(rating~factor(category_name),data=df)
    chi <- round(as.numeric(res$statistic),3)
    dfv <- as.integer(res$parameter)
    pv  <- formatC(res$p.value,format="e",digits=3)
    sig <- if(res$p.value<0.001)"★★★ Маш өндөр ач холбогдолтой (p<0.001)"
    else if(res$p.value<0.01)"★★ p<0.01"
    else if(res$p.value<0.05)"★ p<0.05"
    else "Ач холбогдолгүй (p≥0.05)"
    div(class="tres", HTML(paste0(
      "χ² = <b>",chi,"</b><br>df = <b>",dfv,"</b><br>",
      "p  = <b>",pv,"</b><br>➜ ",sig)))
  })
  
  output$test_sp <- renderUI({
    df  <- P|>filter(!is.na(price_mnt),!is.na(rating),price_mnt<1000000)
    res <- cor.test(df$price_mnt,df$rating,method="spearman",exact=FALSE)
    rho <- round(as.numeric(res$estimate),4)
    pv  <- formatC(res$p.value,format="e",digits=3)
    sig <- if(res$p.value<0.001)"★★★ Маш өндөр ач холбогдолтой"
    else if(res$p.value<0.05)"★ Ач холбогдолтой" else "Ач холбогдолгүй"
    dir <- if(rho>0.1)"эерэг" else if(rho< -0.1)"сөрөг" else "маш сул"
    div(class="tres", HTML(paste0(
      "ρ = <b>",rho,"</b><br>p = <b>",pv,"</b><br>",
      "Чиглэл = <b>",dir,"</b><br>➜ ",sig)))
  })
  
  # Random Forest
  rf_res <- eventReactive(input$run_rf, {
    withProgress(message="Random Forest ажиллуулж байна…", value=.4, {
      df <- P |>
        filter(!is.na(rating),!is.na(price_mnt),price_mnt<1000000) |>
        mutate(cat_id=as.integer(factor(category_name)),
               brd_id=as.integer(factor(brand_name))) |>
        select(rating,price_mnt,cat_id,brd_id) |> na.omit()
      set.seed(42)
      idx <- sample(nrow(df),floor(.75*nrow(df)))
      tr  <- df[idx,]; te <- df[-idx,]
      rf  <- randomForest(rating~.,data=tr,ntree=200,importance=TRUE)
      pr  <- predict(rf,te)
      rmse <- round(sqrt(mean((pr-te$rating)^2)),4)
      r2   <- round(1-sum((pr-te$rating)^2)/sum((te$rating-mean(te$rating))^2),4)
      imp  <- as.data.frame(importance(rf))
      imp$Feature <- rownames(imp)
      imp <- imp |> arrange(desc(`%IncMSE`)) |>
        mutate(Feature=factor(Feature,levels=rev(Feature)))
      list(rmse=rmse,r2=r2,imp=imp,n_tr=nrow(tr),n_te=nrow(te))
    })
  })
  
  output$rf_out <- renderUI({
    req(rf_res()); m <- rf_res()
    div(class="tres", HTML(paste0(
      "Train N = <b>",m$n_tr,"</b>  Test N = <b>",m$n_te,"</b><br>",
      "RMSE = <b>",m$rmse,"</b><br>R² = <b>",m$r2,"</b><br>",
      "➜ ",if(m$r2>0.3)"Загвар сайн тайлбарлаж байна"
      else "Рейтинг бусад хүчин зүйлсээс хамаарч байна")))
  })
  
  output$p_rf_imp <- renderPlotly({
    req(rf_res())
    imp <- rf_res()$imp
    plot_ly(imp, x=~`%IncMSE`, y=~Feature, type="bar", orientation="h",
            marker=list(color=rpal(nrow(imp))),
            hovertemplate="<b>%{y}</b>: %{x:.3f}<extra></extra>") |>
      gl() |> layout(
        title=list(text="Feature Importance (%IncMSE)",font=list(size=12)),
        xaxis=list(title="%IncMSE",gridcolor="#f0dde4"), yaxis=list(title=""))
  })
  
  # K-Means
  km_res <- eventReactive(input$run_km, {
    withProgress(message="K-Means тооцоолж байна…", value=.4, {
      df <- P |>
        filter(!is.na(price_mnt),!is.na(rating),price_mnt>1000,price_mnt<200000) |>
        select(product_name,category_name,price_mnt,rating) |> na.omit()
      mat <- scale(df[,c("price_mnt","rating")])
      set.seed(42)
      km <- kmeans(mat,centers=input$k_val,nstart=25,iter.max=100)
      df$cluster <- paste0("C",km$cluster)
      list(df=df, k=input$k_val,
           wss=round(km$tot.withinss,1),
           sizes=paste(sort(as.integer(table(km$cluster))),collapse=" / "))
    })
  })
  
  output$km_out <- renderUI({
    req(km_res()); m <- km_res()
    div(class="tres", HTML(paste0(
      "k = <b>",m$k,"</b><br>",
      "Кластер хэмжээ: <b>",m$sizes,"</b><br>",
      "Дотоод SS: <b>",m$wss,"</b>")))
  })
  
  output$p_km <- renderPlotly({
    req(km_res())
    df <- km_res()$df
    clusts <- sort(unique(df$cluster))
    nc <- length(clusts)
    cols <- setNames(rpal(nc,PLUM,ROSE), clusts)
    p <- plot_ly()
    for (cl in clusts) {
      sub <- df[df$cluster==cl,]
      p <- add_trace(p, x=sub$price_mnt, y=sub$rating,
                     type="scatter", mode="markers", name=cl,
                     marker=list(color=cols[[cl]],size=5,opacity=.65),
                     hovertemplate=paste0("<b>",cl,"</b><br>₮%{x:,} · ⭐%{y:.1f}<extra></extra>"))
    }
    gl(p) |> layout(
      xaxis=list(title="Үнэ (₮)",tickformat=",.0f",gridcolor="#f0dde4"),
      yaxis=list(title="Рейтинг",gridcolor="#f0dde4"),
      legend=list(title=list(text="Кластер")))
  })
}

shinyApp(ui=ui, server=server)
