
# #!/usr/bin/env python3

# Extract hotel quote metadata from emails, PDFs, or HTML proposals using the latest OpenAI Responses API.

# - Handles: .pdf, .html/.htm, and plaintext (.txt) inputs; a single file or a directory
# - Extracts text using:
#     * unstructured (if installed) for PDFs
#     * PyPDF2 fallback for PDFs
#     * BeautifulSoup (if installed) or html2text-like fallback for HTML
# - Sends full text to the LLM with a hotel-quote-specific JSON schema prompt
# - Saves JSON as <basename>.json in --out
# - Retries with exponential backoff

# Example:
#     export OPENAI_API_KEY=...
#     python extract_hotel_quotes.py --input ./samples --out ./out --model gpt-4o-mini


import os
import re
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Retry utilities
try:
    from tenacity import retry, wait_random_exponential, stop_after_attempt
except Exception:
    def retry(*a, **k):
        def deco(fn): return fn
        return deco
    def wait_random_exponential(*a, **k): return None
    def stop_after_attempt(*a, **k): return None

# -------------------- Extraction helpers --------------------
def _extract_pdf_unstructured(path: str) -> Optional[str]:
    try:
        from unstructured.partition.pdf import partition_pdf
        elems = partition_pdf(path, strategy="hi_res")
        return "\n".join(str(e) for e in elems)
    except Exception:
        return None

def _extract_pdf_pypdf2(path: str) -> Optional[str]:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pass
        return "\n".join(pages).strip() or None
    except Exception:
        return None

def _extract_html_bs4(path: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        # Get visible text with reasonable spacing
        text = soup.get_text(separator="\n")
        return re.sub(r"\n{2,}", "\n", text).strip()
    except Exception:
        return None

def _extract_html_fallback(path: str) -> Optional[str]:
    # Very rough fallback if bs4 not available
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        # strip tags
        text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    except Exception:
        return None

def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        # Try PyPDF2 first (more reliable with latest versions)
        text = _extract_pdf_pypdf2(path) or _extract_pdf_unstructured(path)
        if text: return text
        raise RuntimeError(f"Failed to extract text from PDF: {path}")
    elif ext in {".html", ".htm"}:
        text = _extract_html_bs4(path) or _extract_html_fallback(path)
        if text: return text
        raise RuntimeError(f"Failed to extract text from HTML: {path}")
    else:
        # treat as plaintext
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def read_prompt(path: Optional[str]) -> str:
    # First try the provided path
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Then try hotel_quote_prompt.txt in the same directory as the script
    script_dir = Path(__file__).parent
    default_prompt_path = script_dir / "hotel_quote_prompt.txt"
    if default_prompt_path.exists():
        with open(default_prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Built-in default prompt (short)
    return """Extract hotel quote data into JSON with totals, extras, and calculations. Include property info, program details, fees, policies, concessions, and calculated totals with status fields (explicit, derived, conditional, not_found)."""

def get_client():
    try:
        from openai import OpenAI
        return OpenAI()
    except Exception as e:
        raise RuntimeError("Install the OpenAI SDK v1+: pip install openai") from e

def get_model(cli: Optional[str]) -> str:
    return cli or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

def _truncate(text: str, max_chars: int = 180_000) -> str:
    return text if len(text) <= max_chars else text[:max_chars]

def call_llm(client, model: str, system_prompt: str, content: str) -> Dict[str, Any]:
    # Simple retry logic without external dependencies
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract and analyze the hotel quote data from this document:\n\n{content}"},
                ],
            )
            out = resp.choices[0].message.content or ""
            # Extract last JSON object in case of any wrapper
            m = re.search(r"\{[\s\S]*\}\s*$", out)
            j = m.group(0) if m else out
            try:
                result = json.loads(j)
                # Validate and normalize the result structure
                return normalize_result(result)
            except Exception:
                return {"raw": out, "error": "Failed to parse JSON response"}
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            import time
            time.sleep(2 ** attempt)  # Exponential backoff

def normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the result to ensure it matches the expected schema"""
    normalized = {
        "property": result.get("property", {}),
        "program": result.get("program", {}),
        "fees": result.get("fees", {}),
        "agenda": result.get("agenda", []),
        "policies": result.get("policies", {}),
        "concessions": result.get("concessions", []),
        "notes": result.get("notes"),
        "totals": result.get("totals", {}),
        "extras": result.get("extras", {})
    }
    
    # Ensure totals structure exists
    if "totals" not in normalized or not normalized["totals"]:
        normalized["totals"] = {
            "total_quote": {"status": "not_found", "value": None, "notes": None},
            "guestroom_total": {"status": "not_found", "value": None, "notes": None},
            "meeting_room_total": {"status": "not_found", "value": None, "notes": None},
            "fnb_total": {"status": "not_found", "value": None, "notes": None}
        }
    
    # Ensure extras structure exists
    if "extras" not in normalized or not normalized["extras"]:
        normalized["extras"] = {
            "room_nights": None,
            "nightly_rate": None,
            "guestroom_base": None,
            "guestroom_taxes_fees": None,
            "estimated_fnb_gross": None,
            "effective_value_offsets": [],
            "proposal_url": None
        }
    
    return normalized

def is_supported_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in {".pdf", ".html", ".htm", ".txt"}

def discover_inputs(input_path: Path) -> List[Path]:
    if input_path.is_file():
        if is_supported_file(input_path):
            return [input_path]
        raise FileNotFoundError(f"Unsupported file type: {input_path.suffix}")
    elif input_path.is_dir():
        return sorted([p for p in input_path.iterdir() if is_supported_file(p)])
    else:
        raise FileNotFoundError(f"Path not found: {input_path}")

def process_file(path: str, prompt_path: Optional[str], out_dir: str, model: str) -> Path:
    print(f"[+] Processing {path}")
    text = extract_text(path)
    text = _truncate(text)
    client = get_client()
    system_prompt = read_prompt(prompt_path)
    result = call_llm(client, model, system_prompt, text)

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / (Path(path).stem + ".json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"    -> {out_path}")
    return out_path

def main():
    ap = argparse.ArgumentParser(description="Extract hotel quote metadata from emails, PDFs, or HTML proposals.")
    ap.add_argument("--input", required=True, help="Path to a file or directory (.pdf, .html/.htm, .txt)")
    ap.add_argument("--out", required=True, help="Output directory for JSON")
    ap.add_argument("--prompt", default=None, help="Custom system prompt file (optional)")
    ap.add_argument("--model", default=None, help="OpenAI model (default from OPENAI_MODEL or gpt-4o-mini)")
    args = ap.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY not set")

    model = get_model(args.model)
    inputs = discover_inputs(Path(args.input))

    print(f"Model: {model}")
    print(f"Files: {len(inputs)}")
    for p in inputs:
        try:
            process_file(str(p), args.prompt, args.out, model)
        except Exception as e:
            print(f"[!] Failed on {p}: {e}")

if __name__ == "__main__":
    main()
