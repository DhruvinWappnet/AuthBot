import threading
import streamlit as st
import httpx
import pandas as pd

from app.services.email_embedding_service import trigger_embedding_background

API_BASE_URL = "http://localhost:8000"

# --- Session State Initialization ---
for key in ["logged_in", "token", "email"]:
    if key not in st.session_state:
        st.session_state[key] = ""

for history_key in ["chat_history_text", "chat_history_pdf", "chat_history_audio","chat_history_email"]:
    if history_key not in st.session_state:
        st.session_state[history_key] = []

# --- Sidebar ---
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("### 👤 Logged in as:")
        st.write(st.session_state.email)
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- Page Title ---
st.set_page_config(page_title="Chatbot App", page_icon="🤖")
st.title("🤖 AI Chatbot")

# --- Auth Page ---
def login_signup_page():
    login_success = False  # 👈 Flag to return

    mode = st.radio("Auth Mode", ["Login", "Signup"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if mode == "Signup":
        confirm = st.text_input("Confirm Password", type="password")

    if st.button(mode):
        if not email or not password:
            st.warning("Please fill all fields.")
        elif mode == "Signup" and password != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                r = httpx.post(f"{API_BASE_URL}/auth/{mode.lower()}", json={"email": email, "password": password})
                if r.status_code == 200:
                    data = r.json()
                    st.session_state.logged_in = True
                    st.session_state.token = data["access_token"]
                    st.session_state.email = email
                    login_success = True
                    # st.rerun()
                else:
                    st.error("Auth failed.")
            except Exception as e:
                st.error(f"Error: {e}")
    return login_success

# --- Helper to Render Chat ---
def render_chat(history_key):
    for role, msg in st.session_state[history_key]:
        icon = "🧑" if role == "user" else "🤖"
        st.markdown(f"{icon} **{role.capitalize()}**: {msg}")

# --- Main Chatbot UI ---
def chatbot_page():
    tabs = st.tabs(["Text Chat", "Chat with PDF", "Chat with Audio", "Email Assistant","Token Usage","Chat With Email"])

    # --- Text Chat Tab ---
    with tabs[0]:
        render_chat("chat_history_text")
        with st.form("text_form"):
            user_input = st.text_input("You:", key="text_input")
            if st.form_submit_button("Send"):
                if user_input.strip():
                    res = httpx.post(
                        f"{API_BASE_URL}/chat/query",
                        json={"question": user_input, "session_id": f"normal_{st.session_state.email}"},
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.chat_history_text.append(("user", user_input))
                        st.session_state.chat_history_text.append(("bot", data["answer"]))
                        st.rerun()
                    else:
                        st.error("Text chat failed.")

    # --- PDF Chat Tab ---
    with tabs[1]:
        render_chat("chat_history_pdf")
        with st.form("pdf_form"):
            pdf = st.file_uploader("Upload PDF", type=["pdf"])
            question = st.text_input("Ask about PDF")
            if st.form_submit_button("Send PDF") and pdf and question:
                files = {"file": (pdf.name, pdf, "application/pdf")}
                data = {"question": question, "session_id": f"pdf_{st.session_state.email}"}
                r = httpx.post(f"{API_BASE_URL}/chat/pdf-query", data=data, files=files,
                               headers={"Authorization": f"Bearer {st.session_state.token}"})
                if r.status_code == 200:
                    st.session_state.chat_history_pdf.append(("user", question))
                    st.session_state.chat_history_pdf.append(("bot", r.json()["answer"]))
                    st.rerun()
                else:
                    st.error("PDF chat failed.")

    # --- Audio Chat Tab ---
    with tabs[2]:
        render_chat("chat_history_audio")
        audio = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"])
        if audio and st.button("Send Audio"):
            files = {"file": (audio.name, audio, "audio/mpeg")}
            r = httpx.post(f"{API_BASE_URL}/chat/audio-query",
                           params={"question": "Transcribe and respond"},
                           files=files)
            if r.status_code == 200:
                ans = r.json().get("answer", "No response.")
                st.session_state.chat_history_audio.append(("user", "[Audio Uploaded]"))
                st.session_state.chat_history_audio.append(("bot", ans))
                st.rerun()
            else:
                st.error("Audio chat failed.")

    # --- Email Assistant Tab ---
    with tabs[3]:
        st.info("📬 Email Assistant")
        if "fetched_emails" not in st.session_state:
            st.session_state.fetched_emails = []
        if "email_summaries" not in st.session_state:
            st.session_state.email_summaries = {}

        if st.button("🔄 Fetch Emails"):
            try:
                r = httpx.post(f"{API_BASE_URL}/email_router/list",
                               headers={"Authorization": f"Bearer {st.session_state.token}"},timeout=30)
                if r.status_code == 200:
                    st.session_state.fetched_emails = r.json().get("emails", [])
                elif r.status_code == 400:
                    st.warning("Connect Gmail first.")
                    connect_url = f"{API_BASE_URL}/gmail/connect-gmail-dev?email={st.session_state.email}"
                    st.markdown(f"[🔗 Connect Gmail]({connect_url})")
                else:
                    st.error("Fetch failed.")
            except Exception as e:
                st.error(f"Timeout: {e}")

        for email in st.session_state.fetched_emails:
            st.markdown(f"**Subject:** {email['subject']} | **From:** {email['from']}")
            st.markdown(f"[📧 Gmail Link](https://mail.google.com/mail/u/0/#inbox/{email['id']})")
            if email["id"] in st.session_state.email_summaries:
                st.markdown(f"📝 **Summary:** {st.session_state.email_summaries[email['id']]}")
            if st.button("🧠 Summarize", key=f"summarize_{email['id']}"):
                r = httpx.post(f"{API_BASE_URL}/email_router/summarize",
                               params={"email_id": email["id"]},
                               headers={"Authorization": f"Bearer {st.session_state.token}"})
                if r.status_code == 200:
                    st.session_state.email_summaries[email["id"]] = r.json()["summary"]
                    st.rerun()
                else:
                    st.error("Summarization failed.") 
   
    # --- Token Usage Tab ---
    with tabs[4]:
        st.info("📊 Token Usage")
        try:
            r = httpx.get(f"{API_BASE_URL}/analytics/usage",
                        headers={"Authorization": f"Bearer {st.session_state.token}"})
            if r.status_code == 200:
                usage = r.json()
                if usage:
                    df = pd.DataFrame(usage)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])

                    # 💡 Show token usage chart
                    st.line_chart(df.set_index("timestamp")[["total_tokens"]])

                    # 🕒 Duration chart
                    st.line_chart(df.set_index("timestamp")[["groq_duration", "api_duration"]])

                    # 💰 Summary
                    total_cost = df["cost"].sum()
                    st.metric("💰 Total Cost", f"${total_cost:.6f}")

                    # 📦 Group by model
                    model_summary = df.groupby("model").agg({
                        "total_tokens": "sum",
                        "cost": "sum"
                    }).reset_index()
                    st.markdown("### 📦 Model-wise Usage")
                    st.dataframe(model_summary.rename(columns={
                        "model": "Model",
                        "total_tokens": "Total Tokens",
                        "cost": "Total Cost ($)"
                    }))

                    # 📋 Full log with durations
                    with st.expander("📋 Full Log"):
                        st.dataframe(df[[
                            "timestamp", "model", "total_tokens", "cost",
                            "groq_duration", "api_duration", "message"
                        ]])
                else:
                    st.info("No usage yet.")
            else:
                st.error("Failed to fetch token usage.")
        except Exception as e:
            st.error(f"Error: {e}")
# --- Talk with Emails Tab ---
    
    with tabs[5]:
        st.info("💬 Ask questions based on your recent emails")

        # 🧠 Render previous chat history (User, Bot)
        for role, msg in st.session_state.chat_history_email:
            if role == "user":
                st.markdown(f"🧑 **You**: {msg}")
            elif role == "bot":
                st.markdown(f"🤖 **Bot**: {msg}")
            elif role == "system":
                st.markdown(f"⚙️ *{msg}*")

        # 📥 Ask a new question
        question = st.text_input("Ask a question (e.g., 'Do I have any meetings today?')", key="email_chat_input")
        if st.button("Ask Email Question"):
            if question.strip():
                with st.spinner("Thinking..."):
                    try:
                        res = httpx.post(
                            f"{API_BASE_URL}/chat/query-email",
                            json={"question": question, "session_id": f"email_{st.session_state.email}"},
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if res.status_code == 200:
                            answer = res.json()["answer"]
                            st.session_state.chat_history_email.append(("user", question))
                            st.session_state.chat_history_email.append(("bot", answer))
                            st.rerun()
                        else:
                            st.session_state.chat_history_email.append(("system", "❌ Failed to answer your question."))
                            st.rerun()
                    except Exception as e:
                        st.session_state.chat_history_email.append(("system", f"❌ Error: {e}"))
                        st.rerun()

# --- Start App ---
# if st.session_state.logged_in:
#     chatbot_page()
# else:
#     login_signup_page()
 
if st.session_state.logged_in:
    chatbot_page()
else:
    logged_in_now = login_signup_page()
    if logged_in_now:
        print("🔥 Starting email embedding thread...")

        # 🔁 Fire and forget background embedding
        threading.Thread(
            target=trigger_embedding_background,
            args=(st.session_state.token,),
            daemon=True
        ).start()
        st.rerun()  # rerun to load chatbot interface
