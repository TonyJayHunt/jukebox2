import os
import csv
import tempfile
import useful_tools.get_files as get_files

def test_extract_files_to_csv(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    (d / "a.mp3").write_text("dummy")
    (d / "b.txt").write_text("dummy")
    # Create a subdirectory to check directory filtering
    (d / "subdir").mkdir()
    out_csv = tmp_path / "files.csv"
    get_files.extract_files_to_csv(str(d), str(out_csv))
    with open(out_csv, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    assert rows[0] == ['Filename']
    # Should list files only, with ".mp3" removed
    filenames = [row[0] for row in rows[1:]]
    assert any("a" in name for name in filenames)
    assert not any("subdir" in name for name in filenames)
