# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""把 data/ 的三個 CSV 整理成網頁可直接載入的 docs/data.js（window.DATA）。"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data.js"
read = lambda name: pd.read_csv(ROOT / "data" / name, encoding="utf-8-sig")

enr = read("enrollment.csv")
leave = read("leave.csv")
mapping = read("dept_mapping.csv")

enrollment = (enr.groupby(["semester", "college", "dept", "degree", "gender"], as_index=False)["count"].sum())
leave_rows = (leave.groupby(["semester", "college", "dept", "degree", "gender", "reason"], as_index=False)
              [["new_leave", "on_leave_end"]].sum())

depts = [
    {"dept": r.dept, "college": r.college,
     "aliases": [a.strip() for a in str(r.aliases).split(";") if a.strip()] if pd.notna(r.aliases) else []}
    for r in mapping.itertuples()
]

data = {
    "semesters": sorted(enr["semester"].unique()),
    # 欄位：semester, college, dept, degree, gender, count
    "enrollment": enrollment.to_dict("records"),
    # new_leave = 學期間休學人數；on_leave_end = 學期底處於休學狀態人數
    "leave": leave_rows.to_dict("records"),
    "depts": depts,
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

# 核對
chk = enrollment[enrollment.semester == "114-1"]["count"].sum()
assert chk == 10035, chk
assert enrollment["count"].sum() == enr["count"].sum()
assert leave_rows[["new_leave", "on_leave_end"]].sum().equals(leave[["new_leave", "on_leave_end"]].sum())
print(f"114-1 在學人數合計 {chk} ✅")
print(f"enrollment {len(enrollment)} 列, leave {len(leave_rows)} 列, depts {len(depts)} 筆")
print(f"{OUT.name}: {OUT.stat().st_size/1024:.0f} KB")
