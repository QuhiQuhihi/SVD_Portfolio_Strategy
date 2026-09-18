"""Execute both notebooks offline from cached prices and export readable HTML."""

import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parents[1]
for variable, directory in (
    ("MPLCONFIGDIR", "matplotlib"),
    ("IPYTHONDIR", "ipython"),
    ("JUPYTER_CONFIG_DIR", "jupyter"),
    ("JUPYTER_DATA_DIR", "jupyter_data"),
    ("JUPYTER_RUNTIME_DIR", "jupyter_runtime"),
):
    os.environ.setdefault(variable, str(ROOT / ".cache" / directory))


def main():
    for name in ("SVD-US_Equity.ipynb", "SVD-Multi_Asset.ipynb"):
        path = ROOT / name
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(
            nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
        )
        print(f"Executing {name} ...", flush=True)
        client.execute()
        nbformat.validate(nb)
        # Only replace a notebook after successful complete execution.
        temporary = path.with_suffix(".tmp")
        nbformat.write(nb, temporary)
        temporary.replace(path)
        html, _ = HTMLExporter().from_notebook_node(nb)
        output = ROOT / "outputs" / f"{path.stem}.html"
        output.write_text(html)
        print(f"Saved executed notebook and {output}", flush=True)


if __name__ == "__main__":
    main()
