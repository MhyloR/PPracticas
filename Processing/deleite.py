from pathlib import Path
import shutil
import fnmatch
from typing import Iterable, List, Optional


class DirectoryCleanerError(Exception):
    """Custom exception for directory cleaning operations."""
    pass


class DirectoryCleaner:
    """
    Cleans the contents of a directory with options for:
      - Recursive deletion (including subfolders)
      - Excluding files/folders using glob patterns
      - Dry-run mode (simulation, no deletion)
      - Detailed reporting of actions and errors
    """

    def __init__(self, folder: str | Path):
        self.folder = Path(folder).expanduser().resolve()
        if not self.folder.exists():
            raise DirectoryCleanerError(f"Directory does not exist: {self.folder}")
        if not self.folder.is_dir():
            raise DirectoryCleanerError(f"Path is not a directory: {self.folder}")

    def _matches_exclusion(self, path: Path, patterns: Iterable[str]) -> bool:
        if not patterns:
            return False

        name = path.name
        relative_path = str(path.relative_to(self.folder))

        return any(
            fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative_path, pattern)
            for pattern in patterns
        )

    def list_targets(
        self,
        recursive: bool = True,
        exclude: Optional[Iterable[str]] = None
    ) -> List[Path]:
        """
        Returns a list of files and folders to be deleted.
        exclude examples: "*.log", "__pycache__", ".git", "subfolder/*"
        """
        exclude = list(exclude or [])
        targets: List[Path] = []

        for item in self.folder.iterdir():
            if self._matches_exclusion(item, exclude):
                continue
            targets.append(item)

        return sorted(targets)

    def delete_all(
        self,
        recursive: bool = True,
        exclude: Optional[Iterable[str]] = None,
        dry_run: bool = False,
        verbose: bool = True
    ) -> dict:
        """
        Deletes ALL contents inside the directory (root folder is preserved).

        Parameters:
        - recursive: include subdirectories
        - exclude: glob patterns to exclude
        - dry_run: if True, simulate deletion
        - verbose: print actions to console

        Returns a summary dictionary.
        """
        exclude = list(exclude or [])
        targets = self.list_targets(recursive=recursive, exclude=exclude)

        summary = {
            "directory": str(self.folder),
            "found_items": len(targets),
            "deleted_files": 0,
            "deleted_folders": 0,
            "excluded_patterns": exclude,
            "errors": []
        }

        if verbose:
            mode = "DRY RUN (simulation)" if dry_run else "EXECUTION"
            print(f"[{mode}] Cleaning directory: {self.folder}")
            if exclude:
                print(f"Excluding patterns: {', '.join(exclude)}")
            print(f"Items found: {len(targets)}")

        for path in targets:
            try:
                if dry_run:
                    if verbose:
                        print(f"→ (dry-run) Would delete: {path}")
                    continue

                if path.is_file() or path.is_symlink():
                    path.unlink(missing_ok=True)
                    summary["deleted_files"] += 1
                    if verbose:
                        print(f"✓ File deleted: {path}")

                elif path.is_dir():
                    shutil.rmtree(path)
                    summary["deleted_folders"] += 1
                    if verbose:
                        print(f"✓ Folder deleted: {path}")

                else:
                    raise DirectoryCleanerError(f"Unsupported file type: {path}")

            except Exception as e:
                error_msg = f"Failed to delete {path}: {e}"
                summary["errors"].append(error_msg)
                if verbose:
                    print(f"✗ {error_msg}")

        if verbose:
            print("\nSummary")
            print(f"- Files deleted: {summary['deleted_files']}")
            print(f"- Folders deleted: {summary['deleted_folders']}")
            print(f"- Errors: {len(summary['errors'])}")

        return summary

