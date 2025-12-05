import streamlit as st
from pathlib import Path
import requests
import pandas as pd
import shutil
from src.common.upload import csv_upload
from src.common.common import page_setup

params = page_setup()

st.markdown("## Upload CSV Files, DEseq2")

# Streamlit 저장 경로
csv_dir = Path(st.session_state.workspace, "csv-files")
csv_dir.mkdir(parents=True, exist_ok=True)

FASTAPI_UPLOAD_URL = "http://design-pathway-backend:8000/api/upload-csv"

# 1. CSV 파일 업로드
with st.form("csv-upload", clear_on_submit=True):
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    submitted = st.form_submit_button("Upload CSV")

# 2. 업로드된 파일 저장 및 미리보기
if submitted and uploaded_file:
    # 파일 포인터 초기화
    uploaded_file.seek(0)
    
    # Streamlit에 저장
    csv_upload.save_uploaded_csv([uploaded_file])
    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
    
    # 세션에 저장
    st.session_state.uploaded_csv = uploaded_file
    st.session_state.csv_name = uploaded_file.name

# 3. 업로드된 파일 미리보기 및 그룹 선택
if "uploaded_csv" in st.session_state:
    try:
        # 파일 포인터 초기화
        st.session_state.uploaded_csv.seek(0)
        df = pd.read_csv(st.session_state.uploaded_csv)
        st.markdown("### Uploaded CSV Preview")
        st.dataframe(df)

        # 두 번째 행에서 그룹 정보 추출 (pandas 활용)
        st.session_state.uploaded_csv.seek(0)
        df_group = pd.read_csv(st.session_state.uploaded_csv, header=None)
        if len(df_group) > 1:
            group_row = df_group.iloc[1].tolist()
            group_values = list(set(group_row))
            group_values = [g for g in group_values if g and g != '' and str(g).lower() != 'nan']

            st.markdown("#### 그룹 선택")
            control_group = st.selectbox("Control 그룹 선택", group_values, key="control_group")
            case_group = st.selectbox("Case 그룹 선택", group_values, key="case_group")
        else:
            st.warning("CSV 두 번째 행에 그룹 정보가 없습니다.")
            control_group = None
            case_group = None

        # 4. 분석 시작 버튼
        if control_group and case_group and st.button("🚀 Start DESeq2 Analysis"):
            with st.spinner("Running DESeq2 analysis via FastAPI..."):
                try:
                    st.session_state.uploaded_csv.seek(0)
                    payload = {
                        "control_group": control_group,
                        "case_group": case_group,
                        "target_dir": str(csv_dir)
                    }
                    response = requests.post(
                        FASTAPI_UPLOAD_URL,
                        files={"file": (st.session_state.csv_name, st.session_state.uploaded_csv.getvalue())},
                        data=payload,
                        stream=True
                    )
                    if response.status_code == 200:
                        if csv_dir.exists():
                            shutil.rmtree(csv_dir)
                        csv_dir.mkdir(parents=True, exist_ok=True)
                        download_path = csv_dir / "DEseq_result.zip"
                        download_path.write_bytes(response.content)
                        shutil.unpack_archive(str(download_path), extract_dir=str(csv_dir))
                        download_path.unlink()
                        st.success("✅ DESeq2 analysis completed successfully!")
                        result_files = list(csv_dir.glob("**/*"))
                        st.markdown("### Analysis Results")
                        for f in result_files:
                            if f.is_file():
                                st.write(f"📄 {f.name}")
                    else:
                        st.error(f"❌ Server error: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {e}")
    except Exception as e:
        st.error(f"Error reading CSV: {str(e)}")
else:
    st.info("Please upload a CSV file to begin.")
