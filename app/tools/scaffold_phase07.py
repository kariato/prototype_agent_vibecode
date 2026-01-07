import os
from pathlib import Path

def scaffold_phase07_workspace(workspace_root: str) -> dict:
    root = Path(workspace_root)
    files_created = []
    
    # 1. adder.py
    adder_path = root / "adder.py"
    if not adder_path.exists():
        with open(adder_path, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        files_created.append("adder.py")
        
    # 2. tests/test_adder.py
    test_dir = root / "tests"
    test_dir.mkdir(exist_ok=True)
    test_path = test_dir / "test_adder.py"
    if not test_path.exists():
        with open(test_path, "w") as f:
            f.write("import unittest\nfrom adder import add\n\nclass TestAdder(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n")
        files_created.append("tests/test_adder.py")
        
    return {"status": "success", "files_created": files_created}
