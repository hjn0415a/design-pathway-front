import os
import streamlit as st
import requests
import pandas as pd
import tempfile
import shutil
from pathlib import Path

from frontend.src.common.common import page_setup
params = page_setup()

st.title("🧬 DEG Analysis")

FASTAPI_URL = os.getenv("FASTAPI_DEG", "http://localhost:8000/run_deg")

# ----------------- 업로드 CSV 확인 -----------------
if hasattr(st.session_state, "uploaded_csv_files") and st.session_state.uploaded_csv_files:
    csv_files = st.session_state.uploaded_csv_files
else:
    st.warning("⚠️ Please upload a CSV file first in the Upload tab.")
    csv_files = []

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["🧬 DEG Filtering"])
deg_tab = main_tabs[0]

with deg_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        if csv_files:
            selected_csv = st.selectbox("Select CSV file", [Path(f).name for f in csv_files])
            csv_path = Path(st.session_state.workspace, "csv-files", selected_csv)
            result_dir = Path(st.session_state.workspace, "Deg")
            result_dir.mkdir(parents=True, exist_ok=True)
        else:
            csv_path = None
            result_dir = None

        fc_input = st.text_input("FC thresholds (comma-separated)", "1.5,2")
        pval_input = st.text_input("P-value thresholds (comma-separated)", "0.05,0.01")

        st.session_state["deg_params"] = {
            "csv_path": str(csv_path) if csv_path else "",
            "fc_input": fc_input,
            "pval_input": pval_input
        }

    # ----------------- Run -----------------
    with run_tab:
        if csv_files and st.button("🚀 Run DEG Filtering"):
            params = st.session_state.get("deg_params", {})
            with st.spinner("Running DEG filtering via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_URL, json=params)
                    if response.status_code == 200:
                        result = response.json()
                        st.success(result.get("message", "✅ DEG filtering completed!"))
                        if result.get("stdout"):
                            st.text(result["stdout"])
                    else:
                        st.error(f"❌ Failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"Request failed: {e}")
        elif not csv_files:
            st.info("Please upload a CSV file first before running.")

    # ----------------- Result -----------------
    with result_tab:
        if result_dir and result_dir.exists():
            combo_csv = result_dir / "combo_names.csv"
            if combo_csv.exists():
                combos = pd.read_csv(combo_csv)["combo"].tolist()
                if combos:
                    st.markdown("### 🧩 Filtered Results by Combination")
                    combo_tabs = st.tabs(combos)
                    for combo, tab in zip(combos, combo_tabs):
                        with tab:
                            file_path = result_dir / combo / "filtered_gene_list.csv"
                            if file_path.exists():
                                df = pd.read_csv(file_path)
                                st.markdown(f"**Genes: {len(df)}**")
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.warning(f"No results found for {combo}")
            else:
                st.info("No DEG results found yet.")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- Download -----------------
    with download_tab:
        if result_dir and (result_dir / "combo_names.csv").exists():
            combos = pd.read_csv(result_dir / "combo_names.csv")["combo"].tolist()
            if combos:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for combo in combos:
                        src = result_dir / combo
                        dst = Path(tmpdir, combo)
                        if src.exists():
                            shutil.copytree(src, dst)
                    zip_path = shutil.make_archive(os.path.join(tmpdir, "Deg_combos"), "zip", tmpdir)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download DEG Results (ZIP)",
                            data=f,
                            file_name="Deg_combos.zip",
                            mime="application/zip"
                        )
        else:
            st.info("No files available for download.")