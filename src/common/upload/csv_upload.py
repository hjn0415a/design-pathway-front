import shutil
from pathlib import Path
import streamlit as st
from src.common.common import reset_directory


def save_uploaded_csv(uploaded_files) -> None:
    """
    Saves uploaded CSV files to the csv directory.
    Handles both single and multiple file uploads.
    """
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_dir.mkdir(parents=True, exist_ok=True)

    # ✅ 업로드된 파일이 단일 파일이면 리스트로 감싸서 일관성 유지
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    if not uploaded_files:
        st.warning("Upload some CSV files first.")
        return

    for f in uploaded_files:
        # ✅ Streamlit UploadedFile 객체에 .name 이 존재하는지 확인
        if hasattr(f, "name") and f.name.endswith(".csv"):
            existing_files = [file.name for file in csv_dir.iterdir()]
            if f.name not in existing_files:
                out_path = csv_dir / f.name
                with open(out_path, "wb") as fh:
                    fh.write(f.getbuffer())

    st.success("Successfully added uploaded CSV files!")


def copy_local_csv_files_from_directory(local_csv_directory: str, make_copy: bool = True) -> None:
    """
    Copies local CSV files from a specified directory to the csv directory.
    """
    csv_dir = Path(st.session_state.workspace, "csv-files")
    csv_dir.mkdir(parents=True, exist_ok=True)
    valid_ext = ".csv"

    files = [f for f in Path(local_csv_directory).iterdir() if f.suffix.lower() == valid_ext]

    if not files:
        st.warning("No CSV files found in specified folder.")
        return

    for f in files:
        if make_copy:
            shutil.copy(f, csv_dir / f.name)
        else:
            external_files = csv_dir / "external_files.txt"
            if not external_files.exists():
                external_files.touch()
            with open(external_files, "a") as f_handle:
                f_handle.write(f"{f}\n")

    st.success("Successfully added local CSV files!")


def remove_selected_csv_files(to_remove: list[str], params: dict) -> dict:
    """
    Removes selected CSV files from the csv directory.
    """
    csv_dir = Path(st.session_state.workspace, "csv-files")

    for f in to_remove:
        (csv_dir / f).unlink(missing_ok=True)

    for k, v in params.items():
        if isinstance(v, list) and any(f in v for f in to_remove):
            params[k] = [item for item in v if item not in to_remove]

    st.success("Selected CSV files removed!")
    return params


def remove_all_csv_files(params: dict) -> dict:
    """
    Removes all CSV files from the csv directory.
    """
    csv_dir = Path(st.session_state.workspace, "csv-files")
    reset_directory(csv_dir)

    for k, v in params.items():
        if "csv" in k and isinstance(v, list):
            params[k] = []

    st.success("All CSV files removed!")
    return params