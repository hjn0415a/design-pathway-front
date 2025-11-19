import os
import streamlit as st
import pandas as pd
import requests
import tempfile
import shutil
from pathlib import Path
from src.common.common import page_setup

# ----------------- PAGE SETUP -----------------
params = page_setup()
st.title("GSEA Ridgeplot")

# ----------------- FastAPI URL -----------------
FASTAPI_RIDGEPLOT = os.getenv("FASTAPI_RIDGEPLOT", "http://design-pathway-backend:8000/api/ridgeplot")

# ----------------- Workspace 체크 -----------------
if "workspace" not in st.session_state:
    st.error("❌ Workspace not found. Please configure workspace before running Ridgeplot.")
    st.stop()

workspace = Path(st.session_state.workspace)

# CSV 파일이 저장된 폴더
csv_dir = workspace / "csv-files"
csv_dir.mkdir(parents=True, exist_ok=True)

# 업로드된 CSV 파일 목록
csv_paths = sorted(list(csv_dir.glob("*.csv")))

if not csv_paths:
    st.warning("⚠️ No CSV files found in the workspace csv-files folder. Please upload a CSV file first.")
    st.stop()

# CSV 전체 경로 리스트
csv_files = [str(p) for p in csv_paths]

# Ridgeplot 결과 폴더
ridge_dir = workspace / "Ridgeplot"
ridge_dir.mkdir(parents=True, exist_ok=True)


# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 Ridgeplot (GSEA)"])
ridge_tab = main_tabs[0]

with ridge_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        selected_csv = st.selectbox(
            "Select a CSV file:",
            [Path(f).name for f in csv_files]
        )

        # FastAPI에 넘길 절대 경로
        input_file = str(csv_dir / selected_csv)
        st.info(f"📂 Using CSV: {input_file}")

        width = st.number_input("Plot width", value=10.0, step=0.5)
        height = st.number_input("Plot height", value=8.0, step=0.5)

        st.session_state["ridgeplot_params"] = {
            "input_file": input_file,
            "output_dir": str(ridge_dir),
            "width": width,
            "height": height,
        }

    # ----------------- RUN -----------------
    with run_tab:
        if st.button("Run Ridgeplot GSEA"):
            params = st.session_state.get("ridgeplot_params", {})
            with st.spinner("Running R script via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_RIDGEPLOT, json=params, stream=True, timeout=600)
                    if response.status_code == 200:
                        # ZIP 파일 경로
                        download_path = ridge_dir / "ridgeplot_results.zip"
                        if ridge_dir.exists():
                            shutil.rmtree(ridge_dir)
                        ridge_dir.mkdir(parents=True, exist_ok=True)

                        # ZIP 저장
                        download_path.write_bytes(response.content)

                        # ZIP 풀기
                        shutil.unpack_archive(str(download_path), extract_dir=str(ridge_dir))

                        # ZIP 삭제
                        if download_path.exists():
                            download_path.unlink()

                        st.success("📦 Ridgeplot results unzipped successfully!")
                    else:
                        st.error(f"Failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # ----------------- RESULT -----------------
    with result_tab:
        if ridge_dir.exists():
            ontology_tabs = st.tabs(["BP", "CC", "MF"])
            for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
                with ont_tab:
                    st.subheader(f"Ontology: {ont}")
                    ont_svgs = sorted([f for f in os.listdir(ridge_dir) if f.endswith(".svg") and ont in f])
                    if ont_svgs:
                        for i in range(0, len(ont_svgs), 2):
                            svg_pair = ont_svgs[i:i+2]
                            cols = st.columns(len(svg_pair))
                            for col, svg_file in zip(cols, svg_pair):
                                with col:
                                    st.markdown(f"**{svg_file}**")
                                    st.image(ridge_dir / svg_file, width=800)
                    else:
                        st.info(f"No {ont} ridgeplots found.")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- DOWNLOAD -----------------
    with download_tab:
        if ridge_dir.exists() and os.listdir(ridge_dir):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(Path(tmpdir, "ridgeplot_results"), "zip", ridge_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Ridgeplot Results (ZIP)",
                        data=f,
                        file_name="ridgeplot_results.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No files to download.")