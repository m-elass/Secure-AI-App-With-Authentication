"""
Ingesta de PDFs → corpus de fragmentos para el generador de preguntas.

CÓMO USAR
─────────
Coloca los PDFs en backend/materials/<subject>/ y luego ejecuta:

    cd backend
    python scripts/ingest_pdfs.py

Esto produce backend/materials/<subject>_corpus.json, que el generador
de IA carga al arrancar.

ESTRUCTURA ESPERADA
───────────────────
backend/
├── materials/
│   ├── per/
│   │   ├── http.pdf
│   │   ├── sockets.pdf
│   │   ├── Introducción_a_JSON.pdf
│   │   └── ...
│   └── biochem/
│       ├── Tema_14__Replicacion.pdf
│       ├── Tema_15__Transcripción.pdf
│       ├── Tema_16__Traducción.pdf
│       ├── Tema_17__Regulación.pdf
│       └── Tema_18__Ingeniería_Genética.pdf
└── scripts/
    └── ingest_pdfs.py

DEPENDENCIAS
────────────
    pip install pypdf

(pypdf es estándar, pequeño y sin dependencias C; ya viene en muchos
entornos. Si quisieras OCR para PDFs escaneados habría que añadir
tesseract, pero tus PDFs son texto.)

DETALLES TÉCNICOS
─────────────────
- Cada PDF se trocea en CHUNKS de ~500 palabras con solape de 50 palabras
  para que ningún concepto quede partido por la mitad.
- Cada chunk lleva metadata: nombre del archivo y página(s) origen.
- Los chunks vacíos o muy cortos (< 80 palabras tras limpiar) se descartan.
- Las cabeceras/pies repetidos (autor, copyright, números de página
  aislados) se filtran heurísticamente.
"""
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    from pypdf import PdfReader
except ImportError:
    print("ERROR: necesitas instalar pypdf → pip install pypdf")
    sys.exit(1)

# python-pptx es opcional: solo se usa si detectamos que un .pdf es en
# realidad un .pptx renombrado (cabecera ZIP). Si no está instalado y hay
# pptx, mostramos un aviso pero seguimos.
try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False


# ─── Configuración ─────────────────────────────────────────────────────────
CHUNK_WORDS = 500          # tamaño objetivo de cada fragmento
OVERLAP_WORDS = 50         # solape entre fragmentos contiguos
MIN_CHUNK_WORDS = 80       # fragmentos por debajo de esto se descartan

# Líneas-basura a filtrar (cabeceras y pies repetidos típicos):
NOISE_PATTERNS = [
    re.compile(r"^Ángela Martín Cortés\.?\s*Área de Bioquímica.*", re.I),
    re.compile(r"^Universidad Rey Juan Carlos$", re.I),
    re.compile(r"^FCS\.\s*\d{4}-\d{2}$", re.I),
    re.compile(r"^\d{1,3}$"),                      # números de página sueltos
    re.compile(r"^Página \d+ de \d+$", re.I),
    re.compile(r"^https?://\S+$"),                 # URLs aisladas
]


def clean_text(raw: str) -> str:
    """Limpia el texto extraído del PDF."""
    lines = raw.split("\n")
    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(p.match(stripped) for p in NOISE_PATTERNS):
            continue
        kept.append(stripped)
    text = " ".join(kept)
    # Colapsar espacios múltiples
    text = re.sub(r"\s+", " ", text)
    # Arreglar guiones de fin de línea que parten palabras: "trans-cripción" → "transcripción"
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return text.strip()


def chunk_words(words: List[str], size: int, overlap: int) -> List[List[str]]:
    """Trocea una lista de palabras en chunks con solape."""
    if not words:
        return []
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        chunk = words[i:i + size]
        if len(chunk) >= MIN_CHUNK_WORDS:
            chunks.append(chunk)
        i += size - overlap
    return chunks


def _file_magic(path: Path) -> str:
    """Detecta el formato REAL del archivo por su cabecera, no por la extensión."""
    with open(path, "rb") as f:
        head = f.read(4)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        return "zip"  # podría ser pptx, docx, xlsx...
    return "unknown"


def process_zip_with_txt(path: Path) -> List[Dict[str, Any]]:
    """Algunos PDFs subidos a proyectos se almacenan como ZIP con .jpeg
    (cada slide como imagen) + .txt (texto OCR de cada slide).
    Aprovechamos los .txt para extraer texto."""
    import zipfile
    try:
        with zipfile.ZipFile(path) as z:
            txt_names = sorted(
                [n for n in z.namelist() if n.lower().endswith(".txt")],
                key=lambda n: (len(n), n)  # 1.txt antes que 10.txt
            )
            if not txt_names:
                print(f"[saltado: ZIP sin .txt OCR]")
                return []

            slides_text = []
            for name in txt_names:
                try:
                    raw = z.read(name).decode("utf-8", errors="ignore")
                except Exception:
                    continue
                cleaned = clean_text(raw)
                if cleaned:
                    slides_text.append(cleaned)
    except Exception as e:
        print(f"[ERROR al leer ZIP: {e}]")
        return []

    all_words = []
    page_breaks = []
    for slide_num, text in enumerate(slides_text, start=1):
        page_breaks.append((len(all_words), slide_num))
        all_words.extend(text.split())

    if len(all_words) < MIN_CHUNK_WORDS:
        print(f"[saltado: solo {len(all_words)} palabras]")
        return []

    word_chunks = chunk_words(all_words, CHUNK_WORDS, OVERLAP_WORDS)
    out = []
    for chunk_idx, words in enumerate(word_chunks):
        start_word_idx = chunk_idx * (CHUNK_WORDS - OVERLAP_WORDS)
        slide = 1
        for break_idx, p in page_breaks:
            if break_idx <= start_word_idx:
                slide = p
            else:
                break
        out.append({
            "source": path.name,
            "page_start": slide,
            "text": " ".join(words),
        })

    print(f"(zip-ocr) → {len(out)} fragmentos")
    return out


def process_pptx(path: Path) -> List[Dict[str, Any]]:
    """Extrae texto de un .pptx (o .pdf que en realidad es .pptx)."""
    if not HAS_PPTX:
        print("[saltado: instala python-pptx para procesar este archivo]")
        return []

    try:
        pres = Presentation(str(path))
    except Exception:
        # No es realmente un pptx; el caller lo manejará con otra estrategia.
        return []

    all_words = []
    page_breaks = []
    for slide_num, slide in enumerate(pres.slides, start=1):
        slide_text = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = "".join(run.text for run in para.runs).strip()
                    if line:
                        slide_text.append(line)
            # Tablas en diapositivas
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            slide_text.append(t)

        text = clean_text("\n".join(slide_text))
        if not text:
            continue
        page_breaks.append((len(all_words), slide_num))
        all_words.extend(text.split())

    if len(all_words) < MIN_CHUNK_WORDS:
        print(f"[saltado: solo {len(all_words)} palabras]")
        return []

    word_chunks = chunk_words(all_words, CHUNK_WORDS, OVERLAP_WORDS)
    out = []
    for chunk_idx, words in enumerate(word_chunks):
        start_word_idx = chunk_idx * (CHUNK_WORDS - OVERLAP_WORDS)
        slide = 1
        for break_idx, p in page_breaks:
            if break_idx <= start_word_idx:
                slide = p
            else:
                break
        out.append({
            "source": path.name,
            "page_start": slide,
            "text": " ".join(words),
        })

    print(f"(pptx) → {len(out)} fragmentos")
    return out


def process_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extrae texto del PDF y lo devuelve troceado.

    Si detecta que el archivo .pdf es en realidad un .pptx renombrado
    (cabecera ZIP en lugar de %PDF), delega en process_pptx.
    """
    print(f"  · {pdf_path.name}", end=" ", flush=True)

    magic = _file_magic(pdf_path)
    if magic == "zip":
        # Puede ser pptx O un ZIP con .txt OCR (formato típico de proyectos
        # Anthropic). Probamos pptx primero, si falla, ZIP-OCR.
        result = process_pptx(pdf_path)
        if result:
            return result
        return process_zip_with_txt(pdf_path)
    if magic != "pdf":
        print(f"[saltado: formato no reconocido ({magic})]")
        return []

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as e:
        print(f"[ERROR al abrir: {e}]")
        return []

    # Concatenamos todo el texto del PDF y guardamos por qué página
    # va cada palabra para poder citar la página origen.
    all_words = []
    page_breaks = []  # índice de palabra donde empieza cada página
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        text = clean_text(raw)
        if not text:
            continue
        page_breaks.append((len(all_words), page_num))
        all_words.extend(text.split())

    if len(all_words) < MIN_CHUNK_WORDS:
        print(f"[saltado: solo {len(all_words)} palabras]")
        return []

    word_chunks = chunk_words(all_words, CHUNK_WORDS, OVERLAP_WORDS)

    out = []
    for chunk_idx, words in enumerate(word_chunks):
        # Determinar página de inicio buscando en page_breaks
        start_word_idx = chunk_idx * (CHUNK_WORDS - OVERLAP_WORDS)
        page = 1
        for break_idx, p in page_breaks:
            if break_idx <= start_word_idx:
                page = p
            else:
                break
        out.append({
            "source": pdf_path.name,
            "page_start": page,
            "text": " ".join(words),
        })

    print(f"→ {len(out)} fragmentos")
    return out


def ingest_subject(subject_dir: Path) -> List[Dict[str, Any]]:
    """Procesa todos los PDF/PPTX de un directorio de asignatura."""
    files = sorted(
        list(subject_dir.glob("*.pdf")) +
        list(subject_dir.glob("*.PDF")) +
        list(subject_dir.glob("*.pptx"))
    )
    if not files:
        print(f"  (no hay PDFs ni PPTX en {subject_dir})")
        return []

    all_fragments = []
    for f in files:
        if f.suffix.lower() == ".pptx":
            print(f"  · {f.name}", end=" ", flush=True)
            all_fragments.extend(process_pptx(f))
        else:
            all_fragments.extend(process_pdf(f))
    return all_fragments


def main():
    root = Path(__file__).resolve().parent.parent
    materials = root / "materials"

    if not materials.exists():
        print(f"ERROR: no existe {materials}")
        print("Crea backend/materials/per/ y backend/materials/biochem/ "
              "y coloca dentro los PDFs.")
        sys.exit(1)

    subjects = [d for d in materials.iterdir() if d.is_dir()]
    if not subjects:
        print(f"ERROR: no hay subcarpetas en {materials}")
        sys.exit(1)

    for subject_dir in sorted(subjects):
        subject = subject_dir.name
        print(f"\n📚 Procesando asignatura: {subject}")
        fragments = ingest_subject(subject_dir)

        if not fragments:
            print(f"  ⚠ Sin fragmentos para {subject}, saltando.")
            continue

        out_path = materials / f"{subject}_corpus.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "subject": subject,
                "fragment_count": len(fragments),
                "fragments": fragments,
            }, f, ensure_ascii=False, indent=2)

        total_words = sum(len(fr["text"].split()) for fr in fragments)
        print(f"  ✓ {len(fragments)} fragmentos · {total_words:,} palabras → {out_path.name}")

    print("\n✓ Ingesta completada.")


if __name__ == "__main__":
    main()