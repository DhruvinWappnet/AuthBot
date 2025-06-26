# from fastapi import requests
# import streamlit as st
# import httpx

# from app.core.session_store import generate_session_token
# # from streamlit_extras.app_cookie_manager import CookieManager

# API_BASE_URL = "http://localhost:8000"  # Replace with your actual backend URL

# # --- Cookie Manager Setup ---
# # cookie_manager = CookieManager()

# # --- Set Page Config ---
# st.set_page_config(page_title="Chatbot App", page_icon="🤖")

# # --- Session State Initialization ---
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "token" not in st.session_state:
#     st.session_state.token = ""
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []
# if "email" not in st.session_state:
#     st.session_state.email = ""
# if "chat_input" not in st.session_state:
#     st.session_state.chat_input = ""

# # --- Restore Session from Cookie (if exists) ---
# # cookie_token = cookie_manager.get("session_token")
# # if cookie_token and not st.session_state.logged_in:
# #     try:
# #         with httpx.Client() as client:
# #             response = client.post(f"{API_BASE_URL}/auth/session", json={"session_token": cookie_token})
# #         if response.status_code == 200:
# #             data = response.json()
# #             st.session_state.logged_in = True
# #             st.session_state.token = data.get("access_token", "")
# #             st.session_state.email = data.get("email", "")
# #     except Exception as e:
# #         st.warning(f"Session restore failed: {e}")

# # --- Sidebar (Logout) ---
# if st.session_state.logged_in:
#     with st.sidebar:
#         st.markdown("### 👤 Logged in as:")
#         st.write(st.session_state.email)
#         if st.button("🚪 Logout"):
#             st.session_state.logged_in = False
#             st.session_state.token = ""
#             st.session_state.email = ""
#             st.session_state.chat_history = []
#             st.session_state.chat_input = ""
#             # cookie_manager.delete("session_token")
#             st.rerun()

# # --- Title ---
# st.title("🤖 AI Chatbot")

# # --- Login/Signup Page ---
# def login_signup_page():
#     auth_mode = st.radio("Choose Auth Mode", ["Login", "Signup"], horizontal=True)
#     email = st.text_input("Email")
#     password = st.text_input("Password", type="password")

#     if auth_mode == "Signup":
#         confirm_password = st.text_input("Confirm Password", type="password")

#     if st.button(auth_mode):
#         if not email or not password:
#             st.warning("Please fill in all required fields.")
#         elif auth_mode == "Signup" and password != confirm_password:
#             st.error("Passwords do not match.")
#         else:
#             try:
#                 with httpx.Client() as client:
#                     endpoint = f"{API_BASE_URL}/auth/{auth_mode.lower()}"
#                     response = client.post(endpoint, json={"email": email, "password": password})
#                 if response.status_code == 200:
#                     data = response.json()
#                     st.success(f"{auth_mode} successful!")
#                     st.session_state.logged_in = True
#                     st.session_state.token = data.get("access_token", "")
#                     st.session_state.email = email
#                     # cookie_manager.set("session_token", data.get("session_token"))
#                     st.rerun()
#                 else:
#                     st.error("Invalid credentials or user already exists.")
#             except Exception as e:
#                 st.error(f"Error: {e}")

# # --- Chatbot Page ---


# # def chatbot_page():
# #     st.subheader("💬 Chat Interface")

# #     tabs = st.tabs(["Text Chat", "Chat with PDF", "Chat with Audio", "Email Assistant"])

# #     # Show previous chat messages
# #     for role, msg in st.session_state.chat_history:
# #         st.markdown(f"**{role.capitalize()}**: {msg}")

# #     # Text Chat
# #     with tabs[0]:
# #         with st.form("text_chat_form"):
# #             user_input = st.text_input("You:", key="chat_input_text")
# #             send_text = st.form_submit_button("Send (Text Chat)")

# #         if send_text:
# #             if not user_input.strip():
# #                 st.warning("Please enter a message.")
# #             else:
# #                 response = httpx.post(
# #                     f"{API_BASE_URL}/chat/query",
# #                     json={
# #                         "question": user_input.strip(),
# #                         "session_id": f"normal_{st.session_state.email}"
# #                     }
# #                 )
# #                 if response.status_code == 200:
# #                     answer = response.json().get("answer", "No response.")
# #                     st.session_state.chat_history.append(("user", user_input))
# #                     st.session_state.chat_history.append(("bot", answer))
# #                     st.rerun()
# #                 else:
# #                     st.error("Text chat failed.")

# #     # Chat with PDF
# #     with tabs[1]:
# #         with st.form("pdf_chat_form"):
# #             uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
# #             pdf_question = st.text_input("Ask a question based on the PDF:")
# #             send_pdf = st.form_submit_button("Send (PDF)")

# #         if send_pdf:
# #             if not uploaded_pdf or not pdf_question.strip():
# #                 st.warning("Please upload a PDF and enter a question.")
# #             else:
# #                 files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
# #                 data = {"question": pdf_question.strip()}
# #                 response = httpx.post(
# #                     f"{API_BASE_URL}/chat/pdf-query",
# #                     data=data,
# #                     files=files
# #                 )
# #                 if response.status_code == 200:
# #                     answer = response.json().get("answer", "No response.")
# #                     st.session_state.chat_history.append(("user", f"[PDF Q] {pdf_question}"))
# #                     st.session_state.chat_history.append(("bot", answer))
# #                     st.rerun()
# #                 else:
# #                     st.error("PDF chat failed.")

# #     # Chat with Audio
# #     with tabs[2]:
# #         uploaded_audio = st.file_uploader("Upload audio file", type=["mp3", "wav", "m4a"])
# #         if uploaded_audio and st.button("Send (Audio)", key="send_audio"):
# #             files = {"file": (uploaded_audio.name, uploaded_audio, "audio/mpeg")}
# #             response = httpx.post(
# #                 f"{API_BASE_URL}/chat/audio-query",
# #                 params={"question": "Transcribe and respond to this audio"},
# #                 files=files
# #             )
# #             if response.status_code == 200:
# #                 answer = response.json().get("answer", "No response.")
# #                 st.session_state.chat_history.append(("user", "[Audio Uploaded]"))
# #                 st.session_state.chat_history.append(("bot", answer))
# #                 st.rerun()
# #             else:
# #                 st.error("Audio chat failed.")

# #     # ✅ Email Assistant
# #         # ✅ Email Assistant
# #     with tabs[3]:
# #         st.info("📬 Email Assistant - Fetch and summarize important emails")

# #         if "fetched_emails" not in st.session_state:
# #             st.session_state.fetched_emails = []
# #         if "email_summaries" not in st.session_state:
# #             st.session_state.email_summaries = {}

# #         # 🔄 Fetch Emails Button
# #         if st.button("🔄 Fetch Emails"):
# #             try:
# #                 response = httpx.post(
# #                     f"{API_BASE_URL}/email_router/list",
# #                     headers={"Authorization": f"Bearer {st.session_state.token}"},
# #                     timeout=30
# #                 )
# #                 if response.status_code == 200:
# #                     st.success("✅ Fetched important emails.")
# #                     st.session_state.fetched_emails = response.json().get("emails", [])
# #                 elif response.status_code == 400:
# #                     st.warning("⚠️ Gmail is not connected.")
# #                     connect_url = f"{API_BASE_URL}/gmail/connect-gmail-dev?email={st.session_state.email}"
# #                     st.markdown(f"[🔗 Connect Gmail]({connect_url})")
# #                 else:
# #                     st.error("❌ Something went wrong while fetching emails.")
# #             except httpx.ReadTimeout:
# #                 st.error("⏱️ Timeout while fetching emails.")

# #         # 📬 Display Emails in Table
# #         if st.session_state.fetched_emails:
# #             for email in st.session_state.fetched_emails:
# #                 col1, col2 = st.columns([0.75, 0.25])

# #                 with col1:
# #                     st.markdown(f"""
# #                     **Subject:** {email['subject']}  
# #                     **From:** {email['from']}  
# #                     **Label:** `{email['label']}`  
# #                     [📧 View in Gmail](https://mail.google.com/mail/u/0/#inbox/{email['id']})
# #                     """)

# #                     if email["id"] in st.session_state.email_summaries:
# #                         st.markdown(f"📝 **Summary:** {st.session_state.email_summaries[email['id']]}")

# #                 with col2:
# #                     if st.button("🧠 Summarize", key=f"summarize_{email['id']}"):
# #                         sres = httpx.post(
# #                             f"{API_BASE_URL}/email_router/summarize",
# #                             params={"email_id": email["id"]},
# #                             headers={"Authorization": f"Bearer {st.session_state.token}"}
# #                         )
# #                         if sres.status_code == 200:
# #                             summary = sres.json()["summary"]
# #                             st.session_state.email_summaries[email["id"]] = summary
# #                             st.rerun()
# #                         else:
# #                             st.error("❌ Failed to summarize this email.")

# def chatbot_page():
#     st.subheader("💬 Chat Interface")
#     tabs = st.tabs(["Text Chat", "Chat with PDF", "Chat with Audio", "Email Assistant"])

#     # Show previous chat messages
#     for role, msg in st.session_state.chat_history:
#         st.markdown(f"**{role.capitalize()}**: {msg}")

#     # ----------------------------- Text Chat Tab -----------------------------
#     with tabs[0]:
#         with st.form("text_chat_form"):
#             user_input = st.text_input("You:", key="chat_input_text")
#             send_text = st.form_submit_button("Send (Text Chat)")

#         if send_text and user_input.strip():
#             response = httpx.post(
#                 f"{API_BASE_URL}/chat/query",
#                 json={"question": user_input.strip(), "session_id": f"normal_{st.session_state.email}"}
#             )
#             if response.status_code == 200:
#                 answer = response.json().get("answer", "No response.")
#                 st.session_state.chat_history.append(("user", user_input))
#                 st.session_state.chat_history.append(("bot", answer))
#                 st.rerun()
#             else:
#                 st.error("Text chat failed.")

#     # ----------------------------- Chat with PDF Tab -----------------------------
#     with tabs[1]:
#         with st.form("pdf_chat_form"):
#             uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
#             pdf_question = st.text_input("Ask a question based on the PDF:")
#             send_pdf = st.form_submit_button("Send (PDF)")

#         if send_pdf and uploaded_pdf and pdf_question.strip():
#             files = {"file": (uploaded_pdf.name, uploaded_pdf, "application/pdf")}
#             data = {"question": pdf_question.strip()}
#             response = httpx.post(f"{API_BASE_URL}/chat/pdf-query", data=data, files=files)
#             if response.status_code == 200:
#                 answer = response.json().get("answer", "No response.")
#                 st.session_state.chat_history.append(("user", f"[PDF Q] {pdf_question}"))
#                 st.session_state.chat_history.append(("bot", answer))
#                 st.rerun()
#             else:
#                 st.error("PDF chat failed.")

#     # ----------------------------- Chat with Audio Tab -----------------------------
#     with tabs[2]:
#         uploaded_audio = st.file_uploader("Upload audio file", type=["mp3", "wav", "m4a"])
#         if uploaded_audio and st.button("Send (Audio)", key="send_audio"):
#             files = {"file": (uploaded_audio.name, uploaded_audio, "audio/mpeg")}
#             response = httpx.post(
#                 f"{API_BASE_URL}/chat/audio-query",
#                 params={"question": "Transcribe and respond to this audio"},
#                 files=files
#             )
#             if response.status_code == 200:
#                 answer = response.json().get("answer", "No response.")
#                 st.session_state.chat_history.append(("user", "[Audio Uploaded]"))
#                 st.session_state.chat_history.append(("bot", answer))
#                 st.rerun()
#             else:
#                 st.error("Audio chat failed.")

#     # ----------------------------- Email Assistant Tab -----------------------------
#     with tabs[3]:
#         st.info("📬 Email Assistant - Smart assistant for your Gmail")

#         if "fetched_emails" not in st.session_state:
#             st.session_state.fetched_emails = []
#         if "email_summaries" not in st.session_state:
#             st.session_state.email_summaries = {}

#         # 🔄 Fetch Emails
#         if st.button("🔄 Fetch Emails"):
#             try:
#                 response = httpx.post(
#                     f"{API_BASE_URL}/email_router/list",
#                     headers={"Authorization": f"Bearer {st.session_state.token}"},
#                     timeout=30
#                 )
#                 if response.status_code == 200:
#                     st.success("✅ Fetched important emails.")
#                     st.session_state.fetched_emails = response.json().get("emails", [])
#                 elif response.status_code == 400:
#                     st.warning("⚠️ Gmail is not connected.")
#                     connect_url = f"{API_BASE_URL}/gmail/connect-gmail-dev?email={st.session_state.email}"
#                     st.markdown(f"[🔗 Connect Gmail]({connect_url})")
#                 else:
#                     st.error("❌ Error fetching emails.")
#             except httpx.ReadTimeout:
#                 st.error("⏱️ Timeout while fetching emails.")

#         # 📦 Embed My Emails
#         if st.button("📦 Embed My Emails"):
#             res = httpx.post(
#                 f"{API_BASE_URL}/email_router/embed",
#                 headers={"Authorization": f"Bearer {st.session_state.token}"}
#             )
#             if res.status_code == 200:
#                 st.success("✅ Emails embedded in vector store.")
#             else:
#                 st.error("❌ Failed to embed emails.")

#         # 🔍 Ask About Emails
#         st.markdown("### 🔍 Ask about your emails")
#         email_query = st.text_input("Ask (e.g. 'Do I have any meetings today?'):")

#         if st.button("🧠 Search Emails"):
#             if email_query.strip():
#                 res = httpx.post(
#                     f"{API_BASE_URL}/email_router/search-emails",
#                     params={"query": email_query.strip()},
#                     headers={"Authorization": f"Bearer {st.session_state.token}"}
#                 )
#                 if res.status_code == 200:
#                     results = res.json().get("results", [])
#                     if not results:
#                         st.info("🔍 No similar emails found.")
#                     for result in results:
#                         st.markdown(f"""
#                             📝 **Summary:** {result['summary']}  
#                             🔗 [📧 View Email]({result['gmail_link']})
#                         """)
#                 else:
#                     st.error("❌ Failed to search emails.")
#             else:
#                 st.warning("Please enter a question.")

#         # 📬 Display Email Table
#         if st.session_state.fetched_emails:
#             st.divider()
#             st.markdown("### 📥 Fetched Emails")
#             for email in st.session_state.fetched_emails:
#                 col1, col2 = st.columns([0.75, 0.25])

#                 with col1:
#                     st.markdown(f"""
#                     **Subject:** {email['subject']}  
#                     **From:** {email['from']}  
#                     **Label:** `{email['label']}`  
#                     🔗 [📧 Open in Gmail](https://mail.google.com/mail/u/0/#inbox/{email['id']})
#                     """)
#                     if email["id"] in st.session_state.email_summaries:
#                         st.markdown(f"📝 **Summary:** {st.session_state.email_summaries[email['id']]}")

#                 with col2:
#                     if st.button("🧠 Summarize", key=f"summarize_{email['id']}"):
#                         sres = httpx.post(
#                             f"{API_BASE_URL}/email_router/summarize",
#                             params={"email_id": email["id"]},
#                             headers={"Authorization": f"Bearer {st.session_state.token}"}
#                         )
#                         if sres.status_code == 200:
#                             summary = sres.json()["summary"]
#                             st.session_state.email_summaries[email["id"]] = summary
#                             st.rerun()
#                         else:
#                             st.error("❌ Failed to summarize email.")

# if st.session_state.logged_in:
#     chatbot_page()
# else:
#     login_signup_page()

