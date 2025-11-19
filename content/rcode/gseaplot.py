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
st.title("📊 Gseaplot")

# ----------------- FastAPI URLs -----------------
FASTAPI_TOTAL_URL = os.getenv(
    "FASTAPI_GSEAPLOT_TOTAL",
    "http://design-pathway-backend:8000/api/gseaplot/total",
)
FASTAPI_TERM_URL = os.getenv(
    "FASTAPI_GSEAPLOT_TERM",
    "http://design-pathway-backend:8000/api/gseaplot/term",
)

# ----------------- Workspace 체크 -----------------
if "workspace" not in st.session_state:
    st.error("❌ Workspace not found. Please configure workspace before running GSEA Plot.")
    st.stop()

gseaplot_dir = Path(st.session_state.workspace, "GSEA_GO", "out")
gseaplot_dir.mkdir(parents=True, exist_ok=True)

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 GSEA Plot (Total)", "📊 GSEA Plot (Term)"])
total_tab, term_tab = main_tabs

# ================================================================
# 🧩 TOTAL GSEA PLOT TAB
# ================================================================
with total_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        result_dir = gseaplot_dir / "gseaplot_total"
        result_dir.mkdir(parents=True, exist_ok=True)

        topN = st.number_input("Top N terms to plot", value=10, step=1, min_value=1)
        width = st.number_input("Plot width", value=12.0, step=0.5)
        height = st.number_input("Plot height", value=8.0, step=0.5)

        st.session_state["total_params"] = {
            "input_dir": str(gseaplot_dir),
            "output_dir": str(result_dir),
            "topN": topN,
            "width": width,
            "height": height,
        }

    # ----------------- RUN -----------------
    with run_tab:
        if st.button("🚀 Run GSEA Total Plot"):
            params = st.session_state.get("total_params", {})
            with st.spinner("Running GSEA total plot via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_TOTAL_URL, data=params, stream=True)

                    if response.status_code == 200:
                        # ZIP 파일 경로 생성
                        download_path = result_dir / "gseaplot_total.zip"
                        if result_dir.exists():
                            shutil.rmtree(result_dir)
                        result_dir.mkdir(parents=True, exist_ok=True)

                        # ZIP 저장
                        download_path.write_bytes(response.content)
                        shutil.unpack_archive(str(download_path), extract_dir=str(result_dir))

                        # ZIP 삭제
                        if download_path.exists():
                            download_path.unlink()

                        st.success("📦 Unzipped GSEA total results successfully!")
                    else:
                        st.error(f"❌ Server error: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection failed: {e}")

    # ----------------- RESULT -----------------
    with result_tab:
        if result_dir.exists():
            ontologies = ["BP", "CC", "MF"]
            ontology_tabs = st.tabs(ontologies)

            for ont_tab, ont in zip(ontology_tabs, ontologies):
                with ont_tab:
                    st.markdown(f"### {ont} Ontology Results")

                    # 해당 ontology 관련 SVG 파일 찾기
                    svgs = [f for f in os.listdir(result_dir) if f.endswith(".svg") and f"_{ont}_" in f]
                
                    if svgs:
                        for svg in svgs:
                            st.markdown(f"**{svg}**")
                            st.image(os.path.join(result_dir, svg), width=850)
                    else:
                        st.info(f"No SVG plots found for {ont}")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- DOWNLOAD -----------------
    with download_tab:
        if result_dir.exists() and any(result_dir.iterdir()):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "gseaplot_total_results"), "zip", result_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download GSEA Total Results (ZIP)",
                        data=f,
                        file_name="gseaplot_total_results.zip",
                        mime="application/zip",
                    )
        else:
            st.info("No files to download.")

# ================================================================
# 🧩 TERM GSEA PLOT TAB
# ================================================================
with term_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        result_dir = gseaplot_dir / "gseaplot_term"
        result_dir.mkdir(parents=True, exist_ok=True)

        ont = st.selectbox("Select ontology", ["BP", "CC", "MF"], index=0)
        csv_files = {"BP": "gse_BP.csv", "CC": "gse_CC.csv", "MF": "gse_MF.csv"}
        csv_path = gseaplot_dir / csv_files[ont]

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            if not df.empty:
                st.dataframe(df)
                idx = st.number_input(
                    "Row index (1-based) for GSEA Term Plot",
                    min_value=1,
                    max_value=len(df),
                    value=1,
                    step=1,
                )
                st.session_state["term_params"] = {
                    "input_dir": str(gseaplot_dir),
                    "output_dir": str(result_dir),
                    "ont": ont,
                    "idx": idx,
                    "width": 8,
                    "height": 8,
                }
            else:
                st.warning(f"{csv_files[ont]} is empty.")
        else:
            st.warning(f"{csv_files[ont]} not found in {gseaplot_dir}.")

    # ----------------- RUN -----------------
    with run_tab:
        if st.button("🚀 Run GSEA Term Plot"):
            params = st.session_state.get("term_params", {})
            with st.spinner("Running GSEA term plot via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_TERM_URL, data=params, stream=True)

                    if response.status_code == 200:
                        # ZIP 파일 경로 생성
                        download_path = result_dir / "gseaplot_term.zip"
                        if result_dir.exists():
                            shutil.rmtree(result_dir)
                        result_dir.mkdir(parents=True, exist_ok=True)

                        # ZIP 저장
                        download_path.write_bytes(response.content)
                        shutil.unpack_archive(str(download_path), extract_dir=str(result_dir))

                        # ZIP 삭제
                        if download_path.exists():
                            download_path.unlink()

                        st.success("📦 Unzipped GSEA term results successfully!")
                    else:
                        st.error(f"❌ Server error: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection failed: {e}")

    # ----------------- RESULT -----------------
    with result_tab:
        if result_dir.exists():
            st.markdown(f"### {ont} Ontology Results")

            # CSV 파일
            csv_files = {"BP": "gse_BP.csv", "CC": "gse_CC.csv", "MF": "gse_MF.csv"}
            csv_file = gseaplot_dir / csv_files[ont]

            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    if df.empty:
                        st.info("No enriched terms found for this ontology.")
                    else:
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Failed to read CSV file: {e}")
            else:
                st.warning(f"No CSV found for {ont}")

            # SVG 이미지
            svgs = [f for f in os.listdir(result_dir) if f.endswith(".svg") and f"_{ont}_" in f]
            if svgs:
                for svg in svgs:
                    st.markdown(f"**{svg}**")
                    st.image(os.path.join(result_dir, svg), width=850)
            else:
                st.info(f"No SVG plots found for {ont}")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- DOWNLOAD -----------------
    with download_tab:
        if result_dir.exists() and any(result_dir.iterdir()):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "gseaplot_term_results"), "zip", result_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download GSEA Term Results (ZIP)",
                        data=f,
                        file_name="gseaplot_term_results.zip",
                        mime="application/zip",
                    )
        else:
            st.info("No files to download.")