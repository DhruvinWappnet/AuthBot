import streamlit as st
import httpx

from app.core.session_store import generate_session_token
# from streamlit_extras.app_cookie_manager import CookieManager

API_BASE_URL = "http://localhost:8000"  # Replace with your actual backend URL

# --- Cookie Manager Setup ---
# cookie_manager = CookieManager()

# --- Set Page Config ---
st.set_page_config(page_title="Chatbot App", page_icon="🤖")

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "email" not in st.session_state:
    st.session_state.email = ""
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

# --- Restore Session from Cookie (if exists) ---
# cookie_token = cookie_manager.get("session_token")
# if cookie_token and not st.session_state.logged_in:
#     try:
#         with httpx.Client() as client:
#             response = client.post(f"{API_BASE_URL}/auth/session", json={"session_token": cookie_token})
#         if response.status_code == 200:
#             data = response.json()
#             st.session_state.logged_in = True
#             st.session_state.token = data.get("access_token", "")
#             st.session_state.email = data.get("email", "")
#     except Exception as e:
#         st.warning(f"Session restore failed: {e}")

# --- Sidebar (Logout) ---
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("### 👤 Logged in as:")
        st.write(st.session_state.email)
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.token = ""
            st.session_state.email = ""
            st.session_state.chat_history = []
            st.session_state.chat_input = ""
            # cookie_manager.delete("session_token")
            st.rerun()

# --- Title ---
st.title("🤖 AI Chatbot")

# --- Login/Signup Page ---
def login_signup_page():
    auth_mode = st.radio("Choose Auth Mode", ["Login", "Signup"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if auth_mode == "Signup":
        confirm_password = st.text_input("Confirm Password", type="password")

    if st.button(auth_mode):
        if not email or not password:
            st.warning("Please fill in all required fields.")
        elif auth_mode == "Signup" and password != confirm_password:
            st.error("Passwords do not match.")
        else:
            try:
                with httpx.Client() as client:
                    endpoint = f"{API_BASE_URL}/auth/{auth_mode.lower()}"
                    response = client.post(endpoint, json={"email": email, "password": password})
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"{auth_mode} successful!")
                    st.session_state.logged_in = True
                    st.session_state.token = data.get("access_token", "")
                    st.session_state.email = email
                    # cookie_manager.set("session_token", data.get("session_token"))
                    st.rerun()
                else:
                    st.error("Invalid credentials or user already exists.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- Chatbot Page ---

# def chatbot_page():
#     st.subheader("Ask me anything 🤖")

#     # Display past chat history
#     for role, msg in st.session_state.chat_history:
#         if role == "user":
#             st.markdown(f"**You:** {msg}")
#         else:
#             st.markdown(f"**Bot:** {msg}")

#     # Input box with state tracking
#     st.session_state.chat_input = st.text_input("You:", value=st.session_state.chat_input, key="chat_input_box")

#     if st.button("Send"):
#         user_input = st.session_state.chat_input.strip()
#         if not user_input:
#             st.warning("Please enter a message.")
#         else:
#             try:
#                 with httpx.Client() as client:
#                     headers = {"Authorization": f"Bearer {st.session_state.token}"}
#                     response = client.post(
#                         f"{API_BASE_URL}/chat/query",
#                          json={
#                                 "question": user_input,
#                                 "session_id": generate_session_token(st.session_state.email)  # or any unique session ID
#                             },
#                         headers=headers
#                     )
#                 if response.status_code == 200:
#                     reply = response.json().get("answer", "No response.")

#                     # Save messages
#                     st.session_state.chat_history.append(("user", user_input))
#                     st.session_state.chat_history.append(("bot", reply))

#                     # ✅ Clear the input before rerun
#                     st.session_state.chat_input = ""
#                     st.rerun()
#                 else:
#                     st.error("Failed to get response from server.")
#             except Exception as e:
#                 st.error(f"Exception occurred: {e}")

# Chatbot page
def chatbot_page():
    st.subheader("📄 Chat with your PDF")

    uploaded_pdf = st.file_uploader("Upload a PDF to start chatting", type=["pdf"])

    if uploaded_pdf:
        prev_pdf = st.session_state.get("uploaded_pdf_name", None)
        if uploaded_pdf.name != prev_pdf:
            st.session_state.chat_history = []
            st.session_state.uploaded_pdf = uploaded_pdf
            st.session_state.uploaded_pdf_name = uploaded_pdf.name

    if "uploaded_pdf" not in st.session_state:
        st.info("Please upload a PDF to begin chatting.")
        return

    # 🔄 Clear input before rendering input box (must come before st.text_input)
    if "clear_input" in st.session_state and st.session_state.clear_input:
        st.session_state.chat_input_box = ""
        st.session_state.clear_input = False

    # Show previous chat history
    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role.capitalize()}**: {msg}")

    # Input box
    user_input = st.text_input("You:", key="chat_input_box")

    if st.button("Send"):
        user_input = user_input.strip()
        if not user_input:
            st.warning("Please enter a message.")
            return

        # Save last 15 messages
        history = st.session_state.chat_history[-15:]
        messages = [{"role": role, "content": msg} for role, msg in history]

        try:
            files = {
                "file": (
                    st.session_state.uploaded_pdf.name,
                    st.session_state.uploaded_pdf,
                    "application/pdf"
                )
            }
            response = httpx.post(
                f"{API_BASE_URL}/chat/pdf-query",
                params={"question": user_input},
                files=files
            )
            if response.status_code == 200:
                bot_reply = response.json().get("answer", "No response.")
                st.session_state.chat_history.append(("user", user_input))
                st.session_state.chat_history.append(("bot", bot_reply))
                st.session_state.chat_history = st.session_state.chat_history[-15:]

                # ✅ Signal to clear input box on next rerun
                st.session_state.clear_input = True
                st.rerun()
            else:
                st.error("Failed to get response from server.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- Routing ---
if st.session_state.logged_in:
    chatbot_page()
else:
    login_signup_page()
