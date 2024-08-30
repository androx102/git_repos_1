import json
from pathlib import Path






script_dir = Path(__file__).resolve().parent
file_path = script_dir / "nodes_config.json"

json_handler_f = open(file_path)
json_handler = json.load(json_handler_f)


print(json_handler)