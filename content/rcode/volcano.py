import os
import requests
import streamlit as st
from pathlib import Path
from src.common.common import page_setup
import pandas as pd

# ----------------- 기본 설정 -----------------
params = page_setup()
st.title("Volcano Plot")

FASTAPI_VOLCANO = os.getenv("FASTAPI_VOLCANO", "http://design-pathway-backend:8000/api/volcano/")

# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🌋 Volcano Plot"])
volcano_tab = main_tabs[0]

# ----------------- Volcano Plot -----------------
with volcano_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # Configure
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
            st.session_state.selected_method_volcano = selected_method
        else:
            st.warning("분석 방법을 찾을 수 없습니다. DESeq2 분석을 먼저 실행해주세요.")

        fc_cutoff = st.number_input("Fold Change Cutoff (log2)", value=1.0, step=0.1, min_value=0.0)
        pval_cutoff = st.number_input("P-value Cutoff", value=0.05, step=0.01, min_value=0.0, max_value=1.0, format="%.4f")

        # Configure에서 설정값 저장
        st.session_state.fc_cutoff = fc_cutoff
        st.session_state.pval_cutoff = pval_cutoff

    # Run
    with run_tab:
        if "selected_method_volcano" in st.session_state and st.session_state.selected_method_volcano:
            selected_method = st.session_state.selected_method_volcano
            st.info(f"선택된 분석 방법: **{selected_method}**")

            # FastAPI에서 저장하는 위치와 동일한 경로 설정
            output_dir = Path(st.session_state.workspace) / "csv-files" / "output" / selected_method
            output_filename = f"volcano_{selected_method}.svg"
            output_svg_volcano = output_dir / output_filename

            # session_state에 저장
            st.session_state.output_svg_volcano = output_svg_volcano

            if st.button("🚀 Run Volcano Plot"):
                with st.spinner("Running Volcano Plot analysis..."):
                    try:
                        payload = {
                            "workspace": str(st.session_state.workspace),
                            "method": selected_method,
                            "fc_cutoff": st.session_state.fc_cutoff,
                            "pval_cutoff": st.session_state.pval_cutoff
                        }
                        
                        response = requests.post(FASTAPI_VOLCANO, data=payload, timeout=300)

                        if response.status_code == 200:
                            # 디렉토리 생성
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            # SVG 파일 저장 (FastAPI와 동일한 위치)
                            with open(output_svg_volcano, "wb") as f_out:
                                f_out.write(response.content)
                            
                            st.success(f"✅ Volcano Plot generated successfully at: {output_svg_volcano}")
                        else:
                            st.error(f"❌ Server error: {response.text}")

                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timeout (5 minutes)")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Connection failed: {e}")
        else:
            st.warning("⚠️ Configure 탭에서 분석 방법을 먼저 선택해주세요.")

    # Result
    with result_tab:
        if "output_svg_volcano" in st.session_state:
            output_svg_volcano = st.session_state.output_svg_volcano
            
            if output_svg_volcano.exists():
                st.markdown(f"### Volcano Plot Result: {output_svg_volcano.name}")
                st.image(str(output_svg_volcano), caption="Volcano Plot", use_container_width=True)
            else:
                st.info("Volcano Plot을 생성하려면 Run 탭에서 실행해주세요.")
        else:
            st.info("Configure와 Run 탭을 먼저 실행해주세요.")

    # Download
    with download_tab:
        if "output_svg_volcano" in st.session_state:
            output_svg_volcano = st.session_state.output_svg_volcano
            
            if output_svg_volcano.exists():
                with open(output_svg_volcano, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Volcano SVG",
                        data=f,
                        file_name=output_svg_volcano.name,
                        mime="image/svg+xml"
                    )
                st.success(f"📁 File location: {output_svg_volcano}")
            else:
                st.warning("⚠️ Volcano Plot 파일이 존재하지 않습니다. Run 탭에서 먼저 실행해주세요.")
        else:
            st.info("Configure와 Run 탭을 먼저 실행해주세요.")