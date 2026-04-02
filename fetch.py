"""
Task 3.2 - Retrieval-Augmented QA
This is our document retriever. The list of documents we are pulling is defined here
and defines the dataclass for a file
"""
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn

from corpus import SOURCES, DownloadStatus, Source

console = Console()

def main():
    dest_dir = Path("data/raw")
    manifest_file = Path("data/corpus_manifest.json")

    # If dest_dir doesn't exist, create it
    dest_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        DownloadColumn(),
    ) as progress:
        # Loop the corpus sources and attempt a download
        for source in SOURCES:
            file_path = dest_dir / f"{source.id}{source.file_extension}"
            status = download_file(source=source, dest_dir=dest_dir, progress=progress)
            results.append({"source": source, "status": status, "path": file_path})

    # Add/update manifest of successfully downloaded corpus files
    manifest_data: list[dict[str, Any]] = []
    for result in results:  
        if result["status"] != DownloadStatus.FAILED:
            path = result["path"]
            source = result["source"]
            manifest_data.append({
                "id": source.id,
                "title": source.title,
                "path": str(path),
                "source_type": source.source_type,
                "size_bytes": path.stat().st_size,
                "fetched_at": datetime.now(UTC).isoformat(),
                "url": source.url,
            })

    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f, indent=2)

    total_size = sum(entry["size_bytes"] for entry in manifest_data)
    console.print(f"[bold green]Manifest written to {manifest_file}")
    console.print(f"{len(manifest_data)} sources, {total_size / 1_000_000:.1f} MB total")

def download_file(source: Source, dest_dir: Path, progress: Progress) -> DownloadStatus:
    destination_path = dest_dir / f"{source.id}{source.file_extension}"

    # idempotency check. File being present is not enough. We expect it to be at least a certain
    # size. If it is present but smaller, we should try download again.
    # If it is present and larger, we avoid downloading every time this runs
    if destination_path.exists() and destination_path.stat().st_size >= source.min_bytes:
        progress.add_task(f"[dim]{source.title} (skipped)[/dim]", total=1, completed=1)
        return DownloadStatus.SKIPPED
    
    # THE DOWNLOAD
    try:
        with httpx.stream("GET", source.url, follow_redirects=True) as response:
            response.raise_for_status() # Raise the status error
            total_length = int(response.headers.get("content-length", 0))
            task_id = progress.add_task(source.title, total=total_length)
            with open(destination_path, "wb") as file:
                # Loop chunks from the source, write them to local file, update progress
                for chunk in response.iter_bytes(8192):
                    file.write(chunk)
                    progress.update(task_id=task_id, advance=len(chunk))
    except Exception as e:
        # An error retrieving the file. Delete our current document and output an error
        if destination_path.exists():
            destination_path.unlink()

        console.print(f"[red]Failed to download {source.title}: {e}[/red]")
        return DownloadStatus.FAILED
    
    # Download completed successfully if we get here
    return DownloadStatus.DOWNLOADED

if __name__ == "__main__":
      main()
