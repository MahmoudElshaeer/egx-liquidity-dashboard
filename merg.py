import pandas as pd
from pathlib import Path

# 1) المسارات
INPUT_DIR = Path(r"D:\Projects\merg\csvs")
OUT_DIR = Path(r"D:\Projects\merg")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_EXCEL = OUT_DIR / "liquidity_all.xlsx"
OUT_CSV = OUT_DIR / "liquidity_all.csv"

# 2) ترتيب الأعمدة المتوقع (زي المثال بتاعك)
EXPECTED_COLS = [
    "التاريخ", "الرمز", "الإسم", "أخر سعر", "التغير %",
    "قيمة التداول", "السيولة الداخلة", "السيولة الخارجة",
    "صافى السيولة", "% مخطط السيولة", "رقم الصفحة", "المصدر"
]

def read_csv_safe(path: Path) -> pd.DataFrame:
    # جرّب أشهر encoding للملفات العربية
    for enc in ("utf-8-sig", "cp1256", "utf-8"):
        try:
            df = pd.read_csv(path, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue
    # لو فشل كله، ارفع الخطأ الطبيعي
    return pd.read_csv(path)

def to_number(series: pd.Series) -> pd.Series:
    # يحول "1,234.5" أو "١٢٣٤" إلى رقم قدر الإمكان
    s = series.astype(str).str.replace(",", "", regex=False).str.strip()
    s = s.replace({"nan": None, "None": None, "": None})
    return pd.to_numeric(s, errors="coerce")

# 3) اجمع الملفات
files = sorted(INPUT_DIR.glob("liquidity_*.csv"))
if not files:
    raise SystemExit(f"No files found in: {INPUT_DIR}")

dfs = []
bad_files = []

for f in files:
    df = read_csv_safe(f)
    df.columns = df.columns.astype(str).str.strip()  # إزالة أي مسافات خفية في أسماء الأعمدة

    # تحقق من الأعمدة
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLS]
    if missing or extra:
        bad_files.append((f.name, missing, extra))
        continue

    # إعادة ترتيب الأعمدة نفس الشكل
    df = df[EXPECTED_COLS].copy()

    # إضافة مصدر الملف (اختياري مفيد)
    df["source_file"] = f.name

    # تحويل التاريخ
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")

    # تحويل أعمدة الأرقام
    num_cols = [
        "أخر سعر", "التغير %", "قيمة التداول", "السيولة الداخلة",
        "السيولة الخارجة", "صافى السيولة", "% مخطط السيولة", "رقم الصفحة"
    ]
    for c in num_cols:
        df[c] = to_number(df[c])

    dfs.append(df)

if bad_files:
    print("⚠️ Files skipped بسبب اختلاف أعمدة:")
    for name, missing, extra in bad_files:
        print(f"- {name} | Missing: {missing} | Extra: {extra}")

if not dfs:
    raise SystemExit("No valid files to merge (all skipped بسبب الأعمدة).")

all_df = pd.concat(dfs, ignore_index=True)

# 4) ترتيب نهائي (اختياري)
all_df = all_df.sort_values(["التاريخ", "الرمز"], ascending=[True, True])

# 5) حفظ النتائج
all_df.to_excel(OUT_EXCEL, index=False)
all_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

print(f"✅ Merged rows: {len(all_df):,}")
print(f"✅ Saved Excel: {OUT_EXCEL}")
print(f"✅ Saved CSV  : {OUT_CSV}")
