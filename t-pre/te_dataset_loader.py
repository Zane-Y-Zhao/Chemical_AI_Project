"""Automatically download and load the Tennessee Eastman dataset from GitHub."""

from __future__ import annotations

import json
import shutil
import urllib.request
import warnings
import zipfile
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

REPO = "anasouzac/new_tep_datasets"
BRANCH = "main"
ARCHIVE_URL = f"https://codeload.github.com/{REPO}/zip/refs/heads/{BRANCH}"
LFS_BATCH_URL = f"https://github.com/{REPO}.git/info/lfs/objects/batch"


def get_project_root() -> Path:
    return Path(__file__).resolve().parent


def get_data_root() -> Path:
    data_root = get_project_root() / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root


def download_github_archive(destination: Path) -> Path:
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    print(f"Downloading dataset archive from: {ARCHIVE_URL}")
    urllib.request.urlretrieve(ARCHIVE_URL, destination)
    return destination


def extract_archive(archive_path: Path, extract_to: Path) -> Path:
    if extract_to.exists():
        shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, "r") as zip_file:
        zip_file.extractall(extract_to)

    return extract_to


def parse_lfs_pointer(file_path: Path) -> tuple[str, int] | None:
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None

    if not content.startswith("version https://git-lfs.github.com/spec/v1"):
        return None

    oid: str | None = None
    size: int | None = None

    for line in content.splitlines():
        if line.startswith("oid sha256:"):
            oid = line.split(":", 1)[1].strip()
        elif line.startswith("size "):
            size = int(line.split()[1])

    if not oid or size is None:
        raise ValueError(f"Invalid Git LFS pointer file: {file_path}")

    return oid, size


def download_lfs_object(oid: str, size: int) -> bytes:
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "objects": [{"oid": oid, "size": size}],
    }
    request = urllib.request.Request(
        LFS_BATCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        batch_data = json.loads(response.read().decode("utf-8"))

    objects = batch_data.get("objects", [])
    if not objects:
        raise ValueError("Git LFS batch response did not contain any objects.")

    object_data = objects[0]
    if "error" in object_data:
        raise RuntimeError(f"Git LFS error: {object_data['error']}")

    download_action = object_data.get("actions", {}).get("download")
    if not download_action or "href" not in download_action:
        raise ValueError("Git LFS batch response did not include a download URL.")

    download_request = urllib.request.Request(download_action["href"])
    for header_name, header_value in download_action.get("header", {}).items():
        download_request.add_header(header_name, header_value)

    with urllib.request.urlopen(download_request, timeout=15) as response:
        return response.read()


def resolve_lfs_pointer_if_needed(file_path: Path) -> Path:
    pointer_info = parse_lfs_pointer(file_path)
    if pointer_info is None:
        return file_path

    oid, size = pointer_info
    print(f"Resolving Git LFS file: {file_path.as_posix()}")
    file_path.write_bytes(download_lfs_object(oid, size))
    return file_path


def read_text_table(file_path: Path) -> pd.DataFrame:
    attempts = [
        {"sep": r"\s+", "engine": "python"},
        {"sep": ",", "engine": "python"},
        {"sep": "\t", "engine": "python"},
    ]

    last_error: Exception | None = None
    for kwargs in attempts:
        try:
            return pd.read_csv(
                file_path,
                header=None,
                comment="#",
                **kwargs,
            )
        except Exception as error:  # pragma: no cover - fallback path
            last_error = error

    raise ValueError(f"Unable to read text file: {file_path}") from last_error


def read_tabular_file(file_path: Path) -> pd.DataFrame:
    file_path = resolve_lfs_pointer_if_needed(file_path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(file_path, sep=None, engine="python")
        unnamed_columns = [column for column in frame.columns if str(column).startswith("Unnamed") or str(column) == ""]
        if unnamed_columns:
            frame = frame.drop(columns=unnamed_columns)
        return frame

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path, header=None, engine="openpyxl")

    if suffix in {".dat", ".txt", ".csv"}:
        return read_text_table(file_path)

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def collect_data_files(root: Path) -> list[Path]:
    supported_suffixes = {".dat", ".txt", ".csv", ".xlsx", ".xls"}
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


def load_te_dataset(root: Path) -> pd.DataFrame:
    data_frames: list[pd.DataFrame] = []
    data_files = collect_data_files(root)
    skipped_files: list[str] = []

    if not data_files:
        raise FileNotFoundError(f"No supported data files were found under: {root}")

    for file_path in data_files:
        relative_path = file_path.relative_to(root).as_posix()
        try:
            frame = read_tabular_file(file_path)
            if frame.empty:
                continue

            frame.insert(0, "source_file", relative_path)
            frame.insert(1, "source_format", file_path.suffix.lower().lstrip("."))
            data_frames.append(frame)
        except Exception as error:
            skipped_files.append(f"{relative_path} ({error})")
            print(f"Skipping {relative_path}: {error}")

    if not data_frames:
        raise ValueError("All discovered data files were empty.")

    if skipped_files:
        print(f"Skipped {len(skipped_files)} file(s) that could not be loaded.")

    return pd.concat(data_frames, ignore_index=True, sort=False)


def main() -> None:
    data_root = get_data_root()
    archive_path = data_root / "tennessee-eastman-dataset-main.zip"
    extract_root = data_root / "tennessee-eastman-dataset"
    csv_path = data_root / "TE_dataset.csv"

    download_github_archive(archive_path)
    extract_archive(archive_path, extract_root)

    dataset = load_te_dataset(extract_root)
    dataset.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"Saved CSV to: {csv_path}")
    print(f"Rows: {dataset.shape[0]}")
    print(f"Columns: {dataset.shape[1]}")
    print("First 5 rows:")
    print(dataset.head(5).to_string(index=False))


if __name__ == "__main__":
    main()