import subprocess
import sys
from pathlib import Path

binary = Path(sys.argv[1] if len(sys.argv) > 1 else "build/normal/parser")
for value, expected in [("boot", 0), ("#init", 1)]:
    outcome = subprocess.run([str(binary), value], check=False)
    assert outcome.returncode == expected, (value, outcome.returncode)
print("logger regression tests passed")
