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

FASTAPI_DEG = os.getenv("FASTAPI_DEG", "http://design-pathway-backend:8000/api/deg/")

# ----------------- 업로드된 CSV 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to Upload tab first.")
    csv_files = []
else:
    pass



# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 DEG Filtering"])
deg_tab = main_tabs[0]

with deg_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
                # analysis_info.csv 경로
        analysis_info_path = Path(st.session_state.workspace) / "csv-files" / "output" / "analysis_info.csv"
        method_options = []
        selected_method = None

        if analysis_info_path.exists():
            try:
                info_df = pd.read_csv(analysis_info_path)
                # 'analysis_type' 컬럼에서 wald, LRT 추출
                if "analysis_type" in info_df.columns:
                    method_options = info_df["analysis_type"].dropna().unique().tolist()
                else:
                    st.warning("analysis_info.csv에 'analysis_type' 컬럼이 없습니다.")
            except Exception as e:
                st.warning(f"analysis_info.csv를 읽는 중 오류: {e}")
        else:
            st.warning("analysis_info.csv 파일이 존재하지 않습니다.")

        if method_options:
            selected_method = st.selectbox("분석 방법 선택", method_options)
            st.session_state.selected_method_pca = selected_method
        else:
            st.warning("분석 방법을 찾을 수 없습니다. DESeq2 분석을 먼저 실행해주세요.")
        fc_input = st.text_input("Fold Change thresholds (comma-separated)", "1.5,2")
        pval_input = st.text_input("P-value thresholds (comma-separated)", "0.05,0.01")
    # ----------------- Run -----------------

    with run_tab:
        workspace = Path(st.session_state.workspace)
        deg_dir = workspace / "csv-files" / "output" / selected_method/ "deg"
        if st.button("🚀 Run DEG Filtering"):
            with st.spinner("Running DEG filtering via FastAPI..."):
                try:
                    payload = {
                    "workspace": workspace,
                    "method": selected_method,
                    "fc_input": fc_input,
                    "pval_input": pval_input
                        }
                    response = requests.post(FASTAPI_DEG, data=payload, stream=False)

                    if response.status_code == 200:
                        download_path = deg_dir / "deg.zip"
                        if deg_dir.exists():
                            shutil.rmtree(deg_dir)
                        download_path.parent.mkdir(parents=True, exist_ok=True)

                        # ZIP 파일 저장
                        download_path.write_bytes(response.content)
                        shutil.unpack_archive(str(download_path), extract_dir=str(deg_dir))

                        # deg.zip 파일 삭제
                        if download_path.exists():
                            download_path.unlink()

                        st.success("✅ Deg generated successfully!")

                    else:
                        st.error(f"❌ Server error: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection failed: {e}")


#----------------- Result ----------------
    with result_tab:
        if deg_dir.exists():
            combo_csv = deg_dir / "combo_names.csv"
            if combo_csv.exists():
                combos = pd.read_csv(combo_csv)["combo"].tolist()
                if combos:
                    st.markdown("### 🧩 Filtered Results by Combination")
                    combo_tabs = st.tabs(combos)
                    for combo, tab in zip(combos, combo_tabs):
                        with tab:
                            file_path = deg_dir / combo / "filtered_gene_list.csv"
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

    # # ----------------- Download -----------------
    with download_tab:
        if deg_dir and (deg_dir / "combo_names.csv").exists():
            combos = pd.read_csv(deg_dir / "combo_names.csv")["combo"].tolist()
            if combos:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for combo in combos:
                        src = deg_dir / combo
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