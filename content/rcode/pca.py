import os
import streamlit as st
import requests
from pathlib import Path
from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("📉 PCA (Principal Component Analysis)")

FASTAPI_PCA = os.getenv("FASTAPI_PCA", "http://design-pathway-backend:8000/api/pca/")

# ----------------- 업로드된 CSV 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to page setup or Upload tab first.")
    csv_files = []
else:
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_dir.mkdir(parents=True, exist_ok=True)

    csv_paths = sorted([p for p in csv_dir.glob("*.csv")])

    if not csv_paths:
        st.warning("⚠️ No CSV files found in the workspace csv-files folder. Please upload a CSV file first in the Upload tab.")
        csv_files = []
    else:
        csv_files = [str(p) for p in csv_paths]

# ----------------- 메인 탭 -----------------
main_tab = st.tabs(["📉 PCA Plot"])[0]

with main_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # Configure
    with configure_tab:
        width_pca = st.number_input("Plot Width", value=8.0, step=0.5)
        height_pca = st.number_input("Plot Height", value=6.0, step=0.5)
        pointshape_pca = st.number_input("Point Shape", value=16, step=1)
        pointsize_pca = st.number_input("Point Size", value=3.5, step=0.5)
        text_size_pca = st.number_input("Label Text Size", value=4.0, step=0.5)

    # Run
    with run_tab:
        if csv_files:
            # 자동으로 첫 번째 CSV 파일 사용
            csv_path = str(Path(csv_files[0]))
            st.info(f"📂 CSV Path: {csv_path}")

            output_svg = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_PCA.svg")
            )

            if st.button("Run PCA via FastAPI"):
                with st.spinner("Running PCA via FastAPI..."):
                    payload = {
                        "csv_path": csv_path,
                        "width": width_pca,
                        "height": height_pca,
                        "pointshape": pointshape_pca,
                        "pointsize": pointsize_pca,
                        "text_size": text_size_pca
                    }
                    try:
                        response = requests.post(FASTAPI_PCA, json=payload)
                        if response.status_code == 200:
                            with open(output_svg, "wb") as f:
                                f.write(response.content)
                            st.success("✅ PCA plot generated successfully")
                        else:
                            st.error(f"❌ PCA generation failed: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Request to FastAPI failed: {e}")
        else:
            st.warning("⚠️ Please upload a CSV file first in the Upload tab.")

    # Result
    with result_tab:
        if csv_files:
            output_svg_pca = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_PCA.svg")
            )
            if output_svg_pca.exists():
                st.image(str(output_svg_pca), caption="PCA Plot", width=700)

    # Download
    with download_tab:
        if csv_files:
            output_svg_pca = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_PCA.svg")
            )
            if output_svg_pca.exists():
                with open(output_svg_pca, "rb") as f:
                    st.download_button(
                        label="Download PCA SVG",
                        data=f,
                        file_name=output_svg_pca.name,
                        mime="image/svg+xml"
                    )