import subprocess
from pathlib import Path

binary = Path("build/parser")
for value, expected in [("hello", 0), ("!", 1)]:
    outcome = subprocess.run([str(binary), value], check=False)
    assert outcome.returncode == expected, (value, outcome.returncode)
print("regression tests passed")
