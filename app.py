import streamlit as st
import json
import requests

# --- CONFIG ---
st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")

emails = {"id": 1, "sender": "alice@example.com", "subject": "Meeting Follow-Up", "content": "Hi, just checking in on the meeting notes."}

# --- UI HEADER ---
st.title("📧 AI Email Editing Tool")
st.write("Select an email record by ID and use AI to refine it.")

if not emails:
    st.warning("No emails found in your JSONL file.")
    st.stop()

# --- ID NAVIGATION BAR ---
email_ids = emails.get('id')
selected_id = st.sidebar.selectbox("📂 Select Email ID", options=email_ids, index=0)

# Find the selected email
selected_email = emails
if not selected_email:
    st.error(f"No email found with ID {selected_id}.")
    st.stop()

# --- DISPLAY SELECTED EMAIL ---
st.markdown(f"### ✉️ Email ID: `{selected_id}`")
st.markdown(f"**From:** {selected_email.get('sender', '(unknown)')}")
st.markdown(f"**Subject:** {selected_email.get('subject', '(no subject)')}")

email_text = st.text_area(
    "Email Content",
    value=selected_email.get("content", ""),
    height=250,
    key=f"email_text_{selected_id}",
)