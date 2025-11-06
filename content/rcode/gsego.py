import os
import streamlit as st
import requests
import pandas as pd
import tempfile
import shutil
from pathlib import Path

from src.common.common import page_setup
params = page_setup()

st.title("🧬 GSEA Analysis")

# ✅ FastAPI endpoint (환경변수 우선)
FASTAPI_GSEGO = os.getenv("FASTAPI_GSEGO", "http://design-pathway-backend:8000/api/gsego")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["🧬 GSEA"])
with main_tabs[0]:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        workspace = st.session_state.workspace
        csv_dir = Path(workspace, "csv-files")
        gsea_out_dir = Path(workspace, "gsea-results")
        gsea_out_dir.mkdir(parents=True, exist_ok=True)

        st.markdown(f"📁 **Current workspace:** `{workspace}`")

        # CSV 파일 선택
        csv_files = list(csv_dir.glob("*.csv"))
        if not csv_files:
            st.warning("No CSV files found. Please upload a CSV file first.")
        else:
            selected_csv = st.selectbox("Select input CSV file", [f.name for f in csv_files])
            file_path = csv_dir / selected_csv

            # 파라미터 입력
            orgdb = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
            min_gs_size = st.number_input("Minimum gene set size (minGSSize)", value=10, step=1)
            max_gs_size = st.number_input("Maximum gene set size (maxGSSize)", value=500, step=10)
            pvalue_cutoff = st.number_input("P-value cutoff", value=0.05, step=0.01, format="%.2f")

            # 세션 상태에 저장
            st.session_state["gsea_params"] = {
                "file_path": str(file_path),
                "out_dir": str(gsea_out_dir),
                "orgdb": orgdb,
                "min_gs_size": min_gs_size,
                "max_gs_size": max_gs_size,
                "pvalue_cutoff": pvalue_cutoff,
            }

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run GSEA Analysis via FastAPI"):
            params = st.session_state.get("gsea_params")
            if not params:
                st.warning("Please configure parameters first.")
            else:
                with st.spinner("Running GSEA analysis on FastAPI server..."):
                    try:
                        response = requests.post(FASTAPI_GSEGO, json=params, timeout=600)
                        if response.status_code == 200:
                            result = response.json()
                            st.success(result.get("message", "✅ GSEA completed successfully!"))
                            if result.get("stdout"):
                                st.text_area("R Output Log", result["stdout"], height=300)
                        else:
                            st.error(f"❌ FastAPI request failed: {response.status_code}")
                            st.text_area("Error Details", response.text, height=300)
                    except requests.exceptions.RequestException as e:
                        st.error(f"🚨 Request failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        gsea_out_dir = Path(st.session_state.workspace, "gsea-results")
        ontologies = ["BP", "CC", "MF"]
        ontology_tabs = st.tabs(ontologies)

        for ont_tab, ont in zip(ontology_tabs, ontologies):
            with ont_tab:
                csv_file = gsea_out_dir / f"gse_{ont}.csv"
                st.markdown(f"**Results for {ont}:**")
                if csv_file.exists():
                    df = pd.read_csv(csv_file)
                    if df.empty:
                        st.info(f"No significant results found for {ont}.")
                    else:
                        st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.info(f"{csv_file.name} not found.")

    # ----------------- Download -----------------
    with download_tab:
        gsea_out_dir = Path(st.session_state.workspace, "gsea-results")
        if gsea_out_dir.exists() and any(gsea_out_dir.iterdir()):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "GSEA_results"), "zip", gsea_out_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download GSEA Results (ZIP)",
                        data=f,
                        file_name="GSEA_results.zip",
                        mime="application/zip",
                    )
        else:
            st.info("No GSEA results available for download.")