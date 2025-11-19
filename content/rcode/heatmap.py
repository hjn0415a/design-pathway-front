import os
import requests
import streamlit as st
from pathlib import Path

from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("Heatmap")

FASTAPI_HEATMAP = os.getenv("FASTAPI_HEATMAP", "http://design-pathway-backend:8000/api/heatmap/")

# ----------------- 업로드된 CSV 확인 (수정본) -----------------
# workspace가 초기화되어 있는지 안전하게 확인
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to page setup or Upload tab first.")
    csv_files = []
else:
    csv_dir = Path(st.session_state.workspace, "csv-files")
    # 업로드 페이지에서 이미 만든 폴더지만 보험 차원에서 한 번 더 생성(부모도 포함)
    csv_dir.mkdir(parents=True, exist_ok=True)

    # csv파일 전체 경로 목록을 문자열 리스트로 생성
    csv_paths = sorted([p for p in csv_dir.glob("*.csv")])

    if not csv_paths:
        st.warning("⚠️ No CSV files found in the workspace csv-files folder. Please upload a CSV file first in the Upload tab.")
        csv_files = []
    else:
        # csv_files는 전체 경로 문자열(또는 Path 객체)의 리스트로 사용
        # (기존 코드가 Path(f).name 으로 파일명만 뽑아 쓰므로 호환됨)
        csv_files = [str(p) for p in csv_paths]

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

    # Run
    with run_tab:
        if csv_files:
            # 자동으로 첫 번째 CSV 파일 사용
            csv_path = str(Path(csv_files[0]))  # 이미 csv_files는 절대 경로 문자열 리스트
            st.info(f"📂 CSV Path: {csv_path}")

            output_svg_heatmap = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_heatmap.svg")
            )

            if st.button("Run Heatmap"):
                with st.spinner("Running R Heatmap analysis via FastAPI..."):
                    try:
                        payload = {
                            "csv_path": csv_path,  # FastAPI가 참조할 경로
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

    # Result
    with result_tab:
        if csv_files:
            output_svg_heatmap = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_heatmap.svg")
            )
            if output_svg_heatmap.exists():
                st.image(str(output_svg_heatmap), caption="Heatmap", width=700)

    # Download
    with download_tab:
        if csv_files:
            output_svg_heatmap = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_heatmap.svg")
            )
            if output_svg_heatmap.exists():
                with open(output_svg_heatmap, "rb") as f:
                    st.download_button(
                        label="Download Heatmap SVG",
                        data=f,
                        file_name=output_svg_heatmap.name,
                        mime="image/svg+xml"
                    )