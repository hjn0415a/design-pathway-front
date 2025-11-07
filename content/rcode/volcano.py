import os
import requests
import streamlit as st
from pathlib import Path
from src.common.common import page_setup

# ----------------- 기본 설정 -----------------
params = page_setup()
st.title("Volcano / Enhanced Volcano Plot Dashboard")

FASTAPI_VOLCANO = os.getenv("FASTAPI_VOLCANO", "http://fastapi:8000/api/volcano/")

# ----------------- 업로드된 CSV 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to page setup or Upload tab first.")
    csv_files = []
else:
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_dir.mkdir(parents=True, exist_ok=True)

    csv_paths = sorted([p for p in csv_dir.glob("*.csv")])
    if not csv_paths:
        st.warning("⚠️ No CSV files found in workspace/csv-files. Please upload CSV first.")
        csv_files = []
    else:
        csv_files = [str(p) for p in csv_paths]

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

    with run_tab:
        if csv_files:
            selected_csv = st.selectbox("Select CSV file:", [Path(f).name for f in csv_files])
            csv_path = str(Path(st.session_state.workspace, "csv-files", selected_csv))
            output_svg_volcano = Path(st.session_state.workspace, selected_csv.replace(".csv", "_volcano.svg"))

            st.info(f"📂 CSV Path: {csv_path}")

            if st.button("Run Volcano Plot"):
                with st.spinner("Running Volcano Plot via FastAPI..."):
                    payload = {
                        "csv_path": csv_path,
                        "fc_cutoff": fc_cutoff,
                        "pval_cutoff": pval_cutoff,
                        "plot_type": "volcano"
                    }

                    try:
                        response = requests.post(FASTAPI_VOLCANO, data=payload)
                        if response.status_code == 200:
                            with open(output_svg_volcano, "wb") as f:
                                f.write(response.content)
                            st.success("✅ Volcano Plot generated successfully!")
                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")

    with result_tab:
        if csv_files:
            output_svg_volcano = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_volcano.svg")
            )
            if output_svg_volcano.exists():
                st.image(str(output_svg_volcano), caption="Volcano Plot", width=700)

    with download_tab:
        if csv_files:
            output_svg_volcano = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_volcano.svg")
            )
            if output_svg_volcano.exists():
                with open(output_svg_volcano, "rb") as f:
                    st.download_button(
                        label="Download Volcano SVG",
                        data=f,
                        file_name=output_svg_volcano.name,
                        mime="image/svg+xml"
                    )

# ----------------- EnhancedVolcano Plot -----------------
with enhanced_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    with configure_tab:
        fc_cutoff = st.number_input("Fold Change Cutoff (log2)", value=1.0, key="enhanced_fc")
        pval_cutoff = st.number_input("P-value Cutoff", value=0.05, format="%.4f", key="enhanced_pval")

    with run_tab:
        if csv_files:
            selected_csv = st.selectbox("Select CSV file:", [Path(f).name for f in csv_files], key="enhanced_select")
            csv_path = str(Path(st.session_state.workspace, "csv-files", selected_csv))
            output_svg_enhanced = Path(st.session_state.workspace, selected_csv.replace(".csv", "_enhanced_volcano.svg"))

            st.info(f"📂 CSV Path: {csv_path}")

            if st.button("Run EnhancedVolcano Plot"):
                with st.spinner("Running EnhancedVolcano via FastAPI..."):
                    payload = {
                        "csv_path": csv_path,
                        "fc_cutoff": fc_cutoff,
                        "pval_cutoff": pval_cutoff,
                        "plot_type": "enhanced"
                    }

                    try:
                        response = requests.post(FASTAPI_VOLCANO, data=payload)
                        if response.status_code == 200:
                            with open(output_svg_enhanced, "wb") as f:
                                f.write(response.content)
                            st.success("✅ EnhancedVolcano Plot generated successfully!")
                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")

    with result_tab:
        if csv_files:
            output_svg_enhanced = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_enhanced_volcano.svg")
            )
            if output_svg_enhanced.exists():
                st.image(str(output_svg_enhanced), caption="EnhancedVolcano Plot", width=700)

    with download_tab:
        if csv_files:
            output_svg_enhanced = Path(
                st.session_state.workspace,
                Path(csv_files[0]).name.replace(".csv", "_enhanced_volcano.svg")
            )
            if output_svg_enhanced.exists():
                with open(output_svg_enhanced, "rb") as f:
                    st.download_button(
                        label="Download EnhancedVolcano SVG",
                        data=f,
                        file_name=output_svg_enhanced.name,
                        mime="image/svg+xml"
                    )