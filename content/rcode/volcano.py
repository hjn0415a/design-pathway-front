import os
import requests
import streamlit as st
from pathlib import Path
from src.common.common import page_setup
import pandas as pd

# ----------------- 기본 설정 -----------------
params = page_setup()
st.title("Volcano Plot")

FASTAPI_VOLCANO = os.getenv("FASTAPI_VOLCANO", "http://fastapi:8000/api/volcano/")
FASTAPI_ENHANCED = os.getenv("FASTAPI_ENHANCED", "http://fastapi:8000/api/volcano/enhanced/")


# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🌋 Volcano Plot", "💥 EnhancedVolcano Plot"])
volcano_tab, enhanced_tab = main_tabs

# ----------------- Volcano Plot -----------------
with volcano_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # Configure
    with configure_tab:
        fc_cutoff = st.number_input("Fold Change Cutoff (log2)", value=1.0, key="volcano_fc")
        pval_cutoff = st.number_input("P-value Cutoff", value=0.05, format="%.4f", key="volcano_pval")

        try:
            df = pd.read_csv(st.session_state.selected_csv_path)
            st.markdown("선택된 CSV 파일")
            st.dataframe(df)
        except Exception as e:
            st.warning(f"CSV파일을 file upload에서 먼저 선택해주세요." )

    # Run
    with run_tab:
        if "selected_csv_path" in st.session_state:
            csv_path = st.session_state.selected_csv_path
            st.info(f"📂 CSV Path: {csv_path}")
            volcano_dir = Path(st.session_state.workspace) / "volcano"
            volcano_dir.mkdir(parents=True, exist_ok=True)
            output_svg_volcano = Path(volcano_dir,Path(st.session_state.csv_name).name.replace(".csv", "_volcano.svg"))
            st.text(output_svg_volcano )
            if st.button("Run Volcano Plot"):
                with st.spinner("Running Volcano Plot via FastAPI..."):
                    payload = {
                        "csv_path": str(csv_path),
                        "fc_cutoff": fc_cutoff,
                        "pval_cutoff": pval_cutoff,
                    }
                    try:
                        response = requests.post(FASTAPI_VOLCANO, json=payload)
                        if response.status_code == 200:
                            with open(output_svg_volcano, "wb") as f:
                                f.write(response.content)
                            st.success("✅ Volcano Plot generated successfully!")
                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")

    # Result
    with result_tab:
        if "selected_csv_path" in st.session_state:
            if output_svg_volcano.exists():
                st.image(str(output_svg_volcano), caption="Volcano Plot", width=700)

    # Download
    with download_tab:
        if "selected_csv_path" in st.session_state:
            if output_svg_volcano.exists():
                with open(output_svg_volcano, "rb") as f:
                    st.download_button(
                        label="Download Volcano SVG",
                        data=f,
                        file_name=output_svg_volcano.name,
                        mime="image/svg+xml"
                    )

# ----------------- EnhancedVolcano Plot -----------------
# with enhanced_tab:
#     sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
#     configure_tab, run_tab, result_tab, download_tab = sub_tabs

#     with configure_tab:
#         fc_cutoff = st.number_input("Fold Change Cutoff (log2)", value=1.0, key="enhanced_fc")
#         pval_cutoff = st.number_input("P-value Cutoff", value=0.05, format="%.4f", key="enhanced_pval")

#     # Run
#     with run_tab:
#         if csv_files:
#             csv_path = str(Path(csv_files[0]))
#             output_svg_enhanced = Path(st.session_state.workspace, Path(csv_files[0]).name.replace(".csv", "_enhanced_volcano.svg"))
#             st.info(f"📂 CSV Path: {csv_path}")

#             if st.button("Run EnhancedVolcano Plot"):
#                 with st.spinner("Running EnhancedVolcano via FastAPI..."):
#                     payload = {
#                         "csv_path": csv_path,
#                         "fc_cutoff": fc_cutoff,
#                         "pval_cutoff": pval_cutoff,
#                     }
#                     try:
#                         response = requests.post(FASTAPI_ENHANCED, json=payload)
#                         if response.status_code == 200:
#                             with open(output_svg_enhanced, "wb") as f:
#                                 f.write(response.content)
#                             st.success("✅ EnhancedVolcano Plot generated successfully!")
#                         else:
#                             st.error(f"❌ Server error: {response.text}")
#                     except requests.exceptions.RequestException as e:
#                         st.error(f"Connection failed: {e}")

#     # Result
#     with result_tab:
#         if csv_files:
#             output_svg_enhanced = Path(st.session_state.workspace, Path(csv_files[0]).name.replace(".csv", "_enhanced_volcano.svg"))
#             if output_svg_enhanced.exists():
#                 st.image(str(output_svg_enhanced), caption="EnhancedVolcano Plot", width=700)

#     # Download
#     with download_tab:
#         if csv_files:
#             output_svg_enhanced = Path(st.session_state.workspace, Path(csv_files[0]).name.replace(".csv", "_enhanced_volcano.svg"))
#             if output_svg_enhanced.exists():
#                 with open(output_svg_enhanced, "rb") as f:
#                     st.download_button(
#                         label="Download EnhancedVolcano SVG",
#                         data=f,
#                         file_name=output_svg_enhanced.name,
#                         mime="image/svg+xml"
#                     )