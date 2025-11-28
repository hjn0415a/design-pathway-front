import os
import streamlit as st
import pandas as pd
import requests
import shutil
import tempfile
from pathlib import Path

from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("🧬 GO Enrichment Analysis")

FASTAPI_ENRICH = os.getenv("FASTAPI_ENRICH", "http://design-pathway-backend:8000/api/enrichplot")



# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 GO Enrichment"])
enrich_tab = main_tabs[0]

with enrich_tab:
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

        showCategory = st.number_input("Number of categories to show", value=10, step=1)
        pvalueCutoff = st.number_input("P-value cutoff", value=0.9, step=0.01, format="%.3f")
        org_db = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
        plot_width = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height = st.number_input("Plot height", value=6.0, step=0.5)
        workspace = Path(st.session_state.workspace)
        deg_dir = workspace / "csv-files" / "output" / selected_method/ "deg"
        output_dir = deg_dir / "enrich"
        output_dir.mkdir(parents=True, exist_ok=True)
        combo_csv = deg_dir / "combo_names.csv"
        st.session_state["enrich_params"] = {
            "result_root": str(deg_dir),
            "output_root": str(output_dir),
            "showCategory": showCategory,
            "pvalueCutoff": pvalueCutoff,
            "org_db": org_db,
            "plot_width": plot_width,
            "plot_height": plot_height
        }

    # ----------------- Run -----------------
    with run_tab:
        if "enrich_params" in st.session_state:
            if st.button("🚀 Run GO Enrichment"):
                payload = st.session_state["enrich_params"]

                with st.spinner("Running GO Enrichment via FastAPI..."):
                    try:
                        response = requests.post(FASTAPI_ENRICH, json=payload, stream=False)

                        if response.status_code == 200:
                            # 결과 ZIP 저장 경로
                            download_path = output_dir / "enrich.zip"

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

                            st.success("📦 GO Enrichment results downloaded and unzipped successfully!")

                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")
        else:
            st.info("Please complete DEG filtering first before running enrichment.")

    # ----------------- Result -----------------
    with result_tab:
        combos = pd.read_csv(combo_csv)["combo"].tolist()
        ontology_tabs = st.tabs(["BP", "CC", "MF"])
        for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
            with ont_tab:
                st.subheader(f"Ontology: {ont}")

                # 각 combo마다 (plot_file, result_file) 쌍 생성
                pairs = []
                for combo in combos:
                    result_file = output_dir / combo / f"GO_{ont}_result.csv"
                    plot_file = output_dir / combo / "figure" / f"GO_{ont}.svg"
                    pairs.append((combo, plot_file if plot_file.exists() else None, result_file if result_file.exists() else None))

                if not pairs:
                    st.info("No results available.")
                    continue

                # 2개씩 묶어서 한 행에 2열 출력
                for i in range(0, len(pairs), 2):
                    left = pairs[i]
                    right = pairs[i+1] if i+1 < len(pairs) else None

                    cols = st.columns(2, gap="large")
                    # LEFT column
                    with cols[0]:
                        combo, plot_file, result_file = left
                        st.markdown(f"### {combo}")
                        if plot_file:
                            st.image(str(plot_file), use_container_width=True)
                        else:
                            st.info("No plot available.")
                        if result_file:
                            try:
                                df = pd.read_csv(result_file)
                                st.markdown(f"**Rows: {len(df)}**")
                                st.dataframe(df, use_container_width=True, height=300)
                            except Exception as e:
                                st.error(f"Failed to read table for {combo}: {e}")
                        else:
                            st.info("No result table available.")

                    # RIGHT column (if exists)
                    with cols[1]:
                        if right:
                            combo, plot_file, result_file = right
                            st.markdown(f"### {combo}")
                            if plot_file:
                                st.image(str(plot_file), use_container_width=True)
                            else:
                                st.info("No plot available.")
                            if result_file:
                                try:
                                    df = pd.read_csv(result_file)
                                    st.markdown(f"**Rows: {len(df)}**")
                                    st.dataframe(df, use_container_width=True, height=300)
                                except Exception as e:
                                    st.error(f"Failed to read table for {combo}: {e}")
                            else:
                                st.info("No result table available.")
                        else:
                            # 빈 칸을 채우지 않음 — 필요하면 안내문 표시 가능
                            st.write("") 


    # ----------------- Download -----------------
    with download_tab:
        if combo_csv.exists():
            combos = pd.read_csv(combo_csv)["combo"].tolist()
            if combos:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for combo in combos:
                        src = output_dir / combo
                        dst = Path(tmpdir, combo)
                        if src.exists():
                            shutil.copytree(src, dst)
                    zip_path = shutil.make_archive(os.path.join(tmpdir, "Enrichment_combos"), "zip", tmpdir)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Enrichment Results (ZIP)",
                            data=f,
                            file_name="Enrichment_combos.zip",
                            mime="application/zip"
                        )
        else:
            st.info("No enrichment results available for download.")