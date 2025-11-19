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
st.title("🧬 GO Cnet Plot Analysis")

FASTAPI_CNET = os.getenv(
    "FASTAPI_CNET", "http://design-pathway-backend:8000/api/cnetplot"
)

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
main_tabs = st.tabs(["🧬 GO Cnet Plot"])
cnet_tab = main_tabs[0]

with cnet_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        output_dir = Path(st.session_state.workspace, "CnetPlot", "out")
        output_dir.mkdir(parents=True, exist_ok=True)

        showCategory = st.number_input("Number of categories to show", value=5, step=1)
        org_db = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
        plot_width = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height = st.number_input("Plot height", value=6.0, step=0.5)

        # ✅ 누락된 필드 추가
        fc_threshold = st.number_input("Fold change threshold", value=1.5, step=0.1, format="%.1f")
        pval_threshold = st.number_input(
            "P-value threshold", value=0.05, step=0.01, format="%.2f"
        )
        combo_root = deg_dir  # combo_names.csv가 있는 DEG 폴더
        enrich_dir = Path(st.session_state.workspace, "Enrichment", "out")

        st.session_state["cnet_params"] = {
            "enrich_root": str(enrich_dir),
            "output_root": str(output_dir),
            "combo_root": str(combo_root),
            "fc_threshold": fc_threshold,
            "pval_threshold": pval_threshold,
            "showCategory": showCategory,
            "org_db": org_db,
            "plot_width": plot_width,
            "plot_height": plot_height,
        }

    # ----------------- Run -----------------
    with run_tab:
        if "cnet_params" in st.session_state and combo_csv.exists():
            if st.button("🚀 Run GO Cnet Plot"):
                payload = st.session_state["cnet_params"]

                with st.spinner("Running Cnet Plot via FastAPI..."):
                    try:
                        response = requests.post(FASTAPI_CNET, json=payload, stream=False)

                        if response.status_code == 200:
                            # 결과 ZIP 저장 경로
                            download_path = output_dir / "cnetplot.zip"

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

                            st.success("📦 Cnet Plot results downloaded and unzipped successfully!")

                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")
        else:
            st.info("Please complete DEG filtering first before running Cnet Plot.")

    # ----------------- Result -----------------
    with result_tab:
        combo_name = f"FC{fc_threshold}_p{pval_threshold}"
        for ont in ["BP", "CC", "MF"]:
            st.markdown(f"### {combo_name} - {ont}")
            plot_file = output_dir / combo_name /f"cnet_{ont}.svg"
            if plot_file.exists():
                st.image(str(plot_file), width=750)
            else:
                st.warning(f"No Cnet plot found for {combo_name}")

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
                    zip_path = shutil.make_archive(
                        os.path.join(tmpdir, "CnetPlot_combos"), "zip", tmpdir
                    )
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Cnet Plot Results (ZIP)",
                            data=f,
                            file_name="CnetPlot_combos.zip",
                            mime="application/zip",
                        )
        else:
            st.info("No Cnet plot results available for download.")