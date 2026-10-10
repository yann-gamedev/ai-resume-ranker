"""Create multilingual text embeddings for resume ranking."""

from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def get_embedding(text: str):
    """Return the model's vector embedding for one text."""
    return _model.encode(text)

