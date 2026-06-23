import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger("paperless-letter-generator.latex")


class LatexCompileError(Exception):
    def __init__(self, message: str, log: str = ""):
        super().__init__(message)
        self.log = log


def discover_variables(latex_source: str) -> list[str]:
    seen: set[str] = set()
    variables: list[str] = []
    for match in re.finditer(r"\{\{\s*(\w+)\s*\}\}", latex_source):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            variables.append(name)
    return variables


def substitute_variables(latex_source: str, values: dict[str, str]) -> str:
    def replacer(match: re.Match) -> str:
        name = match.group(1)
        return values.get(name, match.group(0))
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", replacer, latex_source)


def _ensure_fontspec(latex_source: str) -> str:
    if r"\usepackage{fontspec}" not in latex_source:
        latex_source = re.sub(
            r"(\\documentclass(?:\[.*?\])?\{.*?\})",
            r"\1\n\\usepackage{fontspec}",
            latex_source,
            count=1,
        )
    return latex_source


def compile_latex(latex_source: str, output_dir: Path, timeout: int = 60) -> Path:
    latex_source = _ensure_fontspec(latex_source)
    tex_file = output_dir / "document.tex"
    tex_file.write_text(latex_source, encoding="utf-8")

    try:
        result = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise LatexCompileError("lualatex not found. Install texlive-latex-base.")
    except subprocess.TimeoutExpired:
        raise LatexCompileError("LaTeX compilation timed out.")

    pdf = output_dir / "document.pdf"

    second = subprocess.run(
        ["lualatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
        capture_output=True, text=True, timeout=timeout,
    )

    if not pdf.exists():
        log = result.stdout[-2000:] + "\n" + result.stderr[-2000:]
        raise LatexCompileError("LaTeX compilation failed", log=log)

    return pdf


def generate_pdf(template_source: str, field_values: dict[str, str], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    substituted = substitute_variables(template_source, field_values)
    return compile_latex(substituted, output_dir)
