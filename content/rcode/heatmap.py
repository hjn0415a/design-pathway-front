import os
import requests
import streamlit as st
from pathlib import Path
import pandas as pd

from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("Heatmap")

FASTAPI_HEATMAP = os.getenv("FASTAPI_HEATMAP", "http://design-pathway-backend:8000/api/heatmap/")


# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🌡️ Heatmap"])
heatmap_tab = main_tabs[0]

with heatmap_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # Configure
    with configure_tab:
        width_heatmap = st.number_input("Plot Width", value=8.0, step=0.5)
        height_heatmap = st.number_input("Plot Height", value=10.0, step=0.5)
        top_n_genes = st.number_input("Top N genes (by p-value)", value=50, step=5)
        
        try:
            df = pd.read_csv(st.session_state.selected_csv_path)
            st.markdown("선택된 CSV 파일")
            st.dataframe(df)
        except Exception as e:
            st.warning(f"CSV파일을 file upload에서 먼저 선택해주세요." )

    # Run
    with run_tab:
            if "selected_csv_path" in st.session_state:
                csv_path = st.session_state.selected_csv_path# 이미 csv_files는 절대 경로 문자열 리스트
                st.info(f"📂 CSV Path: {csv_path}")
                heatmap_dir = Path(st.session_state.workspace) / "heatmap"
                heatmap_dir.mkdir(parents=True, exist_ok=True)
                output_svg_heatmap = Path(
                    heatmap_dir,
                    Path(st.session_state.csv_name).name.replace(".csv", "_heatmap.svg")
                )

                if st.button("Run Heatmap"):
                    with st.spinner("Running R Heatmap analysis"):
                        try:
                            payload = {
                                "csv_path": str(csv_path),  # FastAPI가 참조할 경로
                                "width": width_heatmap,
                                "height": height_heatmap,
                                "top_n_genes": top_n_genes
                            }
                            response = requests.post(FASTAPI_HEATMAP, data=payload)

                            if response.status_code == 200:
                                with open(output_svg_heatmap, "wb") as f_out:
                                    f_out.write(response.content)
                                st.success("✅ Heatmap generated successfully!")
                            else:
                                st.error(f"❌ Server error: {response.text}")

                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection failed: {e}")
                else:
                    st.info("Click 'Run Heatmap' to start the analysis.")

    # Result
    with result_tab:
         if "selected_csv_path" in st.session_state:
            if output_svg_heatmap.exists():
                st.image(str(output_svg_heatmap), caption="Heatmap", width=700)

    # Download
    with download_tab:
        try:
            if output_svg_heatmap.exists():
                with open(output_svg_heatmap, "rb") as f:
                    st.download_button(
                        label="Download Heatmap SVG",
                        data=f,
                        file_name=output_svg_heatmap.name,
                        mime="image/svg+xml"
                    )
        except NameError:
            st.warning("⚠️ heatmap을 먼저 실행해주세요.")
