import os
import streamlit as st
import requests
from frontend.src.common.common import page_setup
from pathlib import Path

params = page_setup()

st.title("📉 PCA (Principal Component Analysis)")

FASTAPI_URL = "http://localhost:8000/api/pca/run-pca"  # FastAPI endpoint

main_tab = st.tabs(["📉 PCA Plot"])[0]

# ----------------- 업로드 CSV 확인 -----------------
if hasattr(st.session_state, "uploaded_csv_files") and st.session_state.uploaded_csv_files:
    csv_files = st.session_state.uploaded_csv_files
else:
    st.warning("⚠️ Please upload a CSV file first in the Upload tab.")
    csv_files = []

with main_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        if csv_files:
            selected_csv = st.selectbox("Select CSV file for PCA", [Path(f).name for f in csv_files])
            csv_path_pca = Path(st.session_state.workspace, "csv-files", selected_csv)
            output_svg_pca = Path(st.session_state.workspace, selected_csv.replace(".csv", "_PCA.svg"))
        else:
            csv_path_pca = None
            output_svg_pca = None

        width_pca = st.number_input("Plot Width", value=8.0, step=0.5)
        height_pca = st.number_input("Plot Height", value=6.0, step=0.5)
        pointshape_pca = st.number_input("Point Shape", value=16, step=1)
        pointsize_pca = st.number_input("Point Size", value=3.5, step=0.5)
        text_size_pca = st.number_input("Label Text Size", value=4.0, step=0.5)

    # ----------------- Run -----------------
    with run_tab:
        if csv_files and st.button("Run PCA via FastAPI"):
            payload = {
                "csv_path": str(csv_path_pca),
                "output_svg": str(output_svg_pca),
                "width": width_pca,
                "height": height_pca,
                "pointshape": pointshape_pca,
                "pointsize": pointsize_pca,
                "text_size": text_size_pca
            }
            try:
                response = requests.post(FASTAPI_URL, json=payload)
                if response.status_code == 200:
                    with open(output_svg_pca, "wb") as f:
                        f.write(response.content)
                    st.success("✅ PCA plot generated successfully via FastAPI!")
                else:
                    st.error(f"❌ PCA generation failed: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Request to FastAPI failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        if output_svg_pca and output_svg_pca.exists():
            st.image(str(output_svg_pca), caption="PCA Plot", width=700)

    # ----------------- Download -----------------
    with download_tab:
        if output_svg_pca and output_svg_pca.exists():
            with open(output_svg_pca, "rb") as f:
                st.download_button(
                    label="Download PCA SVG",
                    data=f,
                    file_name=output_svg_pca.name,
                    mime="image/svg+xml"
                )