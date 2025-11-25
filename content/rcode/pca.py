import os
import streamlit as st
import requests
from pathlib import Path
from src.common.common import page_setup
import pandas as pd

# 기본 설정
params = page_setup()
st.title("📉 PCA (Principal Component Analysis)")

FASTAPI_PCA = os.getenv("FASTAPI_PCA", "http://design-pathway-backend:8000/api/pca/")


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
        try:
            df = pd.read_csv(st.session_state.selected_csv_path)
            st.markdown("선택된 CSV 파일")
            st.dataframe(df)
        except Exception as e:
            st.warning(f"CSV파일을 file upload에서 먼저 선택해주세요." )
    # Run
    with run_tab:
        if "selected_csv_path" in st.session_state:
            # 자동으로 첫 번째 CSV 파일 사용
            csv_path = st.session_state.selected_csv_path
            st.info(f"📂 CSV Path: {csv_path}")
            pca_dir = Path(st.session_state.workspace) / "pca"
            pca_dir.mkdir(parents=True, exist_ok=True)
            output_svg_pca = Path(pca_dir,Path(st.session_state.selected_csv_path).name.replace(".csv", "_PCA.svg"))
            if st.button("Run PCA"):
                with st.spinner("Running PCA"):
                    payload = {
                        "csv_path": str(csv_path),
                        "width": width_pca,
                        "height": height_pca,
                        "pointshape": pointshape_pca,
                        "pointsize": pointsize_pca,
                        "text_size": text_size_pca
                    }
                    try:
                        response = requests.post(FASTAPI_PCA, json=payload)
                        if response.status_code == 200:
                            with open(output_svg_pca, "wb") as f:
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
        if "selected_csv_path" in st.session_state:
            if output_svg_pca.exists():
                st.image(str(output_svg_pca), caption="PCA Plot", width=700)

    # Download
    with download_tab:
        try:
            if output_svg_pca.exists():
                with open(output_svg_pca, "rb") as f:
                    st.download_button(
                        label="Download PCA SVG",
                        data=f,
                        file_name=output_svg_pca.name,
                        mime="image/svg+xml"
                    )

        except NameError:
            st.warning("⚠️ heatmap을 먼저 실행해주세요.")