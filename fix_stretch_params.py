"""Script to fix all `width='stretch'` to `use_container_width=True` in frontend files."""
import re
from pathlib import Path

frontend_dir = Path("Frontend")
stretch_pattern = re.compile(r"width='stretch'")

files_to_fix = list(frontend_dir.rglob("*.py"))

for filepath in files_to_fix:
    content = filepath.read_text(encoding="utf-8")
    if "width='stretch'" in content:
        new_content = content.replace("width='stretch'", "use_container_width=True")
        filepath.write_text(new_content, encoding="utf-8")
        print(f"FIXED: {filepath}")

print("\nDone!")

