import streamlit as st

from database.database import get_connection
from services.auth_service import change_password


def render_profile_page(user):
    st.title("Profile")
    conn = get_connection()
    try:
        total_inspections = conn.execute("SELECT COUNT(*) FROM inspections WHERE user_id = ?", (user["id"],)).fetchone()[0]
    finally:
        conn.close()

    st.write(f"Name: {user['full_name']}")
    st.write(f"WhatsApp number: {user['whatsapp_number']}")
    st.write(f"Verification status: {'Verified' if user.get('is_verified') or user.get('whatsapp_verified') else 'Pending'}")
    st.write(f"Account creation date: {user.get('created_at', 'N/A')}")
    st.write(f"Total inspections: {total_inspections}")

    st.subheader("Change Password")
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password")
        if submitted:
            if new_password != confirm_new_password:
                st.error("New passwords do not match.")
            else:
                try:
                    change_password(user["id"], current_password, new_password)
                    st.success("Password updated successfully.")
                except ValueError as exc:
                    st.error(str(exc))
