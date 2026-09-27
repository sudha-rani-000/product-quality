import streamlit as st

from services.auth_service import login_user, register_user, resend_otp, verify_otp
from services.whatsapp_service import send_whatsapp_message
from utils.config import whatsapp_is_configured


def render_auth_view():
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-badge">Quality control</div>
            <h1 style="margin:0; color:#f8fbff; font-size:2.4rem;">AI Product Quality Inspector</h1>
            <p style="margin:0.7rem 0 0; color:#b7c7dd; font-size:1.05rem;">Secure product inspection, smarter defect detection, and instant result notifications.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Login", "Register"])

    with tabs[0]:
        with st.form("login_form", clear_on_submit=False):
            st.write("Login")
            phone = st.text_input("WhatsApp Number", placeholder="+91XXXXXXXXXX")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                try:
                    user = login_user(phone, password)
                    st.session_state.user = user
                    st.success(f"Welcome back, {user['full_name']}!")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with tabs[1]:
        with st.form("register_form", clear_on_submit=False):
            st.write("Create an account")
            full_name = st.text_input("Full Name")
            whatsapp_number = st.text_input("WhatsApp Number", placeholder="+91XXXXXXXXXX")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                try:
                    user_data = register_user(full_name, whatsapp_number, password, confirm_password)
                    st.session_state.pending_user = {
                        "id": user_data["id"],
                        "full_name": user_data["full_name"],
                        "whatsapp_number": user_data["whatsapp_number"],
                        "is_verified": False,
                    }
                    st.session_state.user = {
                        "id": user_data["id"],
                        "full_name": user_data["full_name"],
                        "whatsapp_number": user_data["whatsapp_number"],
                        "whatsapp_verified": False,
                        "is_verified": False,
                    }
                    st.session_state.pending_verification = True
                    st.session_state.dev_otp = user_data["otp_code"]

                    message = (
                        f"Welcome {user_data['full_name']}!\n\n"
                        f"Your AI Product Quality Inspector account has been created successfully.\n\n"
                        f"Your verification OTP is: {user_data['otp_code']}\n\n"
                        "Please enter this OTP in the application to verify your WhatsApp number."
                    )

                    result = send_whatsapp_message(
                        user_data["whatsapp_number"],
                        message,
                        development_mode=not whatsapp_is_configured(),
                        development_otp=user_data["otp_code"],
                    )

                    if result.get("status") == "development":
                        st.warning("WhatsApp integration is not configured. Development mode enabled.")
                        st.info(f"Development OTP: {user_data['otp_code']}")
                    elif result.get("status") == "error":
                        st.warning("Registration succeeded, but WhatsApp message delivery failed. Please use the development OTP shown below.")
                        st.info(f"Development OTP: {user_data['otp_code']}")
                    else:
                        st.success("Account created successfully. Please complete WhatsApp verification.")

                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


def render_verification_screen(user):
    st.title("WhatsApp Verification")
    st.write("Enter the 6-digit verification code sent to your WhatsApp number.")
    st.info(f"Number: {user['whatsapp_number']}")

    if not whatsapp_is_configured():
        st.warning("WhatsApp integration is not configured.")
        st.info(f"Development OTP: {st.session_state.get('dev_otp') or 'Not available'}")

    otp = st.text_input("OTP", max_chars=6, placeholder="123456")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Verify"):
            try:
                verify_otp(user["id"], otp)
                user_record = {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "whatsapp_number": user["whatsapp_number"],
                    "whatsapp_verified": True,
                    "is_verified": True,
                }
                st.session_state.user = user_record
                st.session_state.pending_verification = False
                st.session_state.dev_otp = None

                message = (
                    f"Hello {user['full_name']}!\n\n"
                    "Your WhatsApp number has been successfully verified.\n\n"
                    "Your AI Product Quality Inspector account is now ready."
                )
                send_whatsapp_message(user["whatsapp_number"], message, development_mode=not whatsapp_is_configured(), development_otp=st.session_state.get("dev_otp"))

                st.success("WhatsApp number verified successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with col2:
        if st.button("Resend OTP"):
            try:
                new_otp = resend_otp(user["id"])
                st.session_state.dev_otp = new_otp
                message = (
                    f"Welcome {user['full_name']}!\n\n"
                    f"Your verification OTP is: {new_otp}\n\n"
                    "Please enter this OTP in the application to verify your WhatsApp number."
                )
                send_whatsapp_message(user["whatsapp_number"], message, development_mode=not whatsapp_is_configured(), development_otp=new_otp)
                st.success("A new OTP has been generated.")
                st.info(f"Development OTP: {new_otp}")
            except ValueError as exc:
                st.error(str(exc))
