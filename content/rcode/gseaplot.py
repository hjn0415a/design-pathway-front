import os
import streamlit as st
import pandas as pd
import requests
import tempfile
import shutil

from pathlib import Path
from frontend.src.common.common import page_setup

# ----------------- PAGE SETUP -----------------
params = page_setup()

st.title("GSEA Plot (via FastAPI)")

# ----------------- FastAPI URLs -----------------
FASTAPI_TOTAL_URL = os.getenv("FASTAPI_GSEAPLOT_TOTAL", "http://localhost:8000/run_gseaplot_total")
FASTAPI_TERM_URL = os.getenv("FASTAPI_GSEAPLOT_TERM", "http://localhost:8000/run_gseaplot_term")

# ----------------- Workspace 체크 -----------------
if "workspace" not in st.session_state:
    st.error("❌ Workspace not found. Please configure workspace before running GSEA Plot.")
    st.stop()

workspace = st.session_state.workspace

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 GSEA Plot (total)", "📊 GSEA Term Plot"])
total_tab, term_tab = main_tabs

# ================================================================
# 🧩 TOTAL GSEA PLOT TAB
# ================================================================
with total_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        input_dir = Path(workspace, "gsea-results")
        output_dir = input_dir / "gseaplot_total"
        os.makedirs(output_dir, exist_ok=True)

        topN = st.number_input("Top N terms to plot", value=10, step=1, min_value=1)
        width = st.number_input("Plot width", value=12.0, step=0.5)
        height = st.number_input("Plot height", value=8.0, step=0.5)

        st.session_state["total_params"] = {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "topN": topN,
            "width": width,
            "height": height
        }

    # ----------------- RUN -----------------
    with run_tab:
        if st.button("Run Total gseaplot2"):
            params = st.session_state.get("total_params", {})
            with st.spinner("Running total gseaplot2 via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_TOTAL_URL, json=params, timeout=600)
                    if response.status_code == 200:
                        result = response.json()
                        st.success(result.get("message", "Total gseaplot2 completed successfully!"))
                        if result.get("stdout"):
                            st.text(result["stdout"])
                    else:
                        st.error(f"Failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # ----------------- RESULT -----------------
    with result_tab:
        if os.path.exists(output_dir):
            found_any = False
            for ont in ["BP", "CC", "MF"]:
                svgs = [f for f in os.listdir(output_dir) if f.endswith(".svg") and f"_{ont}_" in f]
                if svgs:
                    found_any = True
                    st.subheader(ont)
                    for svg in svgs:
                        st.markdown(f"**{svg}**")
                        st.image(os.path.join(output_dir, svg), width=850)
            if not found_any:
                st.info("No SVG plots found for BP/CC/MF.")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- DOWNLOAD -----------------
    with download_tab:
        if os.path.exists(output_dir) and os.listdir(output_dir):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "gseaplot2_total_results"), "zip", output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download Total gseaplot2 Results (ZIP)",
                        data=f,
                        file_name="gseaplot2_total_results.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No files to download.")

# ================================================================
# 🧩 GSEA TERM PLOT TAB
# ================================================================
with term_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- CONFIGURE -----------------
    with configure_tab:
        input_dir = Path(workspace, "gsea-results")
        output_dir = input_dir / "gseaplot"  # ✅ Term plot 전용 디렉토리
        os.makedirs(output_dir, exist_ok=True)

        ont = st.selectbox("Select ontology", ["BP", "CC", "MF"], index=0)
        csv_files = {"BP": "gse_BP.csv", "CC": "gse_CC.csv", "MF": "gse_MF.csv"}
        csv_path = input_dir / csv_files[ont]

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                st.dataframe(df)
                idx = st.number_input(
                    "Row index (1-based) for GSEA Term Plot",
                    min_value=1,
                    max_value=len(df),
                    value=1,
                    step=1
                )
                st.session_state["selected_idx"] = idx
            else:
                st.warning(f"{csv_files[ont]} is empty.")
        else:
            st.warning(f"{csv_files[ont]} not found in {input_dir}.")

    # ----------------- RUN -----------------
    with run_tab:
        if st.button("Run GSEA Term Plot"):
            idx = st.session_state.get("selected_idx", 1)
            payload = {
                "input_dir": str(input_dir),
                "output_dir": str(output_dir),
                "ont": ont,
                "idx": idx,
                "width": 8,
                "height": 8
            }

            with st.spinner("Running GSEA Term plot via FastAPI..."):
                try:
                    response = requests.post(FASTAPI_TERM_URL, json=payload, timeout=600)
                    if response.status_code == 200:
                        result = response.json()
                        st.success(result.get("message", "GSEA Term plot completed successfully!"))
                        if result.get("stdout"):
                            st.text(result["stdout"])
                    else:
                        st.error(f"Failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # ----------------- RESULT -----------------
    with result_tab:
        if os.path.exists(output_dir):
            images = [f for f in os.listdir(output_dir) if f.endswith(".svg")]
            if images:
                for f in images:
                    st.markdown(f"**{f}**")
                    st.image(os.path.join(output_dir, f), width=1000)
            else:
                st.info("No generated plots yet.")
        else:
            st.warning("Output directory does not exist.")

    # ----------------- DOWNLOAD -----------------
    with download_tab:
        if os.path.exists(output_dir) and os.listdir(output_dir):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "gseaplot_term_results"), "zip", output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download GSEA Term Plot Results (ZIP)",
                        data=f,
                        file_name="gseaplot_term_results.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No files to download.")