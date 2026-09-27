from pathlib import Path

import streamlit as st

from database.database import get_connection
from services.pdf_service import generate_pdf_report
from services.vision_service import analyze_product_image
from services.whatsapp_service import send_whatsapp_message
from utils.config import whatsapp_is_configured
from utils.helpers import save_uploaded_image


def _build_defects_entry(defect_data):
    if not isinstance(defect_data, list):
        return []
    defects = []
    for defect in defect_data:
        if isinstance(defect, dict):
            defects.append({
                "type": defect.get("type", "Visible defect"),
                "description": defect.get("description", "Visible defect detected."),
                "severity": defect.get("severity", "Medium"),
            })
    return defects


def _store_inspection(user, product_name, category, result_data, image_path):
    defects = _build_defects_entry(result_data.get("defects", []))
    defects_text = ", ".join([item["type"] for item in defects]) if defects else "None"

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO inspections (
                user_id, product_name, category, result, confidence, defects, severity,
                summary, recommendation, timestamp, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """,
            (
                user["id"],
                product_name,
                category,
                result_data.get("result", "INVALID"),
                float(result_data.get("confidence", 0.0) or 0.0),
                defects_text,
                result_data.get("severity", "Unknown"),
                result_data.get("summary", "Inspection complete."),
                result_data.get("recommendation", "Review manually before approval."),
                image_path,
            ),
        )
        conn.commit()
        inspection_id = cursor.lastrowid

        for item in defects:
            conn.execute(
                "INSERT INTO inspection_details (inspection_id, defect_type, defect_description, defect_severity) VALUES (?, ?, ?, ?)",
                (inspection_id, item["type"], item["description"], item["severity"]),
            )
        conn.commit()
        return inspection_id
    finally:
        conn.close()


def render_inspection_page(user):
    st.title("New Inspection")
    st.caption("This system performs AI-assisted visual inspection only and does not replace required professional quality-control procedures.")

    with st.form("inspection_form", clear_on_submit=False):
        product_name = st.text_input("Product Name")
        product_category = st.selectbox("Product Category", ["Electronics", "Packaging", "Textile", "Industrial", "Other"])
        uploaded_image = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])
        camera_capture = st.camera_input("Or capture from camera")
        submitted = st.form_submit_button("Start AI Inspection")

        if submitted:
            try:
                image_file = uploaded_image or camera_capture
                if image_file is None:
                    raise ValueError("Please upload or capture a product image.")

                image_path = save_uploaded_image(image_file)
                result = analyze_product_image(image_path, product_name, product_category)

                if result.get("result") == "INVALID":
                    st.error(result.get("summary", "The uploaded image does not appear to contain a valid product."))
                    st.info(result.get("recommendation", "Upload a clear product image."))
                    return

                inspection_id = _store_inspection(user, product_name, product_category, result, image_path)
                st.session_state.current_inspection = {
                    "id": inspection_id,
                    "product_name": product_name,
                    "category": product_category,
                    "result": result.get("result", "FAIL"),
                    "confidence": result.get("confidence", 0),
                    "defects": result.get("defects", []),
                    "severity": result.get("severity", "Unknown"),
                    "summary": result.get("summary", "Inspection complete."),
                    "recommendation": result.get("recommendation", "Review manually before approval."),
                    "image_path": image_path,
                }

                def severity_color(level):
                    return {"None": "green", "Low": "orange", "Medium": "orange", "High": "red", "Unknown": "gray"}.get(level, "gray")

                if result.get("result") == "PASS":
                    st.success("✅ QUALITY PASS")
                else:
                    st.error("❌ QUALITY FAIL")

                st.subheader("Inspection Result")
                st.write(f"Product: {product_name}")
                st.write(f"Confidence: {float(result.get('confidence', 0) or 0) * 100:.0f}%")
                st.write(f"Defects: {len(result.get('defects', []))}")
                st.write(f"Severity: {result.get('severity', 'Unknown')}")
                st.write(f"Summary: {result.get('summary', 'No summary available.')}")

                if result.get("defects"):
                    for idx, defect in enumerate(result["defects"], start=1):
                        st.markdown(f"### Defect {idx}")
                        st.write(f"Type: {defect.get('type', 'Visible defect')}")
                        st.write(f"Severity: {defect.get('severity', 'Medium')}")
                        st.write(f"Description: {defect.get('description', 'Not provided')}")

                st.markdown("### AI Recommendation")
                st.write(result.get("recommendation", "Review manually before approval."))
                st.warning("This is an AI-assisted visual inspection and should not replace required professional quality-control procedures.")

                notification_message = (
                    f"Hello {user['full_name']}!\n\n"
                    "Your product inspection has been completed.\n\n"
                    f"Product: {product_name}\n"
                    f"Result: {('✅ PASS' if result.get('result') == 'PASS' else '❌ FAIL')}\n"
                    f"Defects detected: {len(result.get('defects', []))}\n"
                    f"Severity: {result.get('severity', 'Unknown')}\n"
                    f"Confidence: {float(result.get('confidence', 0) or 0) * 100:.0f}%\n\n"
                    "Please open the AI Product Quality Inspector application to view the complete report."
                )
                if whatsapp_is_configured():
                    send_whatsapp_message(user["whatsapp_number"], notification_message)
                else:
                    st.info("WhatsApp integration is not configured.")
                    st.warning("Development mode: no real message was sent.")

                st.success("Inspection saved successfully.")

                report_path = Path(__file__).resolve().parent.parent / "reports" / "generated" / f"report_{inspection_id}.pdf"
                if generate_pdf_report(str(report_path), {
                    "id": inspection_id,
                    "product_name": product_name,
                    "category": product_category,
                    "result": result.get("result", "FAIL"),
                    "confidence": result.get("confidence", 0),
                    "defects": result.get("defects", []),
                    "severity": result.get("severity", "Unknown"),
                    "summary": result.get("summary", "Inspection complete."),
                    "recommendation": result.get("recommendation", "Review manually before approval."),
                    "timestamp": "Just now",
                }, user):
                    with open(report_path, "rb") as pdf_file:
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_file.read(),
                            file_name=f"report_{inspection_id}.pdf",
                            mime="application/pdf",
                            key=f"download_report_after_{inspection_id}",
                        )
                else:
                    st.warning("PDF generation was not available for this inspection.")

            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("The inspection could not be completed. Please check the uploaded image and try again.")
