from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from corpus import DownloadStatus, Source
from fetch import download_file

# Test that we skip files that are already downloaded and meet minimum bytes
def test_skips_existing_file(tmp_path):
    source = Source(
        id="test_doc",
        url="http://example.com/test.txt",
        title="Test Document",
        source_type="gutenberg",
        min_bytes=10,
        file_extension=".txt",
    )
    # Create a file that satisfies the min_bytes check
    dest = tmp_path / "test_doc.txt"
    dest.write_text("this is more than ten bytes of content")

    from rich.progress import Progress
    with Progress() as progress:
        result = download_file(source=source, dest_dir=tmp_path, progress=progress)

    assert result == DownloadStatus.SKIPPED

# Confirm we will download file again if the one stored on disk is too small
def test_downloads_if_file_too_small(tmp_path: Path):
    source = Source(
        id="test_doc",
        url="http://example.com/test.txt",
        title="Test Document",
        source_type="gutenberg",
        min_bytes=1000,
        file_extension=".txt",
    )
    # File exists but is smaller than min_bytes
    dest = tmp_path / "test_doc.txt"
    dest.write_text("too small")

    mock_response = MagicMock()
    mock_response.headers = {"content-length": "100"}
    mock_response.iter_bytes.return_value = [b"fake content"]
    mock_response.__enter__ = lambda s: mock_response
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("fetch.httpx.stream", return_value=mock_response):
        from rich.progress import Progress
        with Progress() as progress:
            result = download_file(source=source, dest_dir=tmp_path, progress=progress)

    assert result == DownloadStatus.DOWNLOADED

# Simulate a network error and make sure we don't save a bad file
def test_failed_download_removes_partial_file(tmp_path: Path):
    source = Source(                                                                                                                          
        id="test_doc",
        url="http://example.com/test.txt",                                                                                                    
        title="Test Document",                                                                                                                
        source_type="gutenberg",
        min_bytes=10,                                                                                                                         
        file_extension=".txt",
    )

    with patch("fetch.httpx.stream", side_effect=Exception("network error")):                                                                 
        from rich.progress import Progress
        with Progress() as progress:                                                                                                          
            result = download_file(source=source, dest_dir=tmp_path, progress=progress)
                                                                                                                                            
    assert result == DownloadStatus.FAILED
    assert not (tmp_path / "test_doc.txt").exists() 