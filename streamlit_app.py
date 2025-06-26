from fastapi import requests
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


def chatbot_page():
    st.subheader("💬 Chat Interface")

    tabs = st.tabs(["Text Chat", "Chat with PDF", "Chat with Audio", "Email Assistant", "Token Usage"])

    # Show previous chat messages
    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role.capitalize()}**: {msg}")

    # Text Chat
    with tabs[0]:
        with st.form("text_chat_form"):
            user_input = st.text_input("You:", key="chat_input_text")
            send_text = st.form_submit_button("Send (Text Chat)")

        if send_text:
            if not user_input.strip():
                st.warning("Please enter a message.")
            else:
                response = httpx.post(
                    f"{API_BASE_URL}/chat/query",
                    json={
                        "question": user_input.strip(),
                        "session_id": f"normal_{st.session_state.email}"
                    },
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if response.status_code == 200:
                    res = response.json()
                    answer = res.get("answer", "No response.")
                    token_usage = res.get("token_usage", {})

                    st.session_state.chat_history.append(("user", user_input))
                    st.session_state.chat_history.append(("bot", answer))
                    st.success(f"Tokens used — Prompt: {token_usage.get('prompt_tokens', 0)}, Completion: {token_usage.get('completion_tokens', 0)}")
                    st.rerun()
                else:
                    st.error("Text chat failed.")

    # Chat with PDF
    with tabs[1]:
        with st.form("pdf_chat_form"):
            uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
            pdf_question = st.text_input("Ask a question based on the PDF:")
            send_pdf = st.form_submit_button("Send (PDF)")

        if send_pdf:
            if not uploaded_pdf or not pdf_question.strip():
                st.warning("Please upload a PDF and enter a question.")
            else:
                files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
                data = {
                    "question": pdf_question.strip(),
                    "session_id": f"pdf_{st.session_state.email}"
                }

                response = httpx.post(
                    f"{API_BASE_URL}/chat/pdf-query",
                    data=data,
                    files=files,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if response.status_code == 200:
                    res = response.json()
                    answer = res.get("answer", "No response.")
                    token_usage = res.get("token_usage", {})

                    st.session_state.chat_history.append(("user", f"[PDF Q] {pdf_question}"))
                    st.session_state.chat_history.append(("bot", answer))
                    st.success(f"Tokens used — Prompt: {token_usage.get('prompt_tokens', 0)}, Completion: {token_usage.get('completion_tokens', 0)}")
                    st.rerun()
                else:
                    st.error("PDF chat failed.")

    # Chat with Audio
    with tabs[2]:
        uploaded_audio = st.file_uploader("Upload audio file", type=["mp3", "wav", "m4a"])
        if uploaded_audio and st.button("Send (Audio)", key="send_audio"):
            files = {"file": (uploaded_audio.name, uploaded_audio, "audio/mpeg")}
            response = httpx.post(
                f"{API_BASE_URL}/chat/audio-query",
                params={"question": "Transcribe and respond to this audio"},
                files=files
            )
            if response.status_code == 200:
                answer = response.json().get("answer", "No response.")
                st.session_state.chat_history.append(("user", "[Audio Uploaded]"))
                st.session_state.chat_history.append(("bot", answer))
                st.rerun()
            else:
                st.error("Audio chat failed.")

    # ✅ Email Assistant
        # ✅ Email Assistant
    # ✅ Email Assistant
    with tabs[3]:
        st.info("📬 Email Assistant - Fetch and summarize important emails")

        if "fetched_emails" not in st.session_state:
            st.session_state.fetched_emails = []
        if "email_summaries" not in st.session_state:
            st.session_state.email_summaries = {}
        if "email_token_usage" not in st.session_state:
            st.session_state.email_token_usage = {}

        # 🔄 Fetch Emails Button
        if st.button("🔄 Fetch Emails"):
            try:
                response = httpx.post(
                    f"{API_BASE_URL}/email_router/list",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=30
                )
                if response.status_code == 200:
                    st.success("✅ Fetched important emails.")
                    st.session_state.fetched_emails = response.json().get("emails", [])
                elif response.status_code == 400:
                    st.warning("⚠️ Gmail is not connected.")
                    connect_url = f"{API_BASE_URL}/gmail/connect-gmail-dev?email={st.session_state.email}"
                    st.markdown(f"[🔗 Connect Gmail]({connect_url})")
                else:
                    st.error("❌ Something went wrong while fetching emails.")
            except httpx.ReadTimeout:
                st.error("⏱️ Timeout while fetching emails.")

        # 📬 Display Emails in Table
        if st.session_state.fetched_emails:
            total_prompt = total_completion = 0

            for email in st.session_state.fetched_emails:
                col1, col2 = st.columns([0.75, 0.25])

                with col1:
                    st.markdown(f"""
                    **Subject:** {email['subject']}  
                    **From:** {email['from']}  
                    **Label:** `{email['label']}`  
                    [📧 View in Gmail](https://mail.google.com/mail/u/0/#inbox/{email['id']})
                    """)

                    # Show summary if already done
                    if email["id"] in st.session_state.email_summaries:
                        st.markdown(f"📝 **Summary:** {st.session_state.email_summaries[email['id']]}")
                        usage = st.session_state.email_token_usage.get(email["id"], {})
                        if usage:
                            st.markdown(f"""
                            🔢 **Tokens used**:  
                            - Prompt: `{usage.get('prompt_tokens', 0)}`  
                            - Completion: `{usage.get('completion_tokens', 0)}`  
                            - Total: `{usage.get('total_tokens', 0)}`
                            """)

                            # Add to total count
                            total_prompt += usage.get('prompt_tokens', 0)
                            total_completion += usage.get('completion_tokens', 0)

                with col2:
                    if st.button("🧠 Summarize", key=f"summarize_{email['id']}"):
                        sres = httpx.post(
                            f"{API_BASE_URL}/email_router/summarize",
                            params={"email_id": email["id"]},
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if sres.status_code == 200:
                            res_json = sres.json()
                            summary = res_json["summary"]
                            tokens = res_json.get("token_usage", {})

                            st.session_state.email_summaries[email["id"]] = summary
                            st.session_state.email_token_usage[email["id"]] = tokens

                            st.success(f"✅ Summary generated. Tokens used - Prompt: {tokens.get('prompt_tokens', 0)}, Completion: {tokens.get('completion_tokens', 0)}")
                            st.rerun()
                        else:
                            st.error("❌ Failed to summarize this email.")

            # 📊 Show total usage at the bottom
            total_tokens = total_prompt + total_completion
            if total_tokens > 0:
                st.markdown("---")
                st.markdown(f"📈 **Total Tokens Used for Summarization:**")
                st.markdown(f"- Prompt Tokens: `{total_prompt}`")
                st.markdown(f"- Completion Tokens: `{total_completion}`")
                st.markdown(f"- **Total Tokens**: `{total_tokens}`")

    # 📊 Token Usage Tab
    with tabs[4]:
        st.info("📈 Token Usage Over Time")

        try:
            res = httpx.get(
                f"{API_BASE_URL}/analytics/usage",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if res.status_code == 200:
                usage_data = res.json()

                if usage_data:
                    import pandas as pd

                    df = pd.DataFrame(usage_data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])

                    # Plot total tokens over time
                    st.line_chart(
                        df.set_index("timestamp")[["total_tokens"]],
                        use_container_width=True
                    )

                    with st.expander("📄 Detailed Log"):
                        st.dataframe(df[["timestamp", "total_tokens", "message"]].sort_values(by="timestamp", ascending=False))

                else:
                    st.warning("ℹ️ No token usage yet.")

            else:
                st.error("❌ Failed to fetch usage data.")
        except Exception as e:
            st.error(f"🚨 Error: {e}")

if st.session_state.logged_in:
    chatbot_page()
else:
    login_signup_page()