import os
import requests
import streamlit as st
import pandas as pd
import shutil
import tempfile
from pathlib import Path

from frontend.src.common.common import page_setup

# 페이지 설정
params = page_setup()
st.title("🧬 Emapplot")

FASTAPI_URL = os.getenv("FASTAPI_EMAPPLOT", "http://fastapi:8000/run-emapplot/")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["🧬 Emapplot"])
with main_tabs[0]:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        # ✅ workspace 기반 경로 설정
        workspace = Path(st.session_state.workspace)
        result_root = workspace / "Enrichment" / "out"
        figure_root = workspace / "Emap" / "emapplots"
        combo_root = workspace / "Deg"
        figure_root.mkdir(parents=True, exist_ok=True)

        combo_csv = combo_root / "combo_names.csv"
        selected_combos = []

        if combo_csv.exists():
            combo_df = pd.read_csv(combo_csv)
            fc_values = sorted(list({float(c.split("_")[0][2:]) for c in combo_df["combo"]}))
            pval_values = sorted(list({float(c.split("_")[1][1:]) for c in combo_df["combo"]}))

            fc_threshold = st.selectbox("Select FC threshold", options=fc_values, index=0)
            pval_threshold = st.selectbox("Select P-value threshold", options=pval_values, index=0)

            selected_combos = [
                c
                for c in combo_df["combo"]
                if float(c.split("_")[0][2:]) == fc_threshold
                and float(c.split("_")[1][1:]) == pval_threshold
            ]
        else:
            st.warning("⚠️ combo_names.csv not found in Deg directory.")
            fc_threshold, pval_threshold = None, None

        show_n = st.number_input("Number of categories to show", value=20, step=1)
        plot_width = st.number_input("Plot width", value=9.0, step=0.5)
        plot_height = st.number_input("Plot height", value=7.0, step=0.5)

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run Emapplot Generation"):
            if not selected_combos:
                st.warning("No combos match the selected FC/P-value thresholds.")
            else:
                payload = {
                    "result_root": str(result_root),
                    "figure_root": str(figure_root),
                    "combo_names": selected_combos,
                    "show_n": show_n,
                    "plot_width": plot_width,
                    "plot_height": plot_height
                }

                with st.spinner("Generating Emapplots..."):
                    try:
                        response = requests.post(FASTAPI_URL, json=payload, timeout=300)
                        if response.status_code == 200:
                            st.success("✅ Emapplot generation completed!")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Request failed ({response.status_code})")
                            st.text(response.text)
                    except Exception as e:
                        st.error(f"🚨 FastAPI request failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        if selected_combos:
            ontology_tabs = st.tabs(["BP", "CC", "MF"])
            for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
                with ont_tab:
                    st.subheader(f"Ontology: {ont}")
                    for i in range(0, len(selected_combos), 2):
                        combo_pair = selected_combos[i:i+2]
                        cols = st.columns(len(combo_pair))
                        for col, combo in zip(cols, combo_pair):
                            with col:
                                st.markdown(f"**{combo}**")
                                plot_file = figure_root / combo / f"emap_{ont}.svg"
                                if plot_file.exists():
                                    st.image(str(plot_file), width=900)
                                else:
                                    st.info(f"No {ont} plot found for {combo}")
        else:
            st.info("No combos selected.")

    # ----------------- Download -----------------
    with download_tab:
        if selected_combos:
            with tempfile.TemporaryDirectory() as tmpdir:
                for combo in selected_combos:
                    src = figure_root / combo
                    dst = Path(tmpdir) / combo
                    if src.exists():
                        shutil.copytree(src, dst)
                zip_path = shutil.make_archive(str(Path(tmpdir) / "Emapplots_combos"), "zip", tmpdir)

                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Emapplot Results (ZIP)",
                        data=f,
                        file_name="Emapplots_combos.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No figures to download.")