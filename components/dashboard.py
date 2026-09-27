import sqlite3
from pathlib import Path

import streamlit as st

from database.database import get_connection
from services.pdf_service import generate_pdf_report


def fetch_dashboard_stats(user_id):
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS count FROM inspections WHERE user_id = ?", (user_id,)).fetchone()["count"]
        passed = conn.execute("SELECT COUNT(*) AS count FROM inspections WHERE user_id = ? AND result = 'PASS'", (user_id,)).fetchone()["count"]
        failed = conn.execute("SELECT COUNT(*) AS count FROM inspections WHERE user_id = ? AND result = 'FAIL'", (user_id,)).fetchone()["count"]
        defects = conn.execute("SELECT COUNT(*) AS count FROM inspections WHERE user_id = ? AND defects IS NOT NULL", (user_id,)).fetchone()["count"]
        recent = conn.execute(
            "SELECT * FROM inspections WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5",
            (user_id,),
        ).fetchall()
        return {"total": total, "passed": passed, "failed": failed, "defects": defects, "recent": recent}
    finally:
        conn.close()


def render_dashboard(user):
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-badge">Overview</div>
            <h2 style="margin:0; color:#f8fbff;">Dashboard</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    stats = fetch_dashboard_stats(user["id"])

    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Total Inspections", stats["total"])
    with summary_cols[1]:
        st.metric("Passed", stats["passed"])
    with summary_cols[2]:
        st.metric("Failed", stats["failed"])
    with summary_cols[3]:
        st.metric("Defects Detected", stats["defects"])

    st.subheader("Recent Inspections")
    if not stats["recent"]:
        st.info("No inspections yet. Start a new inspection to get results.")
    else:
        for item in stats["recent"]:
            defect_count = len(item["defects"].split(",")) if item["defects"] else 0
            with st.container():
                st.markdown(f"### {item['product_name']}  ·  {item['result']}")
                st.write(f"Category: {item['category']}")
                st.write(f"Confidence: {float(item['confidence'] or 0) * 100:.0f}% | Defects: {defect_count} | Severity: {item['severity']}")
                st.write(f"Summary: {item['summary']}")
                st.markdown("---")

    st.markdown("## Reports")
    from components.dashboard import render_reports_page
    render_reports_page(user)


def render_reports_page(user):
    st.subheader("Reports")
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM inspections WHERE user_id = ? ORDER BY timestamp DESC",
            (user["id"],),
        ).fetchall()
        if not rows:
            st.info("No reports available yet.")
            return

        for item in rows:
            with st.expander(f"{item['product_name']} - {item['result']} - {item['timestamp']}"):
                st.write(f"Category: {item['category']}")
                st.write(f"Summary: {item['summary']}")
                st.write(f"Recommendation: {item['recommendation']}")
                st.write(f"Confidence: {float(item['confidence'] or 0) * 100:.0f}%")

                report_path = Path(__file__).resolve().parent.parent / "reports" / "generated" / f"report_{item['id']}.pdf"
                if not report_path.exists():
                    try:
                        generate_pdf_report(str(report_path), dict(item), user)
                    except Exception:
                        pass

                with open(report_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_file.read(),
                        file_name=f"report_{item['id']}.pdf",
                        mime="application/pdf",
                        key=f"download_report_{item['id']}",
                    )
    finally:
        conn.close()
