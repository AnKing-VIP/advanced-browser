import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time


scriptdir = os.path.dirname(os.path.realpath(__file__))
code_folder = os.path.join(scriptdir, "advancedbrowser")
tmp_dir = tempfile.mkdtemp()
manifest_in_json = os.path.join(tmp_dir, "manifest.json")

if sys.version_info.minor >= 8:
    shutil.copytree(code_folder, tmp_dir, dirs_exist_ok=True, copy_function=shutil.copy)
else:
    print("Aborting. This build script only supports python 3.8 or later")
    sys.exit()

with open(manifest_in_json, "r") as f:
    data = json.load(f)
data["mod"] = int(time.time())
with open(manifest_in_json, "w") as f:
    json.dump(data, f)

target_zip_file = os.path.join(scriptdir, f"advanced_browser__branch_index_{data['branch_index']}___{time.strftime('%Y-%m-%d_%H-%M')}")
shutil.make_archive(target_zip_file, 'zip', tmp_dir)
p = Path(f"{target_zip_file}.zip")
p.rename(p.with_suffix('.ankiaddon'))

shutil.rmtree(tmp_dir)
