import os
import subprocess
import tempfile
import shutil
import streamlit as st
import pandas as pd

from frontend.src.common.common import page_setup
params = page_setup()

st.title("Enrichkegg Dotplot")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["🧬 Enrichkegg Dotplot"])
with main_tabs[0]:
    
    # ----------------- Sub Tabs -----------------
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # 기본 경로 설정
    deg_root    = "/data/Deg"
    enrich_root = "/data/Enrichkegg"
    combo_csv   = os.path.join(deg_root, "combo_names.csv")

    # ----------------- Configure -----------------
    with configure_tab:
        showCategory = st.number_input("Number of categories to show (showCategory)", value=10, step=1)
        plot_width   = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height  = st.number_input("Plot height", value=6.0, step=0.5)

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run Enrichkegg Dotplot Generation"):
            if not os.path.exists(combo_csv):
                st.error("combo_names.csv not found in DEG root.")
            else:
                combo_df = pd.read_csv(combo_csv)
                combo_names = combo_df["combo"].tolist() if "combo" in combo_df.columns else []

                if not combo_names:
                    st.warning("No combos found in combo_names.csv.")
                else:
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False, encoding="utf-8") as tmp_r:
                        r_script_path = tmp_r.name
                        combos_r = 'c(' + ','.join([f'"{c}"' for c in combo_names]) + ')'
                        tmp_r.write(f"""
library(clusterProfiler)
library(enrichplot)
library(ggplot2)

plot_enrichkegg_dotplots <- function(enrich_root,
                                     combo_names,
                                     showCategory = 10,
                                     width = 8, height = 6,
                                     device = "svg") {{
  for (nm in combo_names) {{
    combo_dir <- file.path(enrich_root, nm)
    rds_path  <- file.path(combo_dir, "KEGG_ekegg.rds")
    fig_dir   <- file.path(combo_dir, "figure")
    if (!dir.exists(fig_dir)) dir.create(fig_dir, recursive = TRUE)

    if (!file.exists(rds_path)) {{
      message(sprintf("[SKIP] %s: RDS not found -> %s", nm, rds_path))
      next
    }}

    ek <- tryCatch(readRDS(rds_path), error = function(e) NULL)
    if (is.null(ek)) {{
      message(sprintf("[SKIP] %s: failed to load RDS", nm))
      next
    }}

    df <- tryCatch(as.data.frame(ek), error = function(e) NULL)
    if (is.null(df) || nrow(df) == 0) {{
      message(sprintf("[SKIP] %s: KEGG result empty", nm))
      next
    }}

    p <- dotplot(ek, showCategory = showCategory,
                 x = "GeneRatio", color = "p.adjust") +
      ggtitle(sprintf("Enrichkegg - %s", nm))

    out_file <- file.path(fig_dir, paste0("Enrichkegg_dotplot.", device))
    ggsave(out_file, p, width = width, height = height, device = device)
    message(sprintf("[OK] %s: saved %s", nm, out_file))
  }}
}}

enrich_root <- "{enrich_root}"
combo_names <- {combos_r}

plot_enrichkegg_dotplots(
  enrich_root  = enrich_root,
  combo_names  = combo_names,
  showCategory = {showCategory},
  width        = {plot_width},
  height       = {plot_height},
  device       = "svg"
)
""")
                    # R 실행
                    result = subprocess.run(
                        ["Rscript", r_script_path],
                        capture_output=True,
                        text=True,
                        encoding="utf-8"
                    )
                    if result.returncode == 0:
                        st.success("Enrichkegg Dotplot generation completed!")
                        if result.stdout:
                            st.text(result.stdout)
                    else:
                        st.error("R script execution failed.")
                        if result.stderr:
                            st.text(result.stderr)

    # ----------------- Result -----------------
    with result_tab:
        if os.path.exists(combo_csv):
            combo_df = pd.read_csv(combo_csv)
            combo_names = combo_df["combo"].tolist() if "combo" in combo_df.columns else []

            if combo_names:
                # 콤보별 2개씩 가로 배치
                for i in range(0, len(combo_names), 2):
                    combo_pair = combo_names[i:i+2]
                    cols = st.columns(len(combo_pair))

                    for col, combo in zip(cols, combo_pair):
                        with col:
                            st.markdown(f"**{combo}**")
                            plot_file = os.path.join(enrich_root, combo, "figure", "Enrichkegg_dotplot.svg")
                            if os.path.exists(plot_file):
                                st.image(plot_file, width=750)
                            else:
                                st.info(f"No dotplot found for {combo}")
            else:
                st.info("No combos found in combo_names.csv.")
        else:
            st.warning("⚠️ combo_names.csv not found.")

    # ----------------- Download -----------------
    with download_tab:
        if os.path.exists(enrich_root):
            with tempfile.TemporaryDirectory() as tmpdir:
                for root, dirs, files in os.walk(enrich_root):
                    for f in files:
                        if f.endswith("Enrichkegg_dotplot.svg"):
                            src = os.path.join(root, f)
                            rel = os.path.relpath(root, enrich_root)
                            dst_dir = os.path.join(tmpdir, rel)
                            os.makedirs(dst_dir, exist_ok=True)
                            shutil.copy(src, dst_dir)
                zip_path = shutil.make_archive(os.path.join(tmpdir, "Enrichkegg_dotplots"), "zip", tmpdir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download All Enrichkegg Dotplots (ZIP)",
                        data=f,
                        file_name="Enrichkegg_dotplots.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No figures to download.")
