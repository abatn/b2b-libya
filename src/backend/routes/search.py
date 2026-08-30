"""
Libya B2B Platform - Search Routes
Fuzzy full-text search with scoring.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import get_db
from models import Product, Supplier

router = APIRouter(prefix="/api/search", tags=["search"])


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Simple Levenshtein distance-based similarity ratio (0-1)."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + cost,
            )
    dist = matrix[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (dist / max_len)


def _fuzzy_score(query: str, text: str) -> float:
    """Score how well query matches text. Exact > contains > fuzzy."""
    if not text:
        return 0.0
    q = query.lower()
    t = text.lower()
    # Exact match
    if q == t:
        return 1.0
    # Starts with
    if t.startswith(q):
        return 0.95
    # Contains
    if q in t:
        return 0.85
    # Word-level contains
    q_words = q.split()
    t_words = t.split()
    word_hits = sum(1 for w in q_words if any(w in tw for tw in t_words))
    if word_hits > 0:
        return 0.7 + 0.15 * (word_hits / len(q_words))
    # Fuzzy per word
    best = 0.0
    for qw in q_words:
        for tw in t_words:
            ratio = _levenshtein_ratio(qw, tw)
            if ratio > best:
                best = ratio
    return best * 0.6  # Scale down fuzzy matches


def _fts5_product_search(q: str, limit: int, db) -> list:
    """FTS5 product search with fuzzy fallback."""
    from sqlalchemy import text as sql_text

    if not q.strip():
        return []
    try:
        with db.get_bind().connect() as conn:
            # Try exact FTS5 match first
            rows = conn.execute(
                sql_text(
                    """SELECT p.id, p.name, p.name_arabic, p.price, p.currency,
                              p.category, p.image_url, p.moq, p.stock_quantity,
                              rank
                       FROM products_fts fts
                       JOIN products p ON p.id = fts.rowid
                       WHERE products_fts MATCH :query AND p.is_active = 1
                       ORDER BY rank
                       LIMIT :limit"""
                ),
                {"query": f'"{q}"*', "limit": limit},
            ).fetchall()
            if rows:
                return [
                    {
                        "type": "product",
                        "id": r[0],
                        "name": r[1],
                        "name_arabic": r[2],
                        "price": r[3],
                        "currency": r[4],
                        "category": r[5],
                        "image_url": r[6],
                        "moq": r[7],
                        "stock_quantity": r[8],
                        "score": round(abs(r[9]), 3) if r[9] else 1.0,
                        "source": "fts5",
                    }
                    for r in rows
                ]
    except Exception:
        pass
    # Fallback: ILIKE (fast enough for 312 products)
    try:
        products = (
            db.query(Product)
            .filter(Product.is_active)
            .filter(Product.name.ilike(f"%{q}%") | Product.name_arabic.ilike(f"%{q}%"))
            .limit(limit)
            .all()
        )
        if products:
            return [
                {
                    "type": "product",
                    "id": p.id,
                    "name": p.name,
                    "name_arabic": p.name_arabic,
                    "price": p.price,
                    "currency": p.currency,
                    "category": p.category,
                    "image_url": p.image_url,
                    "moq": p.moq,
                    "stock_quantity": p.stock_quantity,
                    "score": 0.8,
                    "source": "ilike",
                }
                for p in products
            ]
    except Exception:
        pass
    return []


@router.get("")
def full_text_search(
    q: str = "",
    type: Optional[str] = "all",  # all | products | suppliers
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Full-text search: FTS5 for products, Fuzzy for suppliers."""
    results = []

    if type in ("all", "products"):
        # Try FTS5 first (fast), fall back to Python fuzzy (slow)
        fts_results = _fts5_product_search(q, limit, db)
        if fts_results:
            results.extend(fts_results)
        else:
            products = db.query(Product).filter(Product.is_active).all()
            for p in products:
                scores = [
                    _fuzzy_score(q, p.name or "") * 1.0,
                    _fuzzy_score(q, p.name_arabic or "") * 0.9,
                    _fuzzy_score(q, p.description or "") * 0.6,
                    _fuzzy_score(q, p.category or "") * 0.5,
                ]
                score = max(scores)
                if score > 0.3:
                    results.append(
                        {
                            "type": "product",
                            "id": p.id,
                            "name": p.name,
                            "name_arabic": p.name_arabic,
                            "price": p.price,
                            "currency": p.currency,
                            "category": p.category,
                            "image_url": p.image_url,
                            "score": round(score, 3),
                        }
                    )

    if type in ("all", "suppliers"):
        suppliers = db.query(Supplier).all()
        for s in suppliers:
            scores = [
                _fuzzy_score(q, s.name or "") * 1.0,
                _fuzzy_score(q, s.name_arabic or "") * 0.9,
                _fuzzy_score(q, s.description or "") * 0.5,
                _fuzzy_score(q, s.location or "") * 0.4,
            ]
            score = max(scores)
            if score > 0.3:
                results.append(
                    {
                        "type": "supplier",
                        "id": s.id,
                        "name": s.name,
                        "name_arabic": s.name_arabic,
                        "location": s.location,
                        "rating": s.rating,
                        "score": round(score, 3),
                    }
                )

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"query": q, "results": results[:limit], "total": len(results)}


# ============================================================
# SYNONYM DICTIONARY (EN↔AR, B2B-relevant terms)
# ============================================================

SYNONYMS = {
    # Electronics
    "laptop": ["notebook", "computer", "حاسوب"],
    "notebook": ["laptop", "computer", "حاسوب"],
    "cable": ["wire", "اسلاك", "kabel"],
    "wire": ["cable", "اسلاك", "kabel"],
    "cables": ["wires", "اسلاك"],
    "wires": ["cables", "اسلاك"],
    # Construction
    "cement": ["اسمنت", "concrete", "خرسانة"],
    "steel": ["حديد", "rebar", "تسليح"],
    "rebar": ["steel", "حديد", "تسليح"],
    "tiles": ["بلاط", "ceramic", "سيراميك"],
    "ceramic": ["tiles", "بلاط", "سيراميك"],
    "wood": ["خشب", "timber", "lumber"],
    "timber": ["wood", "خشب"],
    "sand": ["رمل", "aggregate"],
    # Hardware
    "drill": ["ثفانة", "borer"],
    "grinder": ["كشطة", "cutter"],
    "wrench": ["مفتاح ربط", "spanner"],
    "screw": ["برغي", "bolt"],
    "bolt": ["برغي", "screw"],
    "lock": ["قفل", "key"],
    # Machinery
    "pump": ["مضخة", "compressor"],
    "compressor": ["ضاغط", "pump"],
    "welder": ["جهاز لحام", "welding"],
    "generator": ["مولدة", "power"],
    # Safety
    "helmet": ["خوذة", "hard hat"],
    "gloves": ["قفازات"],
    "fire extinguisher": ["طفاية", "طفايات"],
    # Lighting
    "led": ["انارة", "light"],
    "light": ["انارة", "led"],
    # Plumbing
    "pipe": ["أنبوب", "tube", "انابيب"],
    "pipes": ["أنابيب", "tubes", "انابيب"],
    "valve": ["صمام"],
    "faucet": ["صنبور", "tap"],
    # Food
    "rice": ["ارز"],
    "flour": ["دقيق"],
    "oil": ["زيت"],
    # IT
    "computer": ["حاسوب", "pc", "laptop"],
    "printer": ["طابعة"],
    "router": ["راوتر", "network"],
    "server": ["سيرفر"],
    # General B2B
    "wholesale": ["جملة", "bulk"],
    "bulk": ["جملة", "wholesale"],
    "price": ["سعر", "cost"],
    "moq": ["minimum order", "اقل كمية"],
    "delivery": ["توصيل", "shipping", "شحن"],
    "shipping": ["توصيل", "delivery", "شحن"],
}


# Build reverse map: term → list of synonyms
_SYNONYM_INDEX: dict[str, list[str]] = {}
for _term, _syns in SYNONYMS.items():
    _SYNONYM_INDEX.setdefault(_term.lower(), [])
    for _s in _syns:
        _SYNONYM_INDEX.setdefault(_term.lower(), []).append(_s.lower())
        _SYNONYM_INDEX.setdefault(_s.lower(), []).append(_term.lower())


def _expand_query(q: str) -> list[str]:
    """Expand search query with synonyms."""
    terms = q.lower().split()
    expanded = [q.lower()]
    for t in terms:
        if t in _SYNONYM_INDEX:
            for syn in _SYNONYM_INDEX[t]:
                if syn not in expanded:
                    expanded.append(syn)
    return expanded


def _normalize_arabic(text: str) -> str:
    """Normalize Arabic text: remove diacritics, normalize Alef/Ya variants."""
    import re

    # Remove Tashkeel (diacritics)
    text = re.sub(r"[\u0617-\u061A\u064B-\u0652]", "", text)
    # Normalize Alef variants → Alef
    text = text.replace("إ", "ا").replace("أ", "ا").replace("آ", "ا")
    # Normalize Ya → Alef Maqsura
    text = text.replace("ى", "ي")
    # Normalize Ta Marbuta → Ha
    text = text.replace("ة", "ه")
    return text


# ============================================================
# AUTOCOMPLETE ENDPOINT
# ============================================================


@router.get("/autocomplete")
def autocomplete(
    q: str = "",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Typeahead autocomplete for products and suppliers."""
    if len(q) < 2:
        return {"suggestions": []}

    # Expand with synonyms
    expanded = _expand_query(q)

    suggestions = []
    seen = set()

    # Search products
    for term in expanded:
        products = (
            db.query(Product)
            .filter(Product.is_active)
            .filter(
                (Product.name.ilike(f"%{term}%"))
                | (Product.name_arabic.ilike(f"%{_normalize_arabic(term)}%"))
            )
            .limit(limit)
            .all()
        )
        for p in products:
            if p.id not in seen:
                seen.add(p.id)
                suggestions.append(
                    {
                        "type": "product",
                        "id": p.id,
                        "name": p.name,
                        "name_arabic": p.name_arabic,
                        "category": p.category,
                        "price": p.price,
                    }
                )

    # Search suppliers
    for term in expanded:
        suppliers = (
            db.query(Supplier)
            .filter(
                (Supplier.name.ilike(f"%{term}%"))
                | (Supplier.name_arabic.ilike(f"%{_normalize_arabic(term)}%"))
            )
            .limit(limit)
            .all()
        )
        for s in suppliers:
            if s.id not in seen:
                seen.add(s.id)
                suggestions.append(
                    {
                        "type": "supplier",
                        "id": s.id,
                        "name": s.name,
                        "name_arabic": s.name_arabic,
                        "category": s.category,
                    }
                )

    return {"suggestions": suggestions[:limit], "query": q}


@router.get("/fts")
def fts_search(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    """FTS5-powered full-text search (faster than ILIKE for large datasets)."""

    from sqlalchemy import text as sql_text

    if not q.strip():
        return {"results": [], "query": q}

    # Try FTS5 search first
    try:
        with db.get_bind().connect() as conn:
            # FTS5 query with fallback to ILIKE
            rows = conn.execute(
                sql_text(
                    """SELECT p.id, p.name, p.name_arabic, p.price, p.category,
                              p.image_url, p.moq, p.stock_quantity,
                              rank
                   FROM products_fts fts
                   JOIN products p ON p.id = fts.rowid
                   WHERE products_fts MATCH :query AND p.is_active = 1
                   ORDER BY rank
                   LIMIT :limit"""
                ),
                {"query": f'"{q}"*', "limit": limit},
            ).fetchall()

            if rows:
                results = []
                for r in rows:
                    results.append(
                        {
                            "id": r[0],
                            "name": r[1],
                            "name_arabic": r[2],
                            "price": r[3],
                            "category": r[4],
                            "image_url": r[5],
                            "moq": r[6],
                            "stock_quantity": r[7],
                            "type": "product",
                            "source": "fts5",
                        }
                    )
                return {"results": results, "query": q, "source": "fts5"}
    except Exception:
        pass  # Fallback to ILIKE

    # Fallback: ILIKE search
    products = (
        db.query(Product)
        .filter(
            Product.is_active,
            (Product.name.ilike(f"%{q}%"))
            | (Product.name_arabic.ilike(f"%{q}%"))
            | (Product.category.ilike(f"%{q}%")),
        )
        .limit(limit)
        .all()
    )
    results = [
        {
            "id": p.id,
            "name": p.name,
            "name_arabic": p.name_arabic,
            "price": p.price,
            "category": p.category,
            "image_url": p.image_url,
            "moq": p.moq,
            "stock_quantity": p.stock_quantity,
            "type": "product",
            "source": "ilike",
        }
        for p in products
    ]
    return {"results": results, "query": q, "source": "ilike"}
