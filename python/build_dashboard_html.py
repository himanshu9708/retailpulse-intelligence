"""
Phase 11 — builds the final standalone dashboard HTML by embedding
powerbi/dashboard_data.json into powerbi/dashboard_template.html.

Run after python/export_dashboard_data.py:
    python python/build_dashboard_html.py
"""

from pathlib import Path

POWERBI_DIR = Path(__file__).resolve().parent.parent / "powerbi"
TEMPLATE_PATH = POWERBI_DIR / "dashboard_template.html"
DATA_PATH = POWERBI_DIR / "dashboard_data.json"
OUT_PATH = POWERBI_DIR / "executive_dashboard.html"


def main():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    data_json = DATA_PATH.read_text(encoding="utf-8")
    output = template.replace("__DASHBOARD_DATA__", data_json)
    OUT_PATH.write_text(output, encoding="utf-8")
    print(f"Dashboard built: {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
