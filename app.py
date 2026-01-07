import streamlit as st
import json
import requests
import pandas as pd
import os
from generate import GenerateEmail
import re
DEPLOYMENT_NAME = "gpt-4o-mini"
JUDGE_DEPLOYMENT_NAME = "gpt-4.1"
models=["gpt-4o-mini", "gpt-4.1"]
app_mode = st.sidebar.radio("Select Mode", ["Single Edit", "Batch Processing"])
selected_model = st.sidebar.selectbox("Select Model", options=models)
if "generator" not in st.session_state or st.session_state.current_model != selected_model:
    st.session_state.generator = GenerateEmail(model=selected_model, judge_model=JUDGE_DEPLOYMENT_NAME)
    st.session_state.current_model = selected_model
# --- CONFIG ---
st.set_page_config(page_title="AI Email Editor", page_icon="📧", layout="wide")
dataset_files = {
    "lengthen": "datasets/lengthen.jsonl",
    "shorten":  "datasets/shorten.jsonl",
    "tone":     "datasets/tone.jsonl",
    "acknowledgement": "datasets/acknowledgement.jsonl",
    "informational": "datasets/informational.jsonl",
    "request": "datasets/request.jsonl",
    "constraint": "datasets/constraint.jsonl",
    "status": "datasets/status.jsonl",
    "check_in": "datasets/check_in.jsonl"
}
selected_dataset = st.sidebar.selectbox("Select Dataset", options=list(dataset_files.keys()))
data_file_path = dataset_files[selected_dataset]
emails = []
with open(data_file_path, "r") as f:
    for line in f:
        emails.append(json.loads(line))
import re

def extract_score(text):
    match = re.search(r"score\s*[:=\-]?\s*([1-5])", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"\b([1-5])\b", text)
    if match:
        return int(match.group(1))
    return None

def calculate_metrics(original, generated):
    len_orig = len(original.split())
    len_gen = len(generated.split())
    diff = len_gen - len_orig
    pct_change = (diff / len_orig) * 100
    return len_orig, len_gen, pct_change
# --- UI HEADER ---
if app_mode == "Single Edit":
    st.title("📧 AI Email Editing Tool")
    st.write("Select an email record by ID and use AI to refine it.")
    if not emails:
        st.warning("No emails found in your JSONL file.")
        st.stop()
    # --- ID NAVIGATION BAR ---
    email_ids = [email["id"] for email in emails]
    selected_id = st.sidebar.selectbox("Select Email ID", options=email_ids)
    # Find the selected email
    selected_email = next((email for email in emails if email["id"] == selected_id), None)
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
    def show_evaluation(original, generated):
            faith_result = st.session_state.generator.evaluate(original, generated, "judge_faithfulness")
            st.write(f"Faithfulness: {faith_result}")
            comp_result = st.session_state.generator.evaluate(original, generated, "judge_completeness")
            st.write(f"Completeness: {comp_result}")
    if st.button("lengthen"):
        response = st.session_state.generator.generate("lengthen", text=email_text)
        st.write(response)
        show_evaluation(email_text,response)
    if st.button("shorten"):
        response = st.session_state.generator.generate("shorten", text=email_text)
        st.write(response)
        show_evaluation(email_text,response)
    tone=st.selectbox("Select Tone", options=["Formal", "Informal", "Friendly", "Professional"])
    if st.button("tone"):
        response = st.session_state.generator.generate("tone", text=email_text, tone=tone)
        st.write(response)
        show_evaluation(email_text, response)
elif app_mode == "Batch Processing":
    batch_action = st.selectbox("Action", ["shorten", "lengthen", "tone"])
    target_tone = None
    if batch_action == "tone":
        target_tone = st.selectbox("Select Tone", ["Formal", "Friendly", "Informal", "Professional"])
    if st.button("Run"):
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        subset = emails
        for i, email in enumerate(subset):
            original = email["content"]
            if batch_action == "tone":
                gen_text = st.session_state.generator.generate("tone", original, tone=target_tone)
            else:
                gen_text = st.session_state.generator.generate(batch_action, original)
            faith = st.session_state.generator.evaluate(original, gen_text, "judge_faithfulness")
            comp = st.session_state.generator.evaluate(original, gen_text, "judge_completeness")
            f_score = extract_score(faith)
            c_score = extract_score(comp)
            l_orig, l_gen, pct = calculate_metrics(original, gen_text)
            results.append({
                "ID": email["id"],
                "Action": batch_action,
                "Tone": target_tone if target_tone else "N/A",
                "Change %": pct,
                "Faithfulness": f_score,
                "Completeness": c_score,
                "Faith Reason": faith,
                "Comp Reason": comp
            })
            progress_bar.progress((i + 1) / len(subset))
        status.empty()
        if results:
            df = pd.DataFrame(results)
            avg_faith = df["Faithfulness"].mean()
            avg_comp = df["Completeness"].mean()
            st.metric("Average Faithfulness", f"{avg_faith}/5")
            st.metric("Average Completeness", f"{avg_comp}/5")
            st.metric("Average Change %", f"{df['Change %'].mean()}%")
            st.dataframe(df)