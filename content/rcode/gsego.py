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

# ----------------- 업로드된 DEG 결과 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to Upload or DEG tab first.")
    csv_files = []
else:
    deg_dir = Path(st.session_state.workspace, "Deg")
    deg_dir.mkdir(parents=True, exist_ok=True)

    combo_csv = deg_dir / "combo_names.csv"
    if not combo_csv.exists():
        st.warning("⚠️ No DEG results found. Please run DEG filtering first.")
        csv_files = []
    else:
        combos = pd.read_csv(combo_csv)["combo"].tolist()

# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 GSEA GO Analysis"])
gsea_tab = main_tabs[0]

with gsea_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        output_dir = Path(st.session_state.workspace, "GSEA_GO", "out")
        output_dir.mkdir(parents=True, exist_ok=True)

        org_db = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
        min_gs_size = st.number_input("Minimum gene set size", value=10, step=1)
        max_gs_size = st.number_input("Maximum gene set size", value=500, step=10)
        pvalue_cutoff = st.number_input("P-value cutoff", value=0.05, step=0.01, format="%.2f")
        plot_width = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height = st.number_input("Plot height", value=6.0, step=0.5)

        st.write("**DEG directory:**", str(deg_dir))
        st.write("**Output directory:**", str(output_dir))

        # csv-files 폴더에서 업로드된 CSV 파일 목록 가져오기
        csv_dir = Path(st.session_state.workspace, "csv-files")
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_paths = sorted([p for p in csv_dir.glob("*.csv")])

        if not csv_paths:
            st.warning("⚠️ No CSV files found in csv-files folder. Please upload a CSV file first.")
            csv_path = None
        else:
            selected_csv = st.selectbox(
                "Select CSV file for GSEA GO Analysis",
                [p.name for p in csv_paths]
            )
            csv_path = str(csv_dir / selected_csv)
            st.info(f"📂 Selected CSV Path: {csv_path}")

        # 선택된 CSV가 있을 때만 st.session_state에 저장
        if csv_path:
            st.session_state["gsego_params"] = {
                "file_path": csv_path,
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
        if "gsego_params" in st.session_state and combo_csv.exists():
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

    # ----------------- Result -----------------
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

    # ----------------- Download -----------------
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