import re


def extract_frontmatter(source: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", source, re.DOTALL)
    if not match:
        return {}, source
    try:
        import yaml
        meta = yaml.safe_load(match.group(1))
        if not isinstance(meta, dict):
            meta = {}
    except Exception:
        meta = {}
    rest = source[match.end():]
    return meta, rest
