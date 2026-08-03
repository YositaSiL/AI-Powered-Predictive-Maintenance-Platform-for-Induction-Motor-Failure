"""Check for remaining `width='stretch'` or other issues in frontend files."""
from pathlib import Path

frontend_dir = Path("Frontend")

print("=== Checking for remaining width='stretch' ===")
for filepath in sorted(frontend_dir.rglob("*.py")):
    content = filepath.read_text(encoding="utf-8")
    if "width='stretch'" in content or 'width="stretch"' in content:
        print(f"  ISSUE: {filepath}")

print("\n=== Checking for common import issues ===")

# Check app.py for imports of update_one_cycle
app_py = frontend_dir / "app.py"
content = app_py.read_text(encoding="utf-8")
# Check if update_one_cycle is defined in app.py or imported
if "def update_one_cycle" in content:
    print("  OK: update_one_cycle is defined in app.py")
else:
    print("  WARNING: update_one_cycle not found in app.py")

# Check 1_Sensor_Monitoring.py for imports
sensor_py = frontend_dir / "pages" / "1_Sensor_Monitoring.py"
sensor_content = sensor_py.read_text(encoding="utf-8")
if "from Frontend.app import update_one_cycle" in sensor_content:
    print("  Sensor page imports update_one_cycle from app.py (circular import risk!)")

print("\n=== Checking page files for basic structure ===")
for filepath in sorted((frontend_dir / "pages").rglob("*.py")):
    content = filepath.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    print(f"  {filepath.name}: {len(lines)} lines, has_content={len(content) > 100}")

print("\nDone!")

