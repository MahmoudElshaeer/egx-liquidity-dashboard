import re
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

# =========================
# App Meta (حقوق + About)
# =========================
APP_TITLE = "مراقب السيولة"
APP_SUBTITLE = "EGX Liquidity Monitor Dashboard"
APP_VERSION = "1.1.0"
AUTHOR = "Mahmoud Abdrabbo"
COPYRIGHT = f"© 2026 {AUTHOR}. All rights reserved."
DISCLAIMER = "هذا التطبيق لأغراض معلوماتية فقط ولا يُعد توصية استثمارية."

WHATSAPP_URL = "https://wa.me/qr/37OH2UF3VH7PM1"
TELEGRAM_URL = "https://t.me/Mahmoud_abdrabbo"
EMAIL = "mahmoud_elshaeer@yahoo.com"

st.set_page_config(page_title=APP_TITLE, layout="wide")

PROJECT_DIR = Path(__file__).resolve().parent
README_PATH = PROJECT_DIR / "README.md"

# للـ Cloud: خلي الملف في نفس الريبو باسم liquidity_all.xlsx
#DATA_PATH = PROJECT_DIR / "liquidity_all.xlsx"
DATA_PATH = Path(__file__).resolve().parent / "liquidity_all.xlsx"

# =========================
# CSS (تكبير التابات + عناوين)
# =========================
st.markdown(
    """
    <style>
    /* تكبير خط التابات */
    div[data-baseweb="tab"] > button {
        font-size: 26px !important;
        font-weight: 800 !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
    }
    /* تكبير عنوان الصفحة */
    h1 { font-size: 42px !important; }
    /* تكبير عناوين الأقسام */
    h2 { font-size: 32px !important; }
    h3 { font-size: 26px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# اسماء مصححة حسب الرمز (Overrides)
# =========================
NAME_OVERRIDES = {
    "COMI": "البنك التجاري الدولي",
    "HDBK": "بنك التعمير والإسكان",
    "ADIB": "مصرف أبوظبي الإسلامي",
    "CCAP": "القلعة",
    "CLHO": "مستشفى كليوباترا",
    "EAST": "إيسترن كومباني",
    "FWRY": "فوري",
    "BTFH": "بلتون القابضة",
    "ACAMD": "الشركة العربية لإدارة وتطوير الأصول",
    "ABUK": "أبوقير للأسمدة",
    "TAQA": "طاقة عربية",
    "TMGH": "طلعت مصطفى",
    "HRHO": "مجموعة إي إف جي القابضة",
    "HELI": "مصر الجديدة للإسكان",
    "ETRS": "إيجيترانس",
    "ZEOT": "الزيوت المستخلصة",
    "ORAS": "أوراسكوم للإنشاء",
    "EGAL": "مصر للألومنيوم",
    "CRST": "كرستمارك للمقاولات",
    "OIH": "أوراسكوم للاستثمار القابضة",
    "MFPC": "موبكو",
    "ISMQ": "الحديد والصلب للمناجم والمحاجر",
    "EGCH": "كيما",
    "NCCW": "النصر للأعمال المدنية",
    "AMER": "عامر جروب",
    "PHGC": "بريميم هيلثكير جروب",
    "PHDC": "بالم هيلز",
    "RAYA": "راية",
    # إضافات من قائمتك:
    "ARAB": "المطورون العرب القابضة",
}

# =========================
# تنظيف/تطبيع عربي (General cleanup)
# =========================
ARABIC_TATWEEL = "\u0640"
ARABIC_DIACRITICS_RE = re.compile(r"[\u0617-\u061A\u064B-\u0652]")

def is_arabic_char(ch: str) -> bool:
    return "\u0600" <= ch <= "\u06FF"

def normalize_arabic_name(s: str) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""

    s = str(s)

    # إزالة اتجاه/رموز خفية
    s = (s.replace("\u200f", "")
           .replace("\u200e", "")
           .replace("\u202b", "")
           .replace("\u202a", "")
           .replace("\xa0", " ")
           .replace(ARABIC_TATWEEL, "")
        )

    # إزالة التشكيل
    s = ARABIC_DIACRITICS_RE.sub("", s)

    # توحيد مسافات
    s = re.sub(r"\s+", " ", s).strip()

    # دمج الحروف اللي الـ OCR فصلها: "كومبان ي" -> "كومباني" / "سي أي ب  ي" -> "سي أي بي"
    tokens = s.split(" ")
    merged = []
    for tok in tokens:
        if len(tok) == 1 and merged and is_arabic_char(tok) and all(is_arabic_char(c) for c in merged[-1][-1:]):
            merged[-1] = merged[-1] + tok
        else:
            merged.append(tok)
    s = " ".join(merged)

    # إصلاحات OCR شائعة
    fixes = [
        ("مرصف", "مصرف"),
        ("مرص", "مصر"),
        ("مستشف", "مستشفى"),
        ("واإ", "والإ"),
        ("اإ", "الإ"),
        ("اال", "ال"),  # االصول -> الاصول (تقريب)
        ("ايست  ن", "ايسترن"),
        ("كومبائني", "كومباني"),
        ("كومبان ي", "كومباني"),
    ]
    for a, b in fixes:
        s = s.replace(a, b)

    return s.strip()

# =========================
# Load + unify columns
# =========================
@st.cache_data
def load_data_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    df = df.rename(columns={
        "صافى السيولة": "صافي السيولة",
        "أخر سعر": "آخر سعر",
        "% مخطط السيولة": "نسبة مخطط السيولة",
        "التغير%": "التغير %",
        "التغير % ": "التغير %",
        "الاسم": "الإسم",
    })

    required = ["التاريخ", "الرمز", "السيولة الداخلة", "السيولة الخارجة", "صافي السيولة"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"أعمدة ناقصة في الملف: {missing}")

    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")

    # تحويل أرقام
    num_cols = [
        "آخر سعر", "التغير %", "قيمة التداول",
        "السيولة الداخلة", "السيولة الخارجة", "صافي السيولة",
        "نسبة مخطط السيولة", "رقم الصفحة"
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.replace(",", "", regex=False).str.strip()
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["التاريخ", "الرمز"]).copy()

    # تنظيف الأسماء العربية + Overrides
    if "الإسم" in df.columns:
        df["اسم_منظف"] = df["الإسم"].apply(normalize_arabic_name)
    else:
        df["اسم_منظف"] = ""

    df["اسم_نهائي"] = df.apply(
        lambda r: NAME_OVERRIDES.get(str(r["الرمز"]).strip(), r["اسم_منظف"]),
        axis=1
    )
    df["اسم_نهائي"] = df["اسم_نهائي"].fillna("").astype(str).str.strip()
    return df

@st.cache_data
def load_data_from_excel(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    return load_data_df(df)

@st.cache_data
def load_data_from_uploaded(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(file_bytes)
    return load_data_df(df)

# =========================
# Helpers
# =========================
def fmt_money(x):
    if x is None or pd.isna(x):
        return "-"
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e9:  return f"{sign}{x/1e9:.2f}B"
    if x >= 1e6:  return f"{sign}{x/1e6:.2f}M"
    if x >= 1e3:  return f"{sign}{x/1e3:.2f}K"
    return f"{sign}{x:.0f}"

def consecutive_positive_days(df_sym):
    s = df_sym.sort_values("التاريخ")["صافي السيولة"].fillna(0).tolist()
    cnt = 0
    for v in reversed(s):
        if v > 0:
            cnt += 1
        else:
            break
    return cnt

def style_net_column(v):
    if pd.isna(v):
        return ""
    if v > 0:
        return "color: #00C853; font-weight: 800;"
    if v < 0:
        return "color: #D50000; font-weight: 800;"
    return ""

def weighted_mean(values, weights):
    v = pd.to_numeric(values, errors="coerce")
    w = pd.to_numeric(weights, errors="coerce")
    mask = v.notna() & w.notna() & (w > 0)
    if mask.sum() == 0:
        return None
    return float((v[mask] * w[mask]).sum() / w[mask].sum())

def get_change_metric(scope_df: pd.DataFrame, mode: str):
    if "التغير %" not in scope_df.columns or scope_df.empty:
        return "-", None

    if mode == "آخر جلسة":
        last_row = scope_df.sort_values("التاريخ").iloc[-1]
        v = last_row.get("التغير %")
        return ("-" if pd.isna(v) else f"{v:.2f}%"), None

    if mode == "متوسط":
        v = scope_df["التغير %"].mean()
        if pd.isna(v):
            return "-", None
        last_v = scope_df.sort_values("التاريخ").iloc[-1].get("التغير %")
        delta = f"آخر جلسة: {last_v:.2f}%" if not pd.isna(last_v) else None
        return f"{v:.2f}%", delta

    if mode == "متوسط مرجّح (قيمة التداول)":
        if "قيمة التداول" not in scope_df.columns:
            return "-", None
        v = weighted_mean(scope_df["التغير %"], scope_df["قيمة التداول"])
        if v is None:
            return "-", None
        last_v = scope_df.sort_values("التاريخ").iloc[-1].get("التغير %")
        delta = f"آخر جلسة: {last_v:.2f}%" if not pd.isna(last_v) else None
        return f"{v:.2f}%", delta

    return "-", None

def add_watermark(fig, text=COPYRIGHT):
    # بصمة خفيفة على الرسومات
    fig.add_annotation(
        text=text,
        xref="paper", yref="paper",
        x=0.99, y=0.01,
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        opacity=0.35,
        font=dict(size=12),
    )
    return fig

# =========================
# Header
# =========================
st.title(f"📊 {APP_TITLE}")
st.caption(f"{APP_SUBTITLE} — Version {APP_VERSION} — {COPYRIGHT}")

# =========================
# Load data (local file or upload)
# =========================
df = None
if DATA_PATH.exists():
    df = load_data_from_excel(DATA_PATH)
else:
    st.warning("ملف البيانات (liquidity_all.xlsx) غير موجود. ارفع الملف من هنا (مناسب للـ Cloud).")
    up = st.file_uploader("Upload liquidity_all.xlsx", type=["xlsx"])
    if up is None:
        st.stop()
    df = load_data_from_uploaded(up)

# =========================
# Top filters
# =========================
min_d, max_d = df["التاريخ"].min(), df["التاريخ"].max()

c1, c2, c3 = st.columns([2, 2, 3])
with c1:
    start_date = st.date_input("من تاريخ", value=min_d.date(), min_value=min_d.date(), max_value=max_d.date())
with c2:
    end_date = st.date_input("إلى تاريخ", value=max_d.date(), min_value=min_d.date(), max_value=max_d.date())
with c3:
    symbols = sorted(df["الرمز"].dropna().unique().tolist())
    selected_symbol = st.selectbox("اختر سهم للتفاصيل", options=["(السوق)"] + symbols)

base_dff = df[(df["التاريخ"].dt.date >= start_date) & (df["التاريخ"].dt.date <= end_date)].copy()

# =========================
# Tabs (الإعدادات آخر حاجة بصريًا) + Help/About/README
# =========================
tab_market, tab_watch, tab_details, tab_history, tab_help, tab_about, tab_readme, tab_settings = st.tabs(
    ["📈 السوق", "📌 مراقب السيولة", "🔎 تفاصيل السهم", "📊 تاريخ السيولة", "❓ Help", "ℹ️ About", "📄 README", "⚙️ إعدادات"]
)

# =========================
# SETTINGS TAB (آخر Tab بصريًا - لكنه يتنفذ عادي)
# =========================
with tab_settings:
    st.header("⚙️ إعدادات العرض")

    mode = st.radio(
        "وضع الحساب",
        ["فترة مخصصة", "آخر 10 جلسات", "آخر جلسة فقط"],
        horizontal=True,
        index=0,
        key="mode_calc"
    )

    net_filter = st.radio(
        "فلتر اتجاه صافي السيولة",
        ["الكل", "صافي موجب فقط", "صافي سالب فقط"],
        horizontal=True,
        index=0,
        key="net_filter"
    )

    min_liq_pct = st.slider(
        "فلتر نسبة مخطط السيولة (≥)",
        0, 100, 0, 5,
        key="min_liq_pct"
    )

    change_mode = st.selectbox(
        "عرض % التغير في الملخص",
        ["آخر جلسة", "متوسط", "متوسط مرجّح (قيمة التداول)"],
        index=1,
        key="change_mode"
    )

    st.caption("ملاحظة: التابات الأخرى تستخدم الإعدادات دي تلقائيًا.")

# =========================
# Apply settings to dff
# =========================
dff = base_dff.copy()

if mode == "آخر 10 جلسات":
    last_dates = sorted(dff["التاريخ"].dt.date.dropna().unique().tolist())
    last_dates = last_dates[-10:] if len(last_dates) > 10 else last_dates
    dff = dff[dff["التاريخ"].dt.date.isin(last_dates)].copy()

elif mode == "آخر جلسة فقط":
    if not dff.empty:
        last_day = dff["التاريخ"].max()
        dff = dff[dff["التاريخ"] == last_day].copy()

if "نسبة مخطط السيولة" in dff.columns and min_liq_pct > 0:
    dff = dff[dff["نسبة مخطط السيولة"] >= min_liq_pct].copy()

if net_filter == "صافي موجب فقط":
    dff = dff[dff["صافي السيولة"] > 0].copy()
elif net_filter == "صافي سالب فقط":
    dff = dff[dff["صافي السيولة"] < 0].copy()

# نطاق العرض (سوق أو سهم)
if selected_symbol != "(السوق)":
    scope_df = dff[dff["الرمز"] == selected_symbol].copy()
    nm = scope_df["اسم_نهائي"].iloc[0] if (not scope_df.empty and "اسم_نهائي" in scope_df.columns) else ""
    scope_label = f"{selected_symbol} - {nm}".strip(" -")
else:
    scope_df = dff
    scope_label = "السوق"

# =========================
# TAB: Help
# =========================
with tab_help:
    st.header("❓ Help")
    st.markdown(
        """
### طريقة الاستخدام
- **اختيار الفترة**: من أعلى الصفحة (من/إلى).
- **اختيار سهم**: من قائمة الأسهم لعرض تفاصيله.
- **إعدادات**: من Tab (⚙️ إعدادات) لتحديد:
  - فترة مخصصة / آخر 10 جلسات / آخر جلسة فقط
  - فلترة صافي السيولة (موجب فقط / سالب فقط)
  - فلترة نسبة مخطط السيولة

### ملاحظات
- تم إضافة تصحيح تلقائي للأسماء العربية (OCR cleanup) + قاموس رموز (Overrides).
- الألوان: **أخضر = صافي موجب**، **أحمر = صافي سالب**.
"""
    )
    st.info(DISCLAIMER)

# =========================
# TAB: About
# =========================
with tab_about:
    st.header("ℹ️ About")
    st.markdown(
        f"""
**{APP_TITLE}** — *{APP_SUBTITLE}*  
Version: `{APP_VERSION}`

**Owner / Author:** {AUTHOR}  
**Copyright:** {COPYRIGHT}

### Intellectual Property
- استخدام الداشبورد مسموح عبر الرابط فقط.
- يمنع نسخ/تعديل/إعادة توزيع الكود أو أي جزء منه بدون إذن كتابي من المالك.

### Contact
- Email: [{EMAIL}](mailto:{EMAIL})
- WhatsApp: {WHATSAPP_URL}
- Telegram: {TELEGRAM_URL}

**Disclaimer:** {DISCLAIMER}
"""
    )

# =========================
# TAB: README (عرض من الملف + تنزيل)
# =========================
with tab_readme:
    st.header("📄 README داخل الداشبورد")

    if README_PATH.exists():
        readme_text = README_PATH.read_text(encoding="utf-8")
        st.download_button(
            "⬇️ تحميل README.md",
            data=readme_text,
            file_name="README.md",
            mime="text/markdown"
        )
        st.markdown(readme_text)
    else:
        st.warning("الملف README.md غير موجود بجانب app.py. ضع README.md في نفس مجلد المشروع.")
        st.code(str(README_PATH))

# =========================
# TAB 1: Market/Symbol summary
# =========================
with tab_market:
    st.header(f"ملخص ({scope_label})")

    if scope_df.empty:
        st.warning("لا توجد بيانات حسب الفلاتر المختارة.")
    else:
        total_in = scope_df["السيولة الداخلة"].sum()
        total_out = scope_df["السيولة الخارجة"].sum()
        net = scope_df["صافي السيولة"].sum()
        change_value, change_delta = get_change_metric(scope_df, change_mode)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("السيولة الداخلة", fmt_money(total_in))
        m2.metric("السيولة الخارجة", fmt_money(total_out))
        m3.metric("صافي السيولة", fmt_money(net))
        m4.metric("% التغير", change_value, delta=change_delta)

        pie_df = pd.DataFrame({
            "النوع": ["السيولة الداخلة", "السيولة الخارجة"],
            "القيمة": [total_in, total_out]
        })
        fig_pie = px.pie(pie_df, names="النوع", values="القيمة", hole=0.6)
        fig_pie.update_traces(
            textposition="outside",
            textinfo="percent+label",
            marker=dict(colors=["#00C853", "#D50000"])
        )
        fig_pie = add_watermark(fig_pie)

        daily_net = (
            scope_df.assign(التاريخ=scope_df["التاريخ"].dt.date)
                    .groupby("التاريخ", as_index=False)["صافي السيولة"].sum()
        )
        daily_net["الإشارة"] = daily_net["صافي السيولة"].apply(lambda x: "موجب" if x >= 0 else "سالب")
        fig_market = px.bar(
            daily_net, x="التاريخ", y="صافي السيولة",
            color="الإشارة",
            color_discrete_map={"موجب": "#00C853", "سالب": "#D50000"},
        )
        fig_market.update_layout(legend_title_text="")
        fig_market = add_watermark(fig_market)

        left, right = st.columns([1, 1])
        with left:
            st.plotly_chart(
                fig_pie,
                use_container_width=True,
                key=f"pie_{selected_symbol}_{mode}_{net_filter}_{min_liq_pct}_{start_date}_{end_date}"
            )
        with right:
            st.plotly_chart(
                fig_market,
                use_container_width=True,
                key=f"market_{selected_symbol}_{mode}_{net_filter}_{min_liq_pct}_{start_date}_{end_date}"
            )

# =========================
# TAB 2: Watchlist ranking
# =========================
with tab_watch:
    st.header("مراقب السيولة (ترتيب الأسهم)")

    if dff.empty:
        st.warning("لا توجد بيانات حسب الفلاتر المختارة.")
    else:
        # نجمع على الرمز فقط لضمان عدم تكرار الاسم بسبب OCR
        def most_common_name(x):
            x = x.dropna().astype(str).str.strip()
            if x.empty:
                return ""
            return x.value_counts().idxmax()

        rank = (
            dff.groupby("الرمز", as_index=False)
               .agg({
                   "اسم_نهائي": most_common_name,
                   "صافي السيولة": "sum",
                   "قيمة التداول": "sum",
                   "التغير %": "mean"
               })
        )

        consec_map = {}
        for sym in rank["الرمز"].tolist():
            sym_df = dff[dff["الرمز"] == sym]
            consec_map[sym] = consecutive_positive_days(sym_df)
        rank["أيام متتالية (صافي موجب)"] = rank["الرمز"].map(consec_map).fillna(0).astype(int)

        rank = rank.sort_values("صافي السيولة", ascending=False)

        top_n = st.slider("عدد الأسهم المعروضة", 10, 200, 30, 10, key="topn_watch")

        show_raw = rank.head(top_n).copy()
        show_raw = show_raw.rename(columns={"اسم_نهائي": "الإسم"})

        styler = (
            show_raw.style
            .applymap(style_net_column, subset=["صافي السيولة"])
            .format({
                "صافي السيولة": lambda v: fmt_money(v),
                "قيمة التداول": lambda v: fmt_money(v),
                "التغير %": "{:.2f}".format
            })
        )

        st.dataframe(styler, use_container_width=True, hide_index=True)

# =========================
# TAB 3: Symbol details
# =========================
with tab_details:
    st.header("تفاصيل السهم")

    if selected_symbol == "(السوق)":
        st.info("اختر سهم من القائمة بالأعلى لعرض التفاصيل.")
    elif scope_df.empty:
        st.warning("لا توجد بيانات للسهم حسب الفلاتر المختارة.")
    else:
        sym_df = scope_df.copy().sort_values("التاريخ")

        c1, c2 = st.columns([2, 1])
        with c1:
            sym_daily = (
                sym_df.assign(التاريخ=sym_df["التاريخ"].dt.date)
                      .groupby("التاريخ", as_index=False)["صافي السيولة"].sum()
            )
            sym_daily["الإشارة"] = sym_daily["صافي السيولة"].apply(lambda x: "موجب" if x >= 0 else "سالب")
            fig_sym = px.bar(
                sym_daily,
                x="التاريخ",
                y="صافي السيولة",
                color="الإشارة",
                color_discrete_map={"موجب": "#00C853", "سالب": "#D50000"},
            )
            fig_sym.update_layout(legend_title_text="")
            fig_sym = add_watermark(fig_sym)

            st.plotly_chart(
                fig_sym, use_container_width=True,
                key=f"sym_{selected_symbol}_{mode}_{net_filter}_{min_liq_pct}_{start_date}_{end_date}"
            )

        with c2:
            st.write("**إحصائيات الفترة**")
            st.metric("الإسم", sym_df["اسم_نهائي"].iloc[0] if "اسم_نهائي" in sym_df.columns else "-")
            st.metric("صافي السيولة", fmt_money(sym_df["صافي السيولة"].sum()))
            if "التغير %" in sym_df.columns:
                st.metric("متوسط التغير %", f'{sym_df["التغير %"].mean():.2f}%')
            if "آخر سعر" in sym_df.columns and not sym_df.empty:
                st.metric("آخر سعر (آخر جلسة)", f'{sym_df.iloc[-1]["آخر سعر"]:.2f}')
            st.metric("أيام متتالية صافي موجب", str(consecutive_positive_days(sym_df)))

        st.write("**تفاصيل الجلسات**")
        view_cols = [
            "التاريخ", "الرمز", "اسم_نهائي",
            "آخر سعر", "التغير %",
            "قيمة التداول", "السيولة الداخلة", "السيولة الخارجة",
            "صافي السيولة", "نسبة مخطط السيولة",
            "المصدر"
        ]
        view_cols = [c for c in view_cols if c in sym_df.columns]
        show_table = sym_df[view_cols].rename(columns={"اسم_نهائي": "الإسم"})
        st.dataframe(show_table.sort_values("التاريخ", ascending=False), use_container_width=True, hide_index=True)

# =========================
# TAB 4: History
# =========================
with tab_history:
    st.header(f"تاريخ السيولة ({scope_label})")

    if scope_df.empty:
        st.warning("لا توجد بيانات حسب الفلاتر المختارة.")
    else:
        hist = (
            scope_df.assign(التاريخ=scope_df["التاريخ"].dt.date)
                    .groupby("التاريخ", as_index=False)
                    .agg({
                        "صافي السيولة": "sum",
                        "السيولة الداخلة": "sum",
                        "السيولة الخارجة": "sum",
                        "التغير %": "mean",
                        "آخر سعر": "last" if "آخر سعر" in scope_df.columns else "size"
                    })
        ).sort_values("التاريخ")

        hist["الإشارة"] = hist["صافي السيولة"].apply(lambda x: "موجب" if x >= 0 else "سالب")
        fig_hist = px.bar(
            hist, x="التاريخ", y="صافي السيولة",
            color="الإشارة",
            color_discrete_map={"موجب": "#00C853", "سالب": "#D50000"},
        )
        fig_hist.update_layout(legend_title_text="")
        fig_hist = add_watermark(fig_hist)

        st.plotly_chart(
            fig_hist, use_container_width=True,
            key=f"hist_{selected_symbol}_{mode}_{net_filter}_{min_liq_pct}_{start_date}_{end_date}"
        )

        table_cols = ["التاريخ", "آخر سعر", "التغير %", "صافي السيولة", "السيولة الداخلة", "السيولة الخارجة"]
        table_cols = [c for c in table_cols if c in hist.columns]
        hist_show = hist[table_cols].copy()

        if "التغير %" in hist_show.columns:
            hist_show["التغير %"] = hist_show["التغير %"].round(2)

        for c in ["صافي السيولة", "السيولة الداخلة", "السيولة الخارجة"]:
            if c in hist_show.columns:
                hist_show[c] = hist_show[c].apply(fmt_money)

        st.dataframe(hist_show.sort_values("التاريخ", ascending=False), use_container_width=True, hide_index=True)

# =========================
# Footer (حقوق + Disclaimer)
# =========================
st.markdown(
    f"""
    <hr>
    <div style='text-align:center; opacity:0.85; font-weight:700;'>
        {COPYRIGHT} — {DISCLAIMER}<br>
        Contact: <a href="mailto:{EMAIL}">{EMAIL}</a> |
        <a href="{WHATSAPP_URL}" target="_blank">WhatsApp</a> |
        <a href="{TELEGRAM_URL}" target="_blank">Telegram</a>
    </div>
    """,
    unsafe_allow_html=True
)

