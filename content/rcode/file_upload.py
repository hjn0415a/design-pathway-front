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
    
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_paths = sorted([p for p in csv_dir.glob("*.csv")])
    csv_names = [p.name for p in csv_paths]
    if not csv_names:
        st.warning("No CSV files found in the directory.")
    else:
        selected_csv_name = st.selectbox("Select a CSV file", csv_names)
    
    if selected_csv_name is not None:
        st.session_state.csv_name = selected_csv_name
        selected_csv_path = csv_dir / selected_csv_name
        st.session_state.selected_csv_path = selected_csv_path
        st.write("Selected CSV path:", selected_csv_path)
        try:
            df = pd.read_csv(st.session_state.selected_csv_path)
            st.markdown("### Uploaded CSV Preview")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
    else:
        st.info("Please select a CSV file.")    
    
    st.subheader("1️⃣ 샘플 컬럼 선택")
    
    all_columns = df.columns.tolist()
    
    selected_samples = st.multiselect(
        "샘플로 사용할 컬럼을 선택하세요",
        options=all_columns,
        help="발현량이나 카운트 데이터가 있는 샘플 컬럼들을 선택하세요"
    )
    
    if selected_samples:
        st.divider()
        
        # 2단계: 그룹 할당
        st.subheader("2️⃣ 각 샘플에 그룹명 입력")
        
        group_assignments = {}
        
        # 컬럼을 3개씩 나눠서 표시
        cols = st.columns(3)
        
        for idx, sample in enumerate(selected_samples):
            col_idx = idx % 3
            with cols[col_idx]:
                group_name = st.text_input(
                    f"📌 {sample}",
                    key=f"group_{sample}",
                    placeholder="그룹명 입력 (예: Control, Treatment)"
                )
                group_assignments[sample] = group_name
        
        st.divider()


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



# csv_dir = Path(st.session_state.workspace, "csv-files")
# csv_paths = sorted([p for p in csv_dir.glob("*.csv")])
# csv_names = [p.name for p in csv_paths]

# # CSV가 없으면 경고
# if not csv_names:
#     st.warning("No CSV files found in the directory.")
# else:
#     selected_csv_name = st.selectbox("Select a CSV file", csv_names)
    
#     if selected_csv_name is not None:
#         st.session_state.csv_name = selected_csv_name
#         selected_csv_path = csv_dir / selected_csv_name
#         st.session_state.selected_csv_path = selected_csv_path
#         st.write("Selected CSV path:", selected_csv_path)
#         try:
#             df = pd.read_csv(st.session_state.selected_csv_path)
#             st.markdown("### Uploaded CSV Preview")
#             st.dataframe(df)
#         except Exception as e:
#             st.error(f"Error reading CSV: {str(e)}")
#     else:
#         st.info("Please select a CSV file.")    
