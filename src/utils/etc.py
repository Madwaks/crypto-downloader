from pathlib import Path

def create_folder_and_parents(path: Path):
	if not path.exists():
		return path.mkdir(parents=True)