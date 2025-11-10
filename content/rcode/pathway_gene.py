import os
import tempfile
import shutil
import streamlit as st
import requests
from pathlib import Path

from src.common.common import page_setup
params = page_setup()

st.title("Heatmaplike Functional Classification")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 GSEA Heatplot"])
with main_tabs[0]:

    # ----------------- Sub Tabs -----------------
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        workspace = st.session_state.workspace
        csv_dir = Path(workspace, "csv-files")
        edox_dir = Path(workspace, "gsea-results")  # RDS 파일 위치
        output_dir = Path(workspace, "gsea-results/heatplot")
        output_dir.mkdir(parents=True, exist_ok=True)

        st.markdown(f"📁 **Current workspace:** `{workspace}`")

        # 업로드된 CSV 선택
        csv_files = list(csv_dir.glob("*.csv"))
        if not csv_files:
            st.warning("No CSV files found. Please upload a CSV file first.")
        else:
            selected_csv = st.selectbox("Select input CSV file", [f.name for f in csv_files])
            csv_path = csv_dir / selected_csv

            # 사용자 입력 파라미터
            top_pathways = st.number_input("Max pathways to display", value=5, step=1, min_value=1)
            top_genes_per_pathway = st.number_input("Max genes per pathway", value=20, step=1, min_value=1)
            width = st.number_input("Plot width", value=12.0, step=0.5)
            height = st.number_input("Plot height", value=6.0, step=0.5)

            # 세션 상태에 저장
            st.session_state["heatplot_params"] = {
                "edox_dir": str(edox_dir),
                "csv_path": str(csv_path),
                "output_dir": str(output_dir),
                "top_pathways": top_pathways,
                "top_genes_per_pathway": top_genes_per_pathway,
                "width": width,
                "height": height
            }

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run Heatplot Generation"):
            params = st.session_state.get("heatplot_params", None)
            if not params:
                st.warning("Please configure parameters first.")
            else:
                try:
                    response = requests.post(
                        "http://localhost:8000/api/pathway_gene/",
                        json=params
                    )
                    if response.status_code == 200:
                        zip_path = Path(workspace, "heatplot_results.zip")
                        with open(zip_path, "wb") as f:
                            f.write(response.content)
                        st.success("Heatplot generation completed via FastAPI!")
                        st.download_button(
                            label="Download Heatplot Results (ZIP)",
                            data=open(zip_path, "rb"),
                            file_name="heatplot_results.zip",
                            mime="application/zip"
                        )
                    else:
                        st.error(f"Heatplot generation failed: {response.text}")
                except Exception as e:
                    st.error(f"Request to FastAPI failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        if output_dir.exists():
            ontology_tabs = st.tabs(["BP", "CC", "MF"])
            for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
                with ont_tab:
                    st.subheader(f"Ontology: {ont}")
                    ont_svgs = [f for f in os.listdir(output_dir) if f.endswith(".svg") and ont in f]
                    if ont_svgs:
                        for i in range(0, len(ont_svgs), 2):
                            svg_pair = ont_svgs[i:i+2]
                            cols = st.columns(len(svg_pair))
                            for col, svg_file in zip(cols, svg_pair):
                                with col:
                                    st.markdown(f"**{svg_file}**")
                                    st.image(os.path.join(output_dir, svg_file), width=950)
                    else:
                        st.info(f"No {ont} heatplots found.")
        else:
            st.info("Output directory does not exist.")

    # ----------------- Download -----------------
    with download_tab:
        if output_dir.exists() and any(output_dir.iterdir()):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "heatplot_results"), "zip", output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Heatplot Results (ZIP)",
                        data=f,
                        file_name="heatplot_results.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No files to download.")