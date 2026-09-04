# predictionModels/services/models/herbert_engine.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import json
import unicodedata
import torch
import math

from transformers import AutoTokenizer, AutoModelForSequenceClassification

# === ŚCIEŻKA DO CHECKPOINTU (Twoja struktura katalogów) ===
MODEL_DIR = Path(__file__).resolve().parent / "her_bert" / "final_model"
# U Ciebie plik wygląda tak: {"classes": ["Choroba zakażna", "Dermatologia", ...]}
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.json"

# === KONFIG: DOKŁADNE NAZWY 2 ANKIET i KONKRETNE PYTANIA ===
ANKIETA_1 = "Pierwszy wywiad ogólny"
ANKIETA_2 = "Informacje dodatkowe"

# Dla każdej ankiety: lista pól w stałej kolejności.
# match po: "id" (int), "text" (pełny tekst), "contains" (fragment – nieczuły na znaki diakrytyczne).
HERBERT_INPUT_CONFIG: Dict[str, List[Dict[str, Any]]] = {
    ANKIETA_1: [
        {"key": "plec",                  "by": "contains", "match": "płeć"},
        {"key": "powod_wizyty",          "by": "contains", "match": "co skłoniło pana/panią do wizyty"},
        {"key": "od_kiedy",              "by": "contains", "match": "od kiedy występują objawy"},
        {"key": "nasilenie_zmiana",      "by": "contains", "match": "objawy ulegają zmianie lub nasileniu"},
        {"key": "choroby_przewlekle",    "by": "contains", "match": "choruje pan/pani przewlekle"},
        {"key": "rodzinne_ch_przewlekle","by": "contains", "match": "w rodzinie występowały choroby przewlekłe"},
    ],
    ANKIETA_2: [
        {"key": "wiek",       "by": "contains", "match": "wiek"},
        {"key": "waga_kg",    "by": "contains", "match": "waga"},
        {"key": "wzrost_cm",  "by": "contains", "match": "wzrost"},
        {"key": "grupa_krwi", "by": "contains", "match": "grupa krwi"},
        {"key": "rh",         "by": "contains", "match": "rh"},
        {"key": "alergie",    "by": "contains", "match": "alergie"},
    ],
}

# Format wejścia do modelu – dopasuj do tego, jak trenowałaś model:
FIELD_JOINER = " [SEP] "
FIELD_FORMAT = "{key}={val}"

# === Warstwa modelowa ===
_device = "cuda" if torch.cuda.is_available() else "cpu"
_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModelForSequenceClassification] = None

# surowe etykiety z configu modelu (np. "class_0", "class_1", ...)
_id2label: Dict[int, str] = {}
_label_order: List[str] = []  # stabilna kolejność id 0..N-1

# aliasy do wyświetlania: "class_2" -> "Neurologia" na bazie label_encoder.json["classes"]
_label_aliases: Dict[str, str] = {}


# ---------- mapowanie etykiet ----------

def _read_encoder_classes() -> List[str]:
    """
    Wczytuje listę ładnych nazw klas z label_encoder.json.
    Oczekiwany format:
      {"classes": ["Choroba zakażna", "Dermatologia", ...]}
    """
    try:
        with open(LABEL_ENCODER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("classes"), list):
            return [str(x) for x in data["classes"]]
    except Exception:
        pass
    return []


def _raw_label_for_idx(i: int) -> str:
    """Zwraca surową etykietę z configu modelu (np. 'class_2')."""
    if not _model:
        return f"class_{i}"
    cfg = getattr(_model, "config", None)
    if cfg is None:
        return f"class_{i}"
    # HuggingFace id2label może mieć klucze int lub stringi
    id2lab = getattr(cfg, "id2label", {}) or {}
    if isinstance(id2lab, dict):
        return str(id2lab.get(i) or id2lab.get(str(i)) or f"class_{i}")
    return f"class_{i}"


def _build_aliases_from_encoder() -> Dict[str, str]:
    """
    Buduje mapę aliasów: surowa_etykieta -> ładna_nazwa na bazie listy "classes".
    Zakładamy, że kolejność w 'classes' odpowiada id 0..N-1.
    """
    nice = _read_encoder_classes()
    if not nice:
        return {}
    aliases: Dict[str, str] = {}
    for i, pretty in enumerate(nice):
        raw = _raw_label_for_idx(i)  # np. "class_2"
        aliases[raw] = pretty        # np. "Neurologia"
    return aliases


def _ensure_loaded():
    global _tokenizer, _model, _id2label, _label_order, _label_aliases
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).to(_device)
        _model.eval()

        # surowe etykiety z configu modelu (mogą być "class_0" itd.)
        cfg_i2l = getattr(_model.config, "id2label", {}) or {}
        if isinstance(cfg_i2l, dict) and len(cfg_i2l) > 0:
            # zabezpieczenie na różne typy kluczy
            tmp = {}
            for k, v in cfg_i2l.items():
                try:
                    tmp[int(k)] = str(v)
                except Exception:
                    # czasem k jest już intem
                    tmp[int(k)] = str(v)
            _id2label = tmp
            _label_order = [tmp[i] for i in range(len(tmp))]
        else:
            # fallback, jeśli config nie zawiera id2label
            # (w praktyce rzadko)
            num_labels = getattr(_model.config, "num_labels", 0) or 0
            _id2label = {i: f"class_{i}" for i in range(num_labels)}
            _label_order = [f"class_{i}" for i in range(num_labels)]

        # aliasy do ładnych nazw z label_encoder.json["classes"]
        _label_aliases = _build_aliases_from_encoder()


def _alias(label_key: str) -> str:
    """Zwraca ładną nazwę dla surowej etykiety, jeśli jest alias; inaczej surową."""
    return _label_aliases.get(label_key, label_key)


# ---------- softmax + predykcja ----------

def _softmax(x: List[float]) -> List[float]:
    m = max(x)
    exps = [math.exp(v - m) for v in x]
    s = sum(exps)
    return [e / s for e in exps]


def predict_text(text: str, max_length: int = 512) -> Dict[str, Any]:
    """
    Zwraca:
      {
        'predicted_label': 'ładna_nazwa_top1',
        'classes': [{'label': 'ładna_nazwa', 'prob': 0.73, 'percent': 73.0}, ...]
      }
    """
    _ensure_loaded()
    enc = _tokenizer(
        text,
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors="pt"
    ).to(_device)
    with torch.no_grad():
        logits = _model(**enc).logits.detach().cpu().tolist()[0]
    probs = _softmax(logits)  # w kolejności id 0..N-1

    classes = []
    for i, p in enumerate(probs):
        raw_label = _id2label.get(i, f"class_{i}")
        pretty = _alias(raw_label)
        classes.append({"label": pretty, "prob": float(p), "percent": float(p * 100.0)})

    top = max(classes, key=lambda d: d["prob"])
    return {"predicted_label": top["label"], "classes": classes}


# ---------- Ekstrakcja danych z ankiet ----------

def _norm(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def _answer_to_text(answer) -> str:
    q = getattr(answer, "question", None)
    qtype = getattr(q, "question_type", None)
    if qtype == "text":
        return (getattr(answer, "text_answer", None) or getattr(answer, "value", None) or "").strip()
    elif qtype == "single_choice":
        try:
            ch = answer.selected_choices.first()
            return (getattr(ch, "text", "") or "").strip()
        except Exception:
            return ""
    elif qtype == "multiple_choice":
        try:
            return ", ".join([(getattr(c, "text", "") or "").strip() for c in answer.selected_choices.all()])
        except Exception:
            return ""
    return (getattr(answer, "text_answer", None) or getattr(answer, "value", None) or "").strip()


def _match_question(cfg: Dict[str, Any], question) -> bool:
    by = (cfg.get("by") or "id").lower()
    match = cfg.get("match")
    if by == "id":
        try:
            return getattr(question, "id", None) == int(match)
        except Exception:
            return False
    qt = _norm(getattr(question, "text", None) or getattr(question, "title", None) or getattr(question, "label", None) or "")
    mm = _norm(str(match))
    if by == "text":
        return qt == mm
    if by == "contains":
        return mm in qt
    return False


def _extract_from_one_survey(survey_req, conf: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {c["key"]: "" for c in conf}
    resp = getattr(survey_req, "response", None)
    if not resp:
        return out
    try:
        answers = resp.answers.select_related("question").prefetch_related("selected_choices")
    except Exception:
        answers = getattr(resp, "answers", [])

    ans_by_q = list(answers)
    for cfg in conf:
        key = cfg["key"]
        for a in ans_by_q:
            if _match_question(cfg, a.question):
                out[key] = _answer_to_text(a)
                break
    return out


def build_payload_from_surveys(surveys: List[Any]) -> Tuple[str, Dict[str, Dict[str, str]]]:
    """
    Przyjmuje listę SentQuestionnaireRequest. Filtruje TYLKO dwie dozwolone ankiety
    i TYLKO wskazane pytania. Zwraca:
      - tekst wejściowy dla HerBERT-a,
      - raport co wykorzystano: {ankieta: {key: val, ...}}
    """
    by_name: Dict[str, List[Any]] = {}
    for s in surveys:
        qname = getattr(getattr(s, "questionnaire", None), "name", None)
        if not qname:
            continue
        by_name.setdefault(qname, []).append(s)

    used: Dict[str, Dict[str, str]] = {}
    fields_linear: List[str] = []

    for aname, conf in HERBERT_INPUT_CONFIG.items():
        reqs = by_name.get(aname) or []
        if not reqs:
            continue
        s = sorted(
            reqs,
            key=lambda r: getattr(r, "filled_at", getattr(r, "sent_at", None)) or 0,
            reverse=True
        )[0]
        kv = _extract_from_one_survey(s, conf)
        used[aname] = kv
        for c in conf:
            v = (kv.get(c["key"], "") or "").strip()
            fields_linear.append(FIELD_FORMAT.format(key=c["key"], val=v if v != "" else "none"))

    if not fields_linear:
        raise ValueError("Brak wymaganych ankiet/pól do zbudowania wejścia dla HerBERT-a.")

    payload_text = FIELD_JOINER.join(fields_linear)
    return payload_text, used


def predict_from_surveys(surveys: List[Any]) -> Dict[str, Any]:
    """
    Helper łączący ekstrakcję + inferencję.
    Zwraca:
      {
        'predicted_label': '...'(ładna nazwa),
        'classes': [{'label':..., 'prob':..., 'percent':...}, ...],
        'raw_features': {ankieta: {key: val}},
        'raw_payload': 'wiek=... [SEP] ...'
      }
    """
    payload_text, used_map = build_payload_from_surveys(surveys)
    pred = predict_text(payload_text, max_length=512)
    out = {
        "predicted_label": pred["predicted_label"],
        "classes": pred["classes"],
        "raw_features": used_map,
        "raw_payload": payload_text
    }
    return out
