import os
import streamlit as st
import pandas as pd
import requests
import shutil
import tempfile
from pathlib import Path

from src.common.common import page_setup

# ----------------- 기본 설정 -----------------
params = page_setup()
st.title("🧬 GSEA GO Analysis")

FASTAPI_GSEGO = os.getenv("FASTAPI_GSEGO", "http://design-pathway-backend:8000/api/gsego")


# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 GSEA GO Analysis"])
gsea_tab = main_tabs[0]

with gsea_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:

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
        else:
            st.warning("분석 방법을 찾을 수 없습니다. DESeq2 분석을 먼저 실행해주세요.")    



        org_db = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
        min_gs_size = st.number_input("Minimum gene set size", value=10, step=1)
        max_gs_size = st.number_input("Maximum gene set size", value=500, step=10)
        pvalue_cutoff = st.number_input("P-value cutoff", value=0.05, step=0.01, format="%.2f")
        plot_width = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height = st.number_input("Plot height", value=6.0, step=0.5)
        workspace = Path(st.session_state.workspace)
        csv_path = workspace / "csv-files" / "output" / selected_method/f"merged_results_{selected_method}.csv"
        st.info(f"📂 Selected CSV Path: {csv_path}")
        output_dir = workspace / "csv-files" / "output" / selected_method/"gsego"
        # 선택된 CSV가 있을 때만 st.session_state에 저장
        if csv_path:
            st.session_state["gsego_params"] = {
                "file_path":str(csv_path),
                "out_dir": str(output_dir),
                "orgdb": org_db,
                "min_gs_size": min_gs_size,
                "max_gs_size": max_gs_size,
                "pvalue_cutoff": pvalue_cutoff,
                "plot_width": plot_width,
                "plot_height": plot_height,
            }

    # ----------------- Run -----------------
    with run_tab:
        if "gsego_params" in st.session_state:
            if st.button("🚀 Run GSEA GO Analysis"):
                payload = st.session_state["gsego_params"]

                with st.spinner("Running GSEA GO Analysis via FastAPI..."):
                    try:
                        response = requests.post(FASTAPI_GSEGO, json=payload, stream=False)

                        if response.status_code == 200:
                            # 결과 ZIP 저장 경로
                            download_path = output_dir / "gsego.zip"

                            # 기존 output_dir 삭제 후 재생성
                            if output_dir.exists():
                                shutil.rmtree(output_dir)
                            output_dir.mkdir(parents=True, exist_ok=True)

                            # ZIP 파일 저장
                            download_path.write_bytes(response.content)

                            # ZIP 압축 해제
                            shutil.unpack_archive(str(download_path), extract_dir=str(output_dir))

                            # ZIP 파일 삭제
                            if download_path.exists():
                                download_path.unlink()

                            st.success("📦 GSEA GO results downloaded and unzipped successfully!")

                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")
        else:
            st.info("Please complete DEG filtering first before running GSEA GO Analysis.")

    # # ----------------- Result -----------------
    with result_tab:
        if output_dir.exists():
            ontologies = ["BP", "CC", "MF"]
            ontology_tabs = st.tabs(ontologies)

            for ont_tab, ont in zip(ontology_tabs, ontologies):
                with ont_tab:
                    csv_file = output_dir / f"gse_{ont}.csv"  # gsego_{ont}.svg → gse_{ont}.csv
                    st.markdown(f"### {ont} Ontology Results")

                    if csv_file.exists():
                        try:
                            df = pd.read_csv(csv_file)
                            if df.empty:
                                st.info("No enriched terms found for this ontology.")
                            else:
                                st.dataframe(df)  # 테이블로 출력
                        except Exception as e:
                            st.error(f"Failed to read CSV file: {e}")
                    else:
                        st.warning(f"No CSV found for {ont}")
        else:
            st.info("No GSEA GO results found. Please run the analysis first.")

    # # ----------------- Download -----------------
    with download_tab:
        if output_dir.exists() and any(output_dir.iterdir()):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "GSEA_GO_results"), "zip", output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download GSEA GO Results (ZIP)",
                        data=f,
                        file_name="GSEA_GO_results.zip",
                        mime="application/zip",
                    )
        else:
            st.info("No GSEA GO results available for download.")