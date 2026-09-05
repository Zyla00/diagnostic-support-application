# import os
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
#
# # ŚCIEŻKA do lokalnego katalogu z modelem/tokenizerem (zmień jeśli trzeba)
# MODEL_PATH = os.getenv("MISTRAL_MODEL_PATH", ".\predictionModels\services\models\mistral\mistral_model")
#
# # Wymuszamy offline (nic nie będzie pobierane z sieci)
# os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
#
# _tokenizer = None
# _model = None
#
# def _device():
#     if torch.cuda.is_available():
#         return "cuda"
#     if torch.backends.mps.is_available():
#         return "mps"
#     return "cpu"
#
# def load_mistral():
#     global _tokenizer, _model
#     if _tokenizer is not None and _model is not None:
#         return _tokenizer, _model
#
#     device = _device()
#
#     _tokenizer = AutoTokenizer.from_pretrained(
#         MODEL_PATH,
#         local_files_only=True,
#         use_fast=True,
#     )
#     if _tokenizer.pad_token is None:
#         _tokenizer.pad_token = _tokenizer.eos_token
#
#     # Spróbuj int8 na CUDA, w innym wypadku fp16/fp32
#     tried_8bit = False
#     if device == "cuda":
#         try:
#             bnb = BitsAndBytesConfig(load_in_8bit=True, llm_int8_threshold=6.0)
#             _model = AutoModelForCausalLM.from_pretrained(
#                 MODEL_PATH, quantization_config=bnb, device_map="auto",
#                 local_files_only=True,
#             )
#             tried_8bit = True
#         except Exception:
#             _model = None
#
#     if _model is None:
#         dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
#         _model = AutoModelForCausalLM.from_pretrained(
#             MODEL_PATH, torch_dtype=dtype, local_files_only=True
#         )
#         _model.to(device)
#
#     try:
#         _model = torch.compile(_model)  # możesz usunąć, jeśli sprawia kłopoty
#     except Exception:
#         pass
#
#     print(f"[Mistral] loaded from {MODEL_PATH} on {device} (int8={tried_8bit})")
#     return _tokenizer, _model
#
#
# @torch.inference_mode()
# def generate_text(prompt: str, max_new_tokens: int = 400) -> str:
#     tok, model = load_mistral()
#     enc = tok(prompt, return_tensors="pt", truncation=True, max_length=4096)
#     input_ids = enc["input_ids"].to(model.device)
#     attn = enc.get("attention_mask")
#     if attn is not None:
#         attn = attn.to(model.device)
#
#     out = model.generate(
#         input_ids=input_ids,
#         attention_mask=attn,
#         max_new_tokens=max_new_tokens,
#         do_sample=True,
#         temperature=0.7,
#         top_k=50,
#         top_p=0.95,
#         repetition_penalty=1.15,
#         pad_token_id=tok.eos_token_id,
#         eos_token_id=tok.eos_token_id,
#     )
#     text = tok.decode(out[0], skip_special_tokens=True)
#     if text.startswith(prompt):
#         text = text[len(prompt):].lstrip()
#     return text


import os
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Nie pobieraj nic z sieci – działamy tylko na lokalnych plikach
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_tokenizer = None
_model = None


def _device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _resolve_model_dir() -> Path:
    """
    Ustal katalog z modelem:
    - jeśli ustawiono MISTRAL_MODEL_PATH → użyj go (relative wobec tego pliku, jeśli ścieżka nie jest absolutna),
    - inaczej: domyślnie ../mistral/mistral_model obok tego pliku.
    """
    base = Path(__file__).resolve().parent  # .../predictionModels/services/models
    env = (os.getenv("MISTRAL_MODEL_PATH") or "").strip()

    if env:
        p = Path(env).expanduser()
        if not p.is_absolute():
            p = (base / p).resolve()
        return p

    # domyślnie: models/mistral/mistral_model (obok tego pliku)
    return (base / "mistral" / "mistral_model").resolve()


MODEL_DIR = _resolve_model_dir()
if not MODEL_DIR.exists():
    raise FileNotFoundError(
        f"[Mistral] Nie znaleziono katalogu modelu: {MODEL_DIR}\n"
        f"Ustaw zmienną środowiskową MISTRAL_MODEL_PATH albo skopiuj model do tego katalogu."
    )


def load_mistral():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model

    device = _device()
    model_path = str(MODEL_DIR)

    _tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True,
        use_fast=True,
    )
    if _tokenizer.pad_token is None:
        # większość modeli ma eos_token; jeśli nie, możesz ustawić np. "<pad>"
        _tokenizer.pad_token = _tokenizer.eos_token

    # Spróbuj INT8 na CUDA; w innym przypadku fp16/fp32
    tried_8bit = False
    if device == "cuda":
        try:
            bnb = BitsAndBytesConfig(load_in_8bit=True, llm_int8_threshold=6.0)
            _model = AutoModelForCausalLM.from_pretrained(
                model_path,
                quantization_config=bnb,
                device_map="auto",
                local_files_only=True,
            )
            tried_8bit = True
        except Exception:
            _model = None

    if _model is None:
        dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
        _model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            local_files_only=True,
        )
        _model.to(device)

    try:
        _model = torch.compile(_model)  # opcjonalnie; usuń jeśli sprawia kłopoty
    except Exception:
        pass

    print(f"[Mistral] loaded from {MODEL_DIR} on {device} (int8={tried_8bit})")
    return _tokenizer, _model


@torch.inference_mode()
def generate_text(prompt: str, max_new_tokens: int = 400) -> str:
    tok, model = load_mistral()
    enc = tok(prompt, return_tensors="pt", truncation=True, max_length=4096)
    input_ids = enc["input_ids"].to(model.device)
    attn = enc.get("attention_mask")
    if attn is not None:
        attn = attn.to(model.device)

    out = model.generate(
        input_ids=input_ids,
        attention_mask=attn,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_k=50,
        top_p=0.95,
        repetition_penalty=1.15,
        pad_token_id=tok.eos_token_id,
        eos_token_id=tok.eos_token_id,
    )
    text = tok.decode(out[0], skip_special_tokens=True)
    if text.startswith(prompt):
        text = text[len(prompt):].lstrip()
    return text
