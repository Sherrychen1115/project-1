# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "xlrd"]
# ///
"""把 114-1 在學生人數統計表（.xls 第一個工作表）轉成整齊的 CSV。"""
import re
from pathlib import Path

import pandas as pd
import xlrd

ROOT = Path(__file__).resolve().parent.parent
SRC = next((ROOT / "東華大學統計資料" / "在學人數統計表").glob("114-1*.xls"))
OUT = ROOT / "work" / "enrollment_114-1.csv"

# 第 0 欄的區段標題 -> program_raw
SECTIONS = {"博士班": "博士班", "碩士班": "碩士班", "碩專班": "碩士在職專班", "學士班": "學士班"}


def main():
    raw = pd.read_excel(SRC, sheet_name=0, header=None)
    # 系所欄（第 2 欄）的合併範圍涵蓋的列；空白但不在任何合併範圍內的列是報表瑕疵，
    # 例如 114-1 的「應用物理博士班一般組」，實際上屬於下一格的物理學系
    sheet = xlrd.open_workbook(SRC, formatting_info=True).sheet_by_index(0)
    merged = {i for r0, r1, c0_, c1 in sheet.merged_cells if c0_ <= 2 < c1 for i in range(r0, r1)}
    program = college = dept = None
    rows = []
    for i, r in raw.iterrows():
        c0 = str(r[0]).strip() if pd.notna(r[0]) else ""
        # 區段開頭：「博士班 合計1」等；遇到就切換學制並清掉合併儲存格的延續狀態
        m = re.match(r"(博士班|碩士班|碩專班|學士班)\s*合計", c0)
        if m:
            program = SECTIONS[m.group(1)]
            college = dept = None
            continue
        if program is None or c0.startswith(("備註", "總計")):
            continue
        # 合併儲存格：只有第一格有值，其餘為空，沿用上一個
        if pd.notna(r[1]):
            college = re.sub(r"[（(].*?[)）]", "", str(r[1])).strip()
        if pd.notna(r[2]):
            dept = str(r[2]).strip()
        elif i not in merged and pd.notna(r[3]):
            dept = next(str(v).strip() for v in raw.loc[i + 1:, 2] if pd.notna(v))
        if pd.isna(r[3]) or pd.isna(r[5]) or pd.isna(r[6]):
            continue  # 不是資料列（備註等）
        rows.append((college, dept, program, "女", int(r[5])))
        rows.append((college, dept, program, "男", int(r[6])))

    df = pd.DataFrame(rows, columns=["college", "dept_raw", "program_raw", "gender", "count"])
    df = df.groupby(["college", "dept_raw", "program_raw", "gender"], sort=False, as_index=False)["count"].sum()
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"{len(df)} rows, total={df['count'].sum()} -> {OUT}")


if __name__ == "__main__":
    main()
