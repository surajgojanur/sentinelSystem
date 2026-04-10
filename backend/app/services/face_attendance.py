import base64
import hashlib
import io

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.random_projection import GaussianRandomProjection

from app.models.face_profile import FaceProfile

IMAGE_SIZE = (64, 64)
EMBEDDING_SIZE = 256
MATCH_THRESHOLD = 0.84

_PROJECTOR = GaussianRandomProjection(n_components=EMBEDDING_SIZE, random_state=42)
_PROJECTOR_FITTED = False


def _decode_image_bytes(image_payload: str) -> bytes:
    if not image_payload:
        raise ValueError("Image payload is required")

    payload = image_payload.strip()
    if "," in payload and payload.startswith("data:image"):
        payload = payload.split(",", 1)[1]

    try:
        return base64.b64decode(payload, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid base64 image payload") from exc


def _preprocess_image(raw_bytes: bytes) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("Pillow is required for image decoding. Install backend dependencies first.") from exc

    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("L").resize(IMAGE_SIZE)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Unsupported image format") from exc

    array = np.asarray(image, dtype=np.float32) / 255.0
    flat = array.reshape(-1)
    centered = flat - np.mean(flat)
    norm = np.linalg.norm(centered)
    if norm == 0:
        raise ValueError("Image contains insufficient signal for recognition")
    return centered / norm


def _embed_vector(normalized_flattened: np.ndarray) -> np.ndarray:
    global _PROJECTOR_FITTED
    sample = normalized_flattened.reshape(1, -1)
    if not _PROJECTOR_FITTED:
        _PROJECTOR.fit(sample)
        _PROJECTOR_FITTED = True
    projected = _PROJECTOR.transform(sample)[0].astype(np.float32)
    proj_norm = np.linalg.norm(projected)
    if proj_norm == 0:
        raise ValueError("Failed to generate stable embedding")
    return projected / proj_norm


def build_face_embedding(image_payload: str) -> tuple[np.ndarray, str]:
    raw = _decode_image_bytes(image_payload)
    normalized = _preprocess_image(raw)
    embedding = _embed_vector(normalized)
    sample_hash = hashlib.sha256(raw).hexdigest()
    return embedding, sample_hash


def match_face(image_payload: str, threshold: float = MATCH_THRESHOLD):
    probe_embedding, _ = build_face_embedding(image_payload)
    profiles = FaceProfile.query.all()
    if not profiles:
        return None, 0.0

    best_profile = None
    best_score = -1.0

    for profile in profiles:
        known = profile.get_embedding()
        score = float(cosine_similarity(probe_embedding.reshape(1, -1), known.reshape(1, -1))[0][0])
        if score > best_score:
            best_score = score
            best_profile = profile

    if best_profile is None or best_score < threshold:
        return None, max(best_score, 0.0)
    return best_profile, best_score
