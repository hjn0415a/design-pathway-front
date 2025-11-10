import os
import requests
import streamlit as st
from pathlib import Path
import pandas as pd
import tempfile
import shutil

from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("🧬 DEG Analysis")

# FastAPI 엔드포인트 (환경변수 or 기본값)
FASTAPI_DEG = os.getenv("FASTAPI_DEG", "http://design-pathway-backend:8000/api/deg/")

# ----------------- 업로드된 CSV 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to Upload tab first.")
    csv_files = []
else:
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_paths = sorted([p for p in csv_dir.glob("*.csv")])

    if not csv_paths:
        st.warning("⚠️ No CSV files found. Please upload a CSV file first.")
        csv_files = []
    else:
        csv_files = [str(p) for p in csv_paths]

# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 DEG Filtering"])
deg_tab = main_tabs[0]

with deg_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        if csv_files:
            selected_csv = st.selectbox(
                "Select a CSV file to analyze:",
                [Path(f).name for f in csv_files]
            )
            csv_path = str(Path(st.session_state.workspace, "csv-files", selected_csv))
            result_dir = Path(st.session_state.workspace, "Deg")
        else:
            csv_path = ""
            result_dir = None

        fc_input = st.text_input("Fold Change thresholds (comma-separated)", "1.5,2")
        pval_input = st.text_input("P-value thresholds (comma-separated)", "0.05,0.01")

        st.session_state["deg_params"] = {
            "csv_path": csv_path,
            "fc_input": fc_input,
            "pval_input": pval_input
        }

    # ----------------- Run -----------------
    with run_tab:
        if csv_files:
            selected_csv = Path(csv_path).name
            st.info(f"📂 CSV Path: {csv_path}")

            if st.button("🚀 Run DEG Filtering"):
                params = st.session_state.get("deg_params", {})
                st.info(params)
                with st.spinner("Running DEG filtering via FastAPI..."):
                    try:
                        # ✅ FastAPI의 Form(...) 구조에 맞게 data로 전송
                        response = requests.post(FASTAPI_DEG, data=params, stream=False)
                        
                        if response.status_code == 200:


                            download_path = Path(result_dir, "deg.zip")
                            download_path.parent.mkdir(parents=True, exist_ok=True)

                            # ✅ ZIP 파일 저장
                            download_path.write_bytes(response.content)

                            shutil.unpack_archive(str(download_path), extract_dir=str(result_dir))

                            st.success("📦 Unzipped results into workspace successfully!")


                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")
        else:
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