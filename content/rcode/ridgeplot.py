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
# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 Ridgeplot (GSEA)"])
ridge_tab = main_tabs[0]

with ridge_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        analysis_info_path = Path(st.session_state.workspace) / "csv-files" / "output" / "analysis_info.csv"
        method_options = []
        selected_method = None

        if analysis_info_path.exists():
            try:
                info_df = pd.read_csv(analysis_info_path)
                # 'analysis_type' 컬럼에서 wald, LRT 추출
                if "analysis_type" in info_df.columns:
                    method_options = info_df["analysis_type"].dropna().unique().tolist()
                else:
                    st.warning("analysis_info.csv에 'analysis_type' 컬럼이 없습니다.")
            except Exception as e:
                st.warning(f"analysis_info.csv를 읽는 중 오류: {e}")
        else:
            st.warning("analysis_info.csv 파일이 존재하지 않습니다.")

        if method_options:
            selected_method = st.selectbox("분석 방법 선택", method_options)
        else:
            st.warning("분석 방법을 찾을 수 없습니다. DESeq2 분석을 먼저 실행해주세요.")    
        workspace = Path(st.session_state.workspace)
        gseaplot_dir = workspace / "csv-files" / "output" / selected_method/"gsego"
        ridge_dir = gseaplot_dir/"ridgeplot"

        width = st.number_input("Plot width", value=10.0, step=0.5)
        height = st.number_input("Plot height", value=8.0, step=0.5)

        st.session_state["ridgeplot_params"] = {
            "input_file": str(gseaplot_dir),
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