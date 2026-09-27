import streamlit as st

from database.database import get_connection
from services.pdf_service import generate_pdf_report


def render_history_page(user):
    st.title("Inspection History")
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM inspections WHERE user_id = ? ORDER BY timestamp DESC",
            (user["id"],),
        ).fetchall()
        if not rows:
            st.info("No prior inspections found.")
            return

        for row in rows:
            with st.expander(f"#{row['id']} - {row['product_name']} - {row['result']} - {row['timestamp']}"):
                st.write(f"Category: {row['category']}")
                st.write(f"Confidence: {float(row['confidence'] or 0) * 100:.0f}%")
                st.write(f"Defects: {row['defects']}")
                st.write(f"Severity: {row['severity']}")
                st.write(f"Summary: {row['summary']}")
                st.write(f"Recommendation: {row['recommendation']}")
                if row["image_path"]:
                    st.image(row["image_path"], caption="Inspection image", use_container_width=True)

                report_path = f"reports/generated/report_{row['id']}.pdf"
                try:
                    generate_pdf_report(report_path, dict(row), user)
                except Exception:
                    pass

                with open(report_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_file.read(),
                        file_name=f"report_{row['id']}.pdf",
                        mime="application/pdf",
                        key=f"history_pdf_{row['id']}",
                    )
    finally:
        conn.close()
