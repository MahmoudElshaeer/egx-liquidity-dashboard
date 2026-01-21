import re
import io
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# App Meta (حقوق + About)
# =========================
APP_TITLE = "مراقب السيولة"
APP_SUBTITLE = "EGX Liquidity Monitor Dashboard"
APP_VERSION = "1.1.2"
AUTHOR = "Mahmoud Abdrabbo"
COPYRIGHT = f"© 2026 {AUTHOR}. All rights reserved."
DISCLAIMER = "هذا التطبيق لأغراض معلوماتية فقط ولا يُعد توصية استثمارية."

WHATSAPP_URL = "https://wa.me/qr/37OH2UF3VH7PM1"
TELEGRAM_URL = "https://t.me/Mahmoud_abdrabbo"
EMAIL = "mahmoud_elshaeer@yahoo.com"

st.set_page_config(page_title=APP_TITLE, layout="wide")

PROJECT_DIR = Path(__file__).resolve().parent
README_PATH = PROJECT_DIR / "README.md"

CSV_PATH  = PROJECT_DIR / "liquidity_all.csv"
XLSX_PATH = PROJECT_DIR / "liquidity_all.xlsx"  # fallback

# =========================
# Colors (ثابتة)
# =========================
GREEN = "#00C853"
RED   = "#D50000"
SIGN_COLOR_MAP = {"موجب": GREEN, "سالب": RED}

# =========================
# CSS (تكبير التابات + عناوين)
# =========================
st.markdown(
    """
    <style>
    div[data-baseweb="tab"] > button {
        font-size: 26px !important;
        font-weight: 800 !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
    }
    h1 { font-size: 42px !important; }
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
    "ARAB": "المطورون العرب القابضة",
}

# =========================
# تنظيف/تطبيع عربي
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

    # دمج الحروف اللي الـ OCR فصلها
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
        ("اال", "ال"),
        ("ايست  ن", "ايسترن"),
        ("كومبائني", "كومباني"),
        ("كومبان ي", "كومباني"),
    ]
    for a, b in fixes:
        s = s.replace(a, b)

    return s.strip()

# =========================
# CSV reading (safe encodings)
# =========================
def read_csv_safe_path(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp1256", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)

def read_csv_safe_bytes(b: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp1256", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(b), encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(io.BytesIO(b))

# =========================
# Unify + Validate
# =========================
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

    # تاريخ
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

    before = len(df)
    df = df.dropna(subset=["التاريخ", "الرمز"]).copy()
    if len(df) == 0:
        raise ValueError(
            "بعد تحويل التاريخ/الرمز أصبحت البيانات فارغة. "
            "راجع عمود 'التاريخ' وتنسيقه في الملف. "
            f"(قبل التنظيف: {before} صف)"
        )

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

def file_signature(path: Path) -> tuple:
    st_ = path.stat()
    return (int(st_.st_mtime_ns), int(st_.st_size))

@st.cache_data(show_spinner=False)
def load_data_from_csv(path_str: str, sig: tuple) -> pd.DataFrame:
    _ = sig  # cache-bust
    df = read_csv_safe_path(Path(path_str))
    return load_data_df(df)

@st.cache_data(show_spinner=False)
def load_data_from_excel(path_str: str, sig: tuple) -> pd.DataFrame:
    _ = sig  # cache-bust
    df = pd.read_excel(path_str)
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
        return f"color: {GREEN}; font-weight: 800;"
    if v < 0:
        return f"color: {RED}; font-weight: 800;"
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

def fmt_dt(ts: float) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# =========================
# Header
# =========================
st.title(f"📊 {APP_TITLE}")
st.caption(f"{APP_SUBTITLE} — Version {APP_VERSION} — {COPYRIGHT}")

# =========================
# Sidebar: refresh + debug
# =========================
with st.sidebar:
    st.markdown("### ⚙️ أدوات")
    if st.button("🔄 تحديث البيانات الآن (مسح الكاش)", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("### 🧪 تشخيص سريع")

# =========================
# Load data (CSV first, XLSX fallback, else upload)
# =========================
df = None
data_source = None
data_path = None
data_mtime = None
data_size = None

try:
    if CSV_PATH.exists():
        sig = file_signature(CSV_PATH)
        df = load_data_from_csv(str(CSV_PATH), sig)
        data_source = "CSV"
        data_path = str(CSV_PATH)
        data_mtime = CSV_PATH.stat().st_mtime
        data_size = CSV_PATH.stat().st_size

    elif XLSX_PATH.exists():
        sig = file_signature(XLSX_PATH)
        df = load_data_from_excel(str(XLSX_PATH), sig)
        data_source = "XLSX (fallback)"
        data_path = str(XLSX_PATH)
        data_mtime = XLSX_PATH.stat().st_mtime
        data_size = XLSX_PATH.stat().st_size

    else:
        st.warning("ملف البيانات غير موجود داخل الريبو. ارفع الملف من هنا.")
        up = st.file_uploader("Upload liquidity_all.csv أو liquidity_all.xlsx", type=["csv", "xlsx"], key="uploader_data")
        if up is None:
            st.stop()

        if up.name.lower().endswith(".csv"):
            tmp = read_csv_safe_bytes(up.getvalue())
            df = load_data_df(tmp)
            data_source = "Uploaded CSV"
        else:
            tmp = pd.read_excel(up.getvalue())
            df = load_data_df(tmp)
            data_source = "Uploaded XLSX"

except Exception as e:
    st.error(f"فشل تحميل البيانات: {type(e).__name__}: {e}")
    st.stop()

# Sidebar debug
with st.sidebar:
    st.write(f"**المصدر:** {data_source}")
    if data_path:
        st.write(f"**الملف:** `{Path(data_path).name}`")
        st.write(f"**الحجم:** {data_size:,} bytes")
        st.write(f"**آخر تعديل:** {fmt_dt(data_mtime)}")
    st.write(f"**Rows:** {len(df):,}")
    st.write(f"**Date range:** {df['التاريخ'].min().date()} → {df['التاريخ'].max().date()}")
    with st.expander("🔍 Preview (أول 10 صفوف)"):
        st.dataframe(df.head(10), use_container_width=True, key="preview_df")

def trading_dates(df_: pd.DataFrame):
    return sorted(df_["التاريخ"].dropna().dt.date.unique().tolist())

def last_n_sessions_range(df_: pd.DataFrame, n: int):
    dates = trading_dates(df_)
    if not dates:
        return None, None
    n = max(1, int(n))
    tail = dates[-n:] if len(dates) >= n else dates
    return tail[0], tail[-1]

def ytd_range(df_: pd.DataFrame):
    dates = trading_dates(df_)
    if not dates:
        return None, None
    last_day = dates[-1]
    y0 = last_day.replace(month=1, day=1)
    start = next((d for d in dates if d >= y0), dates[0])
    return start, last_day

def apply_quick_range(df_: pd.DataFrame, option: str, min_date, max_date):
    # يرجّع (start_date, end_date) كـ date
    if option == "مخصص":
        return None, None

    if option == "آخر يوم (آخر جلسة)":
        return last_n_sessions_range(df_, 1)

    if option == "آخر أسبوع (5 جلسات)":
        return last_n_sessions_range(df_, 5)

    if option == "آخر 10 جلسات":
        return last_n_sessions_range(df_, 10)

    if option == "آخر شهر (≈22 جلسة)":
        return last_n_sessions_range(df_, 22)

    if option == "آخر 3 شهور (≈66 جلسة)":
        return last_n_sessions_range(df_, 66)

    if option == "من بداية السنة (YTD)":
        return ytd_range(df_)

    if option == "كل البيانات":
        return (min_date, max_date)

    return None, None


# =========================
# Top filters
# =========================
# =========================
# Top filters (Dropdown ranges + manual dates)
# =========================
# =========================
# Helpers for Quick Ranges (put once, before Top filters)
# =========================
def trading_dates(df_: pd.DataFrame):
    return sorted(df_["التاريخ"].dropna().dt.date.unique().tolist())

def last_n_sessions_range(df_: pd.DataFrame, n: int):
    dates = trading_dates(df_)
    if not dates:
        return None, None
    n = max(1, int(n))
    tail = dates[-n:] if len(dates) >= n else dates
    return tail[0], tail[-1]

def ytd_range(df_: pd.DataFrame):
    dates = trading_dates(df_)
    if not dates:
        return None, None
    last_day = dates[-1]
    y0 = last_day.replace(month=1, day=1)
    start = next((d for d in dates if d >= y0), dates[0])
    return start, last_day

def apply_quick_range(df_: pd.DataFrame, option: str, min_date, max_date):
    if option == "مخصص":
        return None, None
    if option == "آخر يوم (آخر جلسة)":
        return last_n_sessions_range(df_, 1)
    if option == "آخر أسبوع (5 جلسات)":
        return last_n_sessions_range(df_, 5)
    if option == "آخر 10 جلسات":
        return last_n_sessions_range(df_, 10)
    if option == "آخر شهر (≈22 جلسة)":
        return last_n_sessions_range(df_, 22)
    if option == "آخر 3 شهور (≈66 جلسة)":
        return last_n_sessions_range(df_, 66)
    if option == "من بداية السنة (YTD)":
        return ytd_range(df_)
    if option == "كل البيانات":
        return (min_date, max_date)
    return None, None


# =========================
# Top filters (CLEAN) - Dropdown quick range + manual dates + symbol
# =========================
min_d, max_d = df["التاريخ"].min(), df["التاريخ"].max()
min_date, max_date = min_d.date(), max_d.date()

QUICK_OPTIONS = [
    "مخصص",
    "آخر يوم (آخر جلسة)",
    "آخر أسبوع (5 جلسات)",
    "آخر 10 جلسات",
    "آخر شهر (≈22 جلسة)",
    "آخر 3 شهور (≈66 جلسة)",
    "من بداية السنة (YTD)",
    "كل البيانات",
]

# --- init session state once ---
if "quick_range" not in st.session_state:
    st.session_state["quick_range"] = "مخصص"
if "start_date" not in st.session_state:
    st.session_state["start_date"] = min_date
if "end_date" not in st.session_state:
    st.session_state["end_date"] = max_date

# --- quick range row (mobile friendly) ---
# --- quick range row (aligned) ---
qr1, qr2 = st.columns([4, 1])

with qr1:
    st.selectbox(
        "⏱️ نطاق زمني سريع",
        options=QUICK_OPTIONS,
        index=QUICK_OPTIONS.index(st.session_state["quick_range"]) if st.session_state["quick_range"] in QUICK_OPTIONS else 0,
        key="quick_range",
    )

with qr2:
    # Spacer ينزل الزرار لنفس مستوى الـ selectbox
    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    if st.button("تطبيق", use_container_width=True, key="apply_quick_btn"):
        s, e = apply_quick_range(df, st.session_state["quick_range"], min_date, max_date)
        if s and e:
            st.session_state["start_date"] = s
            st.session_state["end_date"] = e
        st.rerun()



# --- manual dates + symbol ---
c1, c2, c3 = st.columns([2, 2, 3])

with c1:
    st.date_input(
        "من تاريخ",
        min_value=min_date,
        max_value=max_date,
        key="start_date",
    )

with c2:
    st.date_input(
        "إلى تاريخ",
        min_value=min_date,
        max_value=max_date,
        key="end_date",
    )

with c3:
    symbols = sorted(df["الرمز"].dropna().unique().tolist())
    selected_symbol = st.selectbox(
        "اختر سهم للتفاصيل",
        options=["(السوق)"] + symbols,
        key="selected_symbol",
    )

# --- keep dates valid & treat manual edits as "custom" ---
# (لو المستخدم غيّر يدوي، نخلي النطاق "مخصص")
if st.session_state["start_date"] > st.session_state["end_date"]:
    st.session_state["start_date"], st.session_state["end_date"] = st.session_state["end_date"], st.session_state["start_date"]
    st.session_state["quick_range"] = "مخصص"
    st.rerun()

# لو المستخدم لمس التواريخ يدويًا (ومش متسقة مع النطاق السريع)، رجّعها "مخصص"
# (نكتفي بالتحويل لمخصص دائمًا عند أي تعديل يدوي)
# ملاحظة: Streamlit مش بيدينا event مباشر، فده سلوك عملي وبسيط.
if st.session_state["quick_range"] != "مخصص":
    # لو اختار نطاق سريع لكن بعدين عدّل التاريخ يدويًا، غالبًا ده "مخصص"
    # خلّيها مخصص في أول rerun بعد أي اختلاف بسيط
    # (اختياري لكنه مفيد)
    pass

start_date = st.session_state["start_date"]
end_date = st.session_state["end_date"]

base_dff = df[(df["التاريخ"].dt.date >= start_date) & (df["التاريخ"].dt.date <= end_date)].copy()



# =========================
# Tabs
# =========================
tab_market, tab_watch, tab_details, tab_history, tab_help, tab_about, tab_readme, tab_settings = st.tabs(
    ["📈 السوق", "📌 مراقب السيولة", "🔎 تفاصيل السهم", "📊 تاريخ السيولة", "❓ Help", "ℹ️ About", "📄 README", "⚙️ إعدادات"]
)

# =========================
# SETTINGS TAB
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
# Apply settings
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

# Key base (يمنع Duplicate IDs)
key_base = f"{selected_symbol}_{start_date}_{end_date}_{mode}_{net_filter}_{min_liq_pct}"

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
# TAB: README
# =========================
with tab_readme:
    st.header("📄 README داخل الداشبورد")
    if README_PATH.exists():
        readme_text = README_PATH.read_text(encoding="utf-8")
        st.download_button(
            "⬇️ تحميل README.md",
            data=readme_text,
            file_name="README.md",
            mime="text/markdown",
            key="download_readme"
        )
        st.markdown(readme_text)
    else:
        st.warning("الملف README.md غير موجود بجانب app.py.")
        st.code(str(README_PATH))

# =========================
# TAB 1: Market summary
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

        pie_df = pd.DataFrame({"النوع": ["السيولة الداخلة", "السيولة الخارجة"], "القيمة": [total_in, total_out]})
        fig_pie = px.pie(pie_df, names="النوع", values="القيمة", hole=0.6)
        fig_pie.update_traces(
            textposition="outside",
            textinfo="percent+label",
            marker=dict(colors=[GREEN, RED])
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
            color_discrete_map=SIGN_COLOR_MAP,
        )
        fig_market.update_layout(legend_title_text="")
        fig_market = add_watermark(fig_market)

        left, right = st.columns([1, 1])
        with left:
            st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{key_base}")
        with right:
            st.plotly_chart(fig_market, use_container_width=True, key=f"market_{key_base}")

# =========================
# TAB 2: Watchlist
# =========================
with tab_watch:
    st.header("مراقب السيولة (ترتيب الأسهم)")

    if dff.empty:
        st.warning("لا توجد بيانات حسب الفلاتر المختارة.")
    else:
        def most_common_name(x):
            x = x.dropna().astype(str).str.strip()
            if x.empty:
                return ""
            return x.value_counts().idxmax()

        agg_map = {"اسم_نهائي": most_common_name, "صافي السيولة": "sum"}
        if "قيمة التداول" in dff.columns:
            agg_map["قيمة التداول"] = "sum"
        if "التغير %" in dff.columns:
            agg_map["التغير %"] = "mean"

        rank = dff.groupby("الرمز", as_index=False).agg(agg_map)

        consec_map = {sym: consecutive_positive_days(dff[dff["الرمز"] == sym]) for sym in rank["الرمز"].tolist()}
        rank["أيام متتالية (صافي موجب)"] = rank["الرمز"].map(consec_map).fillna(0).astype(int)

        rank = rank.sort_values("صافي السيولة", ascending=False)

        top_n = st.slider("عدد الأسهم المعروضة", 10, 200, 30, 10, key="topn_watch")
        show_raw = rank.head(top_n).copy().rename(columns={"اسم_نهائي": "الإسم"})

        styler = show_raw.style.applymap(style_net_column, subset=["صافي السيولة"])
        fmt_map = {"صافي السيولة": lambda v: fmt_money(v)}
        if "قيمة التداول" in show_raw.columns:
            fmt_map["قيمة التداول"] = lambda v: fmt_money(v)
        if "التغير %" in show_raw.columns:
            fmt_map["التغير %"] = "{:.2f}".format
        styler = styler.format(fmt_map)

        st.dataframe(styler, use_container_width=True, hide_index=True, key=f"watch_{key_base}")

# =========================
# TAB 3: Details
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
                color_discrete_map=SIGN_COLOR_MAP,
            )
            fig_sym.update_layout(legend_title_text="")
            fig_sym = add_watermark(fig_sym)

            st.plotly_chart(fig_sym, use_container_width=True, key=f"sym_{key_base}")

        with c2:
            st.write("**إحصائيات الفترة**")
            st.metric("الإسم", sym_df["اسم_نهائي"].iloc[0] if "اسم_نهائي" in sym_df.columns else "-")
            st.metric("صافي السيولة", fmt_money(sym_df["صافي السيولة"].sum()))
            if "التغير %" in sym_df.columns:
                st.metric("متوسط التغير %", f'{sym_df["التغير %"].mean():.2f}%')
            if "آخر سعر" in sym_df.columns and not sym_df.empty and not pd.isna(sym_df.iloc[-1].get("آخر سعر")):
                st.metric("آخر سعر (آخر جلسة)", f'{float(sym_df.iloc[-1]["آخر سعر"]):.2f}')
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
        st.dataframe(
            show_table.sort_values("التاريخ", ascending=False),
            use_container_width=True,
            hide_index=True,
            key=f"details_tbl_{key_base}"
        )

# =========================
# TAB 4: History
# =========================
with tab_history:
    st.header(f"تاريخ السيولة ({scope_label})")

    if scope_df.empty:
        st.warning("لا توجد بيانات حسب الفلاتر المختارة.")
    else:
        agg_map = {
            "صافي السيولة": "sum",
            "السيولة الداخلة": "sum",
            "السيولة الخارجة": "sum",
        }
        if "التغير %" in scope_df.columns:
            agg_map["التغير %"] = "mean"
        if "آخر سعر" in scope_df.columns:
            agg_map["آخر سعر"] = "last"

        hist = (
            scope_df.assign(التاريخ=scope_df["التاريخ"].dt.date)
                    .groupby("التاريخ", as_index=False)
                    .agg(agg_map)
        ).sort_values("التاريخ")

        hist["الإشارة"] = hist["صافي السيولة"].apply(lambda x: "موجب" if x >= 0 else "سالب")

        fig_hist = px.bar(
            hist, x="التاريخ", y="صافي السيولة",
            color="الإشارة",
            color_discrete_map=SIGN_COLOR_MAP,
        )
        fig_hist.update_layout(legend_title_text="")
        fig_hist = add_watermark(fig_hist)

        st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_{key_base}")

        table_cols = ["التاريخ", "آخر سعر", "التغير %", "صافي السيولة", "السيولة الداخلة", "السيولة الخارجة"]
        table_cols = [c for c in table_cols if c in hist.columns]
        hist_show = hist[table_cols].copy()

        if "التغير %" in hist_show.columns:
            hist_show["التغير %"] = hist_show["التغير %"].round(2)

        for c in ["صافي السيولة", "السيولة الداخلة", "السيولة الخارجة"]:
            if c in hist_show.columns:
                hist_show[c] = hist_show[c].apply(fmt_money)

        st.dataframe(
            hist_show.sort_values("التاريخ", ascending=False),
            use_container_width=True,
            hide_index=True,
            key=f"hist_tbl_{key_base}"
        )

# =========================
# Footer
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
