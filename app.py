import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Glow — Skincare Advisor", page_icon="🌸", layout="wide", initial_sidebar_state="expanded")

DB_PATH = str(Path.home() / "Downloads" / "skincare_project.db")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans',sans-serif!important}
.stApp{background:linear-gradient(135deg,#fdf4f7 0%,#fce8ee 50%,#f0e8f5 100%)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(253,244,247,.95),rgba(252,232,238,.95));border-right:1px solid rgba(201,123,150,.2)}
.block-container{max-width:1280px;padding-top:1.5rem;padding-bottom:2rem}
h1,h2,h3{color:#2e1a24!important;font-weight:700!important}
div[data-testid="metric-container"]{background:rgba(255,255,255,.78);border:1px solid rgba(201,123,150,.2);padding:20px;border-radius:18px;box-shadow:0 4px 20px rgba(158,80,112,.08);backdrop-filter:blur(12px)}
div[data-testid="metric-container"] label{color:#b6a9b1!important;font-size:12px!important;font-weight:600!important;letter-spacing:.5px}
div[data-testid="metric-container"] > div{color:#9e5070!important;font-size:26px!important;font-weight:700!important}
.stDataFrame{border-radius:16px!important;border:1px solid rgba(201,123,150,.15)!important}
div[data-baseweb="select"]>div{background:white!important;border-radius:12px!important;border:1.5px solid rgba(201,123,150,.2)!important}
.stButton>button{background:linear-gradient(135deg,#c97b96,#9e5070);color:white;border:none;border-radius:100px;padding:.6rem 1.4rem;font-weight:600;box-shadow:0 4px 16px rgba(158,80,112,.3)}
.hero-banner{background:linear-gradient(135deg,rgba(252,232,238,.8),rgba(234,213,240,.6));border:1px solid rgba(201,123,150,.2);border-radius:20px;padding:28px 32px;margin-bottom:24px}
.hero-label{font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#c97b96;margin-bottom:6px}
.hero-title{font-size:36px;font-weight:700;color:#2e1a24;margin:0 0 10px 0}
.hero-sub{font-size:15px;color:#b6a9b1;margin:0;line-height:1.6}
.econ-card{background:rgba(255,255,255,.78);border:1px solid rgba(201,123,150,.18);border-radius:18px;padding:20px 22px;margin-bottom:12px;box-shadow:0 4px 20px rgba(158,80,112,.07)}
.econ-label{font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#c97b96;margin-bottom:4px}
.econ-title{font-size:16px;font-weight:700;color:#2e1a24;margin-bottom:6px}
.econ-body{font-size:12px;color:#8a7a82;line-height:1.65}
.insight-box{background:rgba(242,167,184,.12);border-left:3px solid #f2a7b8;border-radius:0 10px 10px 0;padding:8px 12px;font-size:11px;color:#9e5070;font-weight:500;line-height:1.6;margin-top:8px}
.insight-box strong{display:block;font-size:10px;letter-spacing:.8px;text-transform:uppercase;color:#c97b96;margin-bottom:2px}
.section-label{font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:#c97b96;margin-bottom:4px}
.section-title{font-size:24px;font-weight:700;color:#2e1a24;margin:0 0 16px 0}
hr{border:none;border-top:1px solid rgba(201,123,150,.15)!important}
.footer-note{font-size:12px;color:#b6a9b1;text-align:center;padding:12px 0}
</style>
""", unsafe_allow_html=True)

ROSE="#f2a7b8"; MAUVE="#c97b96"; PLUM="#9e5070"; MIST="#b6a9b1"; INK="#2e1a24"; PETAL="#fdf4f7"
PALETTE=[ROSE,MAUVE,PLUM,"#e8c4d0","#d4a0b5","#ead5f0","#c8a8d8","#f5c6d0"]
CAT_MN={"Cleanser":"Угаагч","OilCleanser":"Тосон цэвэрлэгч","Toner":"Тонер","Serum":"Серум","Essence":"Эссенс","Moisturizer":"Чийгшүүлэх тос","Sunscreen":"Нарны тос","Mask":"Маск","Eye Care":"Нүдний арчилгаа","Other":"Бусад","Бүгд":"Бүгд"}
SKIN_MN={"Dry":"Хуурай","Oily":"Тосолог","Combination":"Холимог","Sensitive":"Эмзэг","Normal":"Хэвийн"}
CONC_MN={"Acne":"Батгашилж үрэвсэх","Dryness":"Хуурайшилт","Hyperpigmentation":"Нөсөө толбо","Inflammation":"Улайлт"}
RENAME={"product_name":"Бүтээгдэхүүн","brand_name":"Брэнд","category_name":"Ангилал","price_mnt":"Үнэ (₮)","rating":"Үнэлгээ","source":"Эх сурвалж","recommendation_score":"Оноо"}

def fs(ax,fig,title=""):
    fig.patch.set_facecolor(PETAL); ax.set_facecolor(PETAL)
    if title: ax.set_title(title,color=INK,fontsize=11,fontweight="bold",pad=8)
    ax.tick_params(axis="x",colors=INK,labelsize=8,rotation=20)
    ax.tick_params(axis="y",colors=MIST,labelsize=8)
    for s in ax.spines.values(): s.set_color("#f0d8e4")
    plt.tight_layout()

@st.cache_data(ttl=300)
def load_data():
    conn=sqlite3.connect(DB_PATH)
    pf=pd.read_sql_query("""SELECT p.product_id,p.product_name,b.brand_name,c.category_name,p.price_mnt,p.rating,p.source
        FROM products p LEFT JOIN brands b ON p.brand_id=b.brand_id LEFT JOIN categories c ON p.category_id=c.category_id
        WHERE p.price_mnt>0 AND p.price_mnt<1000000""",conn)
    cf=pd.read_sql_query("SELECT ic.ingredient_id,sc.concern_name,ic.effect_type FROM ingredient_concerns ic LEFT JOIN skin_concerns sc ON ic.concern_id=sc.concern_id",conn)
    sf=pd.read_sql_query("SELECT ist.ingredient_id,st.skin_type_name,ist.suitability FROM ingredient_skin_types ist LEFT JOIN skin_types st ON ist.skin_type_id=st.skin_type_id",conn)
    ig=pd.read_sql_query("SELECT pi.product_id,pi.ingredient_id,i.ingredient_name FROM product_ingredients pi LEFT JOIN ingredients i ON pi.ingredient_id=i.ingredient_id",conn)
    conn.close()
    pf["price_mnt"]=pd.to_numeric(pf["price_mnt"],errors="coerce")
    pf["rating"]=pd.to_numeric(pf["rating"],errors="coerce")
    return pf,cf,sf,ig

def build_rec(pf,cf,sf,ig,skin,concern,cat,brand,src,mn,mx):
    df=pf.copy()
    if cat!="Бүгд": df=df[df["category_name"]==cat]
    if brand!="Бүгд": df=df[df["brand_name"]==brand]
    if src!="Бүгд": df=df[df["source"]==src]
    df=df[(df["price_mnt"]>=mn)&(df["price_mnt"]<=mx)]
    m=df.merge(ig,on="product_id",how="left")
    if concern!="Бүгд":
        cm=cf[cf["concern_name"]==concern][["ingredient_id","effect_type"]]
        m=m.merge(cm,on="ingredient_id",how="left")
    else: m["effect_type"]=None
    if skin!="Бүгд":
        sm=sf[sf["skin_type_name"]==skin][["ingredient_id","suitability"]]
        m=m.merge(sm,on="ingredient_id",how="left")
    else: m["suitability"]=None
    def es(x): return 2 if x=="helpful" else -2 if x=="avoid" else -1 if x=="caution" else 0
    def ss(x): return 1 if x=="suitable" else -1 if x=="avoid" else 0
    m["cs"]=m["effect_type"].apply(es); m["ss"]=m["suitability"].apply(ss)
    g=m.groupby(["product_id","product_name","brand_name","category_name","price_mnt","rating","source"],dropna=False).agg(cs=("cs","sum"),ss=("ss","sum"),ic=("ingredient_id","nunique")).reset_index()
    g["recommendation_score"]=g["cs"]+g["ss"]+g["rating"].fillna(0)*0.6
    return g.sort_values(["recommendation_score","rating","price_mnt"],ascending=[False,False,True]).reset_index(drop=True)

pf,cf,sf,ig=load_data()

# SIDEBAR
st.sidebar.markdown("## 🌸 Шүүлт")
skin_opts=["Бүгд"]+sorted(sf["skin_type_name"].dropna().unique())
conc_opts=["Бүгд"]+sorted(cf["concern_name"].dropna().unique())
cat_opts=["Бүгд"]+sorted(pf["category_name"].dropna().unique())
brand_opts=["Бүгд"]+sorted(pf["brand_name"].dropna().unique())
src_opts=["Бүгд"]+sorted(pf["source"].dropna().unique())
si=st.sidebar.selectbox("Арьсны төрөл",range(len(skin_opts)),format_func=lambda i:SKIN_MN.get(skin_opts[i],skin_opts[i]))
ci=st.sidebar.selectbox("Арьсны асуудал",range(len(conc_opts)),format_func=lambda i:CONC_MN.get(conc_opts[i],conc_opts[i]))
ti=st.sidebar.selectbox("Ангилал",range(len(cat_opts)),format_func=lambda i:CAT_MN.get(cat_opts[i],cat_opts[i]))
sel_brand=st.sidebar.selectbox("Брэнд",brand_opts)
sel_src=st.sidebar.selectbox("Эх сурвалж",src_opts)
max_p=min(int(pf["price_mnt"].max()),500000); min_p=int(pf["price_mnt"].min())
min_price,max_price=st.sidebar.slider("Үнийн хязгаар (₮)",min_value=min_p,max_value=max_p,value=(min_p,max_p),step=1000,format="%d₮")
sel_skin=skin_opts[si]; sel_concern=conc_opts[ci]; sel_cat=cat_opts[ti]

# HERO
st.markdown("""<div class="hero-banner">
  <div class="hero-label">✦ Орц найрлага дээр суурилсан · AI зөвлөгч</div>
  <div class="hero-title">🌸 Glow — Skincare Advisor</div>
  <p class="hero-sub">Арьсны төрөл болон тулгамдсан асуудлаасаа хамааруулан — орц найрлагын дүн шинжилгээнд тулгуурлан таны арьсанд хамгийн тохирох бүтээгдэхүүнийг зөвлөнө.<br/>
  <strong style="color:#c97b96">3,124 бүтээгдэхүүн · 138 брэнд · 5 вэбсайт</strong></p>
</div>""", unsafe_allow_html=True)

rec_df=build_rec(pf,cf,sf,ig,sel_skin,sel_concern,sel_cat,sel_brand,sel_src,min_price,max_price)

# KPI
c1,c2,c3,c4=st.columns(4)
total=len(rec_df); avg_p=rec_df["price_mnt"].mean() if total else 0
avg_r=rec_df["rating"].mean() if total else 0; top_b=rec_df["brand_name"].mode()[0] if total else "—"
c1.metric("🌸 Тохирох бүтээгдэхүүн",f"{total:,}")
c2.metric("💰 Дундаж үнэ",f"{avg_p:,.0f}₮")
c3.metric("⭐ Дундаж үнэлгээ",f"{avg_r:.2f}" if avg_r else "—")
c4.metric("🏆 Тэргүүлэх брэнд",top_b)
st.markdown("---")

# ═══════════════════════════════════════
# 📊 ЭДИЙН ЗАСГИЙН ШИНЖИЛГЭЭ
# ═══════════════════════════════════════
st.markdown('<div class="section-label">Эдийн засгийн шинжилгээ</div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">📊 Зах зээлийн дүн шинжилгээ</div>',unsafe_allow_html=True)

cat_stats=pf[pf["price_mnt"]<500000].groupby("category_name").agg(Тоо=("product_id","count"),avg=("price_mnt","mean"),med=("price_mnt","median")).reset_index().sort_values("avg",ascending=False)
cat_stats["Ангилал"]=cat_stats["category_name"].map(lambda x:CAT_MN.get(x,x))

# ROW 1
r1a,r1b=st.columns(2)
with r1a:
    st.markdown('<div class="econ-card"><div class="econ-label">Үнийн шинжилгээ</div><div class="econ-title">Ангилалаар дундаж үнэ</div><div class="econ-body">Серум хамгийн үнэтэй ангилал — active ingredient-ийн концентраци өндөр байдагтай холбоотой. Маск хамгийн хямд хэдий ч хамгийн их тоотой.</div><div class="insight-box"><strong>Premium Pricing Signal</strong>Серумын өндөр үнэ нь R&D зардал болон хэрэглэгчийн perceived efficacy-тай шууд холбоотой — "you get what you pay for" итгэл үнэмшлийг ашигладаг.</div></div>',unsafe_allow_html=True)
    fig,ax=plt.subplots(figsize=(6,3.8))
    ax.barh(cat_stats["Ангилал"],cat_stats["avg"],color=MAUVE,alpha=0.8,height=0.55,label="Дундаж")
    ax.barh(cat_stats["Ангилал"],cat_stats["med"],color=ROSE,alpha=0.6,height=0.55,label="Медиан")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k₮"))
    ax.legend(fontsize=8); fs(ax,fig,"")
    st.pyplot(fig)

with r1b:
    st.markdown('<div class="econ-card"><div class="econ-label">Үнийн тархалт</div><div class="econ-title">Ангилал тус бүрийн үнийн хүрээ</div><div class="econ-body">Box plot: медиан, дээд/доод хязгаар, outlier-ийг харуулна. Серум, чийгшүүлэгчийн үнийн тархалт өргөн — зах зээлийн сегментчлэл тод.</div><div class="insight-box"><strong>Versioning Strategy</strong>Нэг ангилал доторх өргөн үнийн хүрээ нь брэндүүд нэг бүтээгдэхүүнийг олон сегментэд зарах стратегийн илрэл.</div></div>',unsafe_allow_html=True)
    pdf2=pf[pf["price_mnt"]<300000].copy()
    pdf2["Ангилал"]=pdf2["category_name"].map(lambda x:CAT_MN.get(x,x))
    cats_ord=cat_stats["Ангилал"].tolist()
    gbox=[pdf2[pdf2["Ангилал"]==c]["price_mnt"].dropna().values for c in cats_ord]
    fig2,ax2=plt.subplots(figsize=(6,3.8))
    bp=ax2.boxplot(gbox,labels=cats_ord,patch_artist=True,medianprops=dict(color=PLUM,linewidth=2),
        whiskerprops=dict(color=MAUVE),capprops=dict(color=MAUVE),flierprops=dict(marker="o",color=ROSE,alpha=0.3,markersize=2))
    for i,patch in enumerate(bp["boxes"]): patch.set_facecolor(PALETTE[i%len(PALETTE)]); patch.set_alpha(0.7)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k"))
    fs(ax2,fig2,""); st.pyplot(fig2)

st.markdown("<br/>",unsafe_allow_html=True)

# ROW 2
r2a,r2b=st.columns(2)
src_stats=pf[pf["price_mnt"]<500000].groupby("source").agg(Тоо=("product_id","count"),avg_p=("price_mnt","mean"),med_p=("price_mnt","median"),avg_r=("rating","mean")).reset_index().dropna(subset=["source"])

with r2a:
    st.markdown('<div class="econ-card"><div class="econ-label">Платформ харьцуулалт</div><div class="econ-title">Вэбсайтаар дундаж үнэ</div><div class="econ-body">Платформ бүр өөр үнийн сегментэд төвлөрдөг. Beautysecrets.mn дундаж үнэ хамгийн өндөр — premium брэнд илүү их агуулна.</div><div class="insight-box"><strong>Платформ эдийн засаг</strong>E-commerce платформ бүр өөр buyer persona-тай — үнийн зөрүү нь target сегментийн ялгааг харуулна.</div></div>',unsafe_allow_html=True)
    fig3,ax3=plt.subplots(figsize=(6,3.8))
    bars3=ax3.bar(src_stats["source"],src_stats["avg_p"],color=PALETTE[:len(src_stats)],alpha=0.88,edgecolor="white")
    for bar,val in zip(bars3,src_stats["avg_p"]):
        ax3.text(bar.get_x()+bar.get_width()/2,bar.get_height()+300,f"{val/1000:.1f}k₮",ha="center",va="bottom",fontsize=8,color=INK,fontweight="600")
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k"))
    ax3.set_ylabel("Дундаж үнэ (₮)",color=MIST,fontsize=8)
    fs(ax3,fig3,""); st.pyplot(fig3)

with r2b:
    st.markdown('<div class="econ-card"><div class="econ-label">Зах зээлийн хувь</div><div class="econ-title">Бүтээгдэхүүний тоогоор зах зээлийн хувь</div><div class="econ-body">Beautysecrets.mn нийт бүтээгдэхүүний 55%-ийг эзэлж байна — зах зээлийн давамгайлах оролцогч.</div><div class="insight-box"><strong>Market Concentration (HHI)</strong>Нэг платформ >50% эзэлбэл зах зээлийн концентраци өндөр — Herfindahl-Hirschman Index судлах сонирхолтой сэдэв.</div></div>',unsafe_allow_html=True)
    fig4,ax4=plt.subplots(figsize=(5.5,3.8))
    wedges,texts,autotexts=ax4.pie(src_stats["Тоо"],labels=src_stats["source"],autopct="%1.1f%%",
        colors=PALETTE[:len(src_stats)],startangle=140,pctdistance=0.78,wedgeprops=dict(edgecolor="white",linewidth=1.5))
    for t in texts: t.set_fontsize(8); t.set_color(INK)
    for at in autotexts: at.set_fontsize(8); at.set_color("white"); at.set_fontweight("bold")
    fig4.patch.set_facecolor(PETAL); plt.tight_layout()
    st.pyplot(fig4)

st.markdown("<br/>",unsafe_allow_html=True)

# ROW 3
r3a,r3b=st.columns(2)
with r3a:
    st.markdown('<div class="econ-card"><div class="econ-label">Үнийн бүтэц</div><div class="econ-title">Нийт үнийн тархалт</div><div class="econ-body">Үнийн тархалт баруун тийш хазайсан (right-skewed) — олонх бүтээгдэхүүн 20,000–60,000₮ хооронд. Монголын зах зээлийн худалдан авах чадварын дунджийг тусгана.</div><div class="insight-box"><strong>Right-skewed тархалт</strong>Mass-market бүтээгдэхүүн давамгайлдаг ч luxury tail нь орлого дээд 10%-ийг чиглэдэг — эдийн засгийн тэгш бус байдлын илрэл.</div></div>',unsafe_allow_html=True)
    dh=pf["price_mnt"].dropna(); dh=dh[dh<200000]
    fig5,ax5=plt.subplots(figsize=(6,3.8))
    ax5.hist(dh,bins=30,color=MAUVE,alpha=0.8,edgecolor="white",linewidth=0.5)
    ax5.axvline(dh.mean(),color=PLUM,linestyle="--",linewidth=1.8,label=f"Дундаж: {dh.mean():,.0f}₮")
    ax5.axvline(dh.median(),color=ROSE,linestyle=":",linewidth=1.8,label=f"Медиан: {dh.median():,.0f}₮")
    ax5.legend(fontsize=8)
    ax5.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k"))
    ax5.set_xlabel("Үнэ (₮)",color=MIST,fontsize=8)
    ax5.set_ylabel("Тоо",color=MIST,fontsize=8)
    fs(ax5,fig5,""); st.pyplot(fig5)

with r3b:
    st.markdown('<div class="econ-card"><div class="econ-label">Зах зээлийн сегментчлэл</div><div class="econ-title">Үнийн сегментээр бүтээгдэхүүний тоо</div><div class="econ-body">Budget (&lt;20k₮), Mid-range (20-50k₮), Premium (50-100k₮), Luxury (&gt;100k₮) гэсэн 4 сегментэд хуваасан.</div><div class="insight-box"><strong>Market Segmentation</strong>Mid-range сегмент хамгийн их — "squeezed middle" үзэгдэл. Premium-тай өрсөлдөхийн тулд брэндүүд differentiation стратеги ашиглана.</div></div>',unsafe_allow_html=True)
    bins=[0,20000,50000,100000,1000000]
    labels_seg=["Budget\n<20k₮","Mid-range\n20-50k₮","Premium\n50-100k₮","Luxury\n>100k₮"]
    sd=pf[pf["price_mnt"]>0].copy()
    sd["seg"]=pd.cut(sd["price_mnt"],bins=bins,labels=labels_seg)
    sc=sd["seg"].value_counts().reindex(labels_seg)
    fig6,ax6=plt.subplots(figsize=(6,3.8))
    bars6=ax6.bar(labels_seg,sc.values,color=PALETTE[:4],alpha=0.88,edgecolor="white",linewidth=1)
    for bar,val in zip(bars6,sc.values):
        ax6.text(bar.get_x()+bar.get_width()/2,bar.get_height()+5,str(val),ha="center",va="bottom",fontsize=9,color=INK,fontweight="700")
    ax6.set_ylabel("Бүтээгдэхүүний тоо",color=MIST,fontsize=8)
    ax6.tick_params(axis="x",rotation=0)
    fs(ax6,fig6,""); st.pyplot(fig6)

st.markdown("<br/>",unsafe_allow_html=True)

# ROW 4: Корреляц + Брэнд үнэ
r4a,r4b=st.columns(2)
with r4a:
    st.markdown('<div class="econ-card"><div class="econ-label">Корреляцийн шинжилгээ</div><div class="econ-title">Үнэ ба үнэлгээний хамаарал</div><div class="econ-body">Үнэ өндөр байвал үнэлгээ мөн өндөр байх уу? "Price-quality relationship" судалгааны гол асуулт.</div><div class="insight-box"><strong>Price-Quality Relationship</strong>Корреляц сул байвал хэрэглэгчид үнэ биш бүтээгдэхүүний үр дүнг илүү үнэлдэг — Монголын зах зээлийн онцлог шинж.</div></div>',unsafe_allow_html=True)
    rated=pf[(pf["rating"].notna())&(pf["price_mnt"]<200000)].copy()
    corr=rated["price_mnt"].corr(rated["rating"])
    fig7,ax7=plt.subplots(figsize=(6,3.8))
    ax7.scatter(rated["price_mnt"],rated["rating"],alpha=0.2,color=MAUVE,s=12,edgecolors="none")
    z=np.polyfit(rated["price_mnt"].dropna(),rated["rating"].dropna(),1)
    xs=np.linspace(rated["price_mnt"].min(),rated["price_mnt"].max(),100)
    ax7.plot(xs,np.poly1d(z)(xs),color=PLUM,linewidth=2,linestyle="--",label=f"r = {corr:.3f}")
    ax7.legend(fontsize=9); ax7.set_xlabel("Үнэ (₮)",color=MIST,fontsize=8); ax7.set_ylabel("Үнэлгээ ★",color=MIST,fontsize=8)
    ax7.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k"))
    fs(ax7,fig7,""); st.pyplot(fig7)

with r4b:
    st.markdown('<div class="econ-card"><div class="econ-label">Брэндийн шинжилгээ</div><div class="econ-title">Топ брэндүүдийн дундаж үнэ</div><div class="econ-body">Eco Your Skin хамгийн өндөр дундаж үнэтэй — premium positioning. Зарим брэнд low-price strategy ашиглаж volume-аар орлого нэмдэг.</div><div class="insight-box"><strong>Brand Positioning</strong>Үнийн стратеги нь брэндийн зах зээл дэх байрлалыг тодорхойлно — Premium vs. Value vs. Economy сегментүүд.</div></div>',unsafe_allow_html=True)
    bs=pf[pf["price_mnt"]<500000].groupby("brand_name").agg(n=("product_id","count"),avg_p=("price_mnt","mean")).reset_index()
    tb=bs[bs["n"]>=5].nlargest(12,"avg_p")
    fig8,ax8=plt.subplots(figsize=(6,3.8))
    ax8.barh(tb["brand_name"],tb["avg_p"],color=[PALETTE[i%len(PALETTE)] for i in range(len(tb))],alpha=0.85,height=0.65)
    ax8.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x/1000:.0f}k₮"))
    ax8.set_xlabel("Дундаж үнэ (₮)",color=MIST,fontsize=8)
    fs(ax8,fig8,""); st.pyplot(fig8)

st.markdown("---")

# RECOMMENDATIONS TABLE
st.markdown('<div class="section-label">Зөвлөмж</div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">Таны арьсанд тохирох бүтээгдэхүүнүүд</div>',unsafe_allow_html=True)
show_cols=["product_name","brand_name","category_name","price_mnt","rating","source","recommendation_score"]
exist=[c for c in show_cols if c in rec_df.columns]
disp=rec_df[exist].head(30).rename(columns=RENAME)
if "Үнэ (₮)" in disp.columns: disp["Үнэ (₮)"]=disp["Үнэ (₮)"].apply(lambda x:f"{x:,.0f}₮" if pd.notna(x) else "—")
if "Үнэлгээ" in disp.columns: disp["Үнэлгээ"]=disp["Үнэлгээ"].apply(lambda x:f"★{x:.1f}" if pd.notna(x) else "—")
if "Ангилал" in disp.columns: disp["Ангилал"]=disp["Ангилал"].map(lambda x:CAT_MN.get(x,x))
if "Оноо"    in disp.columns: disp["Оноо"]=disp["Оноо"].apply(lambda x:f"{x:.1f}")
st.dataframe(disp,use_container_width=True,height=380)

lc2,rc2=st.columns(2)
with lc2:
    if not rec_df.empty:
        cc=rec_df["category_name"].map(lambda x:CAT_MN.get(x,x)).value_counts().head(8)
        fc,ac=plt.subplots(figsize=(6,3.2))
        ac.bar(cc.index,cc.values,color=PALETTE[:len(cc)],alpha=0.85,edgecolor="white")
        ac.set_ylabel("Тоо",color=MIST,fontsize=8); fs(ac,fc,"Ангилалаар"); st.pyplot(fc)
with rc2:
    if not rec_df.empty:
        bc=rec_df["brand_name"].value_counts().head(10)
        fb,ab=plt.subplots(figsize=(6,3.2))
        ab.barh(bc.index,bc.values,color=PALETTE[:len(bc)],alpha=0.85)
        ab.set_xlabel("Тоо",color=MIST,fontsize=8); fs(ab,fb,"Топ брэндүүд"); st.pyplot(fb)

st.markdown("---")

# QUICK CONCERN
st.markdown('<div class="section-label">Хурдан сонголт</div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">Асуудлаар нь шуурхай</div>',unsafe_allow_html=True)
qc_map={"🌿 Батгашилж үрэвсэх":"Acne","💧 Хуурайшилт":"Dryness","✨ Нөсөө толбо":"Hyperpigmentation","🌸 Улайлт":"Inflammation"}
qc_lbl=st.selectbox("Асуудал сонгох",list(qc_map.keys()))
qdf=build_rec(pf,cf,sf,ig,"Бүгд",qc_map[qc_lbl],"Бүгд","Бүгд","Бүгд",min_p,max_p)
qshow=["product_name","brand_name","category_name","price_mnt","rating","source"]
qd=qdf[[c for c in qshow if c in qdf.columns]].head(10).rename(columns=RENAME)
if "Үнэ (₮)" in qd.columns: qd["Үнэ (₮)"]=qd["Үнэ (₮)"].apply(lambda x:f"{x:,.0f}₮" if pd.notna(x) else "—")
if "Ангилал" in qd.columns: qd["Ангилал"]=qd["Ангилал"].map(lambda x:CAT_MN.get(x,x))
st.dataframe(qd,use_container_width=True)
st.markdown("---")

# PRODUCT DETAIL
st.markdown('<div class="section-label">Дэлгэрэнгүй</div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">Бүтээгдэхүүн шалгах</div>',unsafe_allow_html=True)
sel_prod=st.selectbox("Бүтээгдэхүүн сонгох",["—"]+rec_df["product_name"].tolist())
if sel_prod!="—":
    row=rec_df[rec_df["product_name"]==sel_prod].iloc[0]
    iv=ig[ig["product_id"]==row["product_id"]][["ingredient_name"]].drop_duplicates()
    il,ir=st.columns([1.3,1])
    with il:
        st.markdown("**Бүтээгдэхүүний мэдээлэл**")
        for k,v in {"Нэр":row["product_name"],"Брэнд":row.get("brand_name","—"),"Ангилал":CAT_MN.get(row.get("category_name",""),"—"),
            "Үнэ":f"{row['price_mnt']:,.0f}₮" if pd.notna(row.get("price_mnt")) else "—",
            "Үнэлгээ":f"★{row['rating']:.1f}" if pd.notna(row.get("rating")) else "—",
            "Эх сурвалж":row.get("source","—"),"Оноо":f"{row['recommendation_score']:.2f}"}.items():
            st.markdown(f"**{k}:** {v}")
    with ir:
        st.markdown("**Орц найрлага**")
        if iv.empty: st.info("Орц мэдээлэл байхгүй")
        else: st.dataframe(iv.rename(columns={"ingredient_name":"Орц"}),use_container_width=True)

with st.expander("📋 Бүх бүтээгдэхүүн харах"):
    st.dataframe(pf.rename(columns={"product_name":"Нэр","brand_name":"Брэнд","category_name":"Ангилал","price_mnt":"Үнэ","rating":"Үнэлгээ","source":"Эх сурвалж"}),use_container_width=True)

st.markdown("---")
st.markdown('<div class="footer-note">✦ <strong>Glow</strong> — Монголын гоо сайхны арьс арчилгааны зөвлөгч · beautysecrets.mn · mimicorner.mn · miruskincare.com</div>',unsafe_allow_html=True)
