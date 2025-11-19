import streamlit as st
from pathlib import Path
import requests
import pandas as pd
from src.common.upload import csv_upload

st.markdown("## Upload CSV Files")

# Streamlit 저장 경로
csv_dir = Path(st.session_state.workspace, "csv-files")
csv_dir.mkdir(parents=True, exist_ok=True)

FASTAPI_UPLOAD_URL = "http://design-pathway-backend:8000/api/upload-csv"

with st.form("csv-upload", clear_on_submit=True):
    files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    submitted = st.form_submit_button("Add CSV files")

if submitted and files:
    # Streamlit에도 저장
    csv_upload.save_uploaded_csv(files)

    # FastAPI로 전송
    for file in files:
        try:
            response = requests.post(
                FASTAPI_UPLOAD_URL,
                files={"file": (file.name, file.getbuffer())},
                data={"target_dir": str(csv_dir)}  # CSV 저장 경로 전송
            )
            if response.status_code == 200:
                st.success(f"{file.name} uploaded to FastAPI successfully!")
            else:
                st.error(f"Failed to upload {file.name}: {response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error while uploading {file.name}: {e}")

    # 첫 번째 CSV 미리보기
    try:
        df = pd.read_csv(files[0])
        st.markdown("### Uploaded CSV Preview")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading CSV: {str(e)}")