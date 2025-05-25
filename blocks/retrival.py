# retrieval_rerank_functions.py
"""
Defines two helper functions:
1. retrieve_and_rerank(): loads indexes and BM25, encodes a query (image/text), retrieves top-K, reranks, and returns ranked indices and metadata.
2. rerank_only(indices): given initial retrieval indices and scores, applies reranking and returns refined ranked indices.
"""
import os
import pickle
import numpy as np
import torch
import faiss
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from rank_bm25 import BM25Okapi
from PIL import Image

# Configuration constants
INDEX_DIR = "indexes_final"
CLIP_MODEL = "openai/clip-vit-large-patch14"
BLIP_MODEL = "Salesforce/blip-image-captioning-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Utility normalization

def normalize(x: np.ndarray) -> np.ndarray:
    mn, mx = x.min(), x.max()
    return (x - mn) / (mx - mn + 1e-8)

# Encoder class
class QueryEncoder:
    def __init__(self):
        self.clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL)
        self.clip_model = CLIPModel.from_pretrained(CLIP_MODEL).to(DEVICE).eval()
        # self.blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL)
        # self.blip_model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL).to(DEVICE).eval()

    def encode(self, image_path=None, text=None, weight_image=0.5, weight_text=0.5):
        imgs, txts = [], []
        from PIL import Image

        if image_path:
            imgs.append(Image.open(image_path).convert('RGB'))
        if text:
            txts.append(text)
        # auto-caption if only image
        # if image_path and not txts:
        #     bi = self.blip_processor(images=imgs, return_tensors='pt').to(DEVICE)
        #     bo = self.blip_model.generate(**bi, max_new_tokens=50)
        #     txts = [self.blip_processor.batch_decode(bo, skip_special_tokens=True)[0]]
        inp = self.clip_processor(text=txts or [""], images=imgs or [Image.new('RGB',(224,224))] ,
                                  return_tensors='pt', padding=True, truncation=True).to(DEVICE)
        ie = self.clip_model.get_image_features(pixel_values=inp.pixel_values) if len(imgs)>0 else None
        te = self.clip_model.get_text_features(input_ids=inp.input_ids, attention_mask=inp.attention_mask) if txts else None
        if ie is not None:
            ie = ie / ie.norm(dim=-1, keepdim=True)
        if te is not None:
            te = te / te.norm(dim=-1, keepdim=True)
        ce = (weight_image * ie + weight_text * te) if (ie is not None and te is not None) else (ie or te)
        ce = ce / ce.norm(dim=-1, keepdim=True)
        return (
            ie.detach().cpu().numpy()[0] if ie is not None else None,
            te.detach().cpu().numpy()[0] if te is not None else None,
            ce.detach().cpu().numpy()[0]
        )

class Retriever:
    def __init__(self, idx_comb, idx_txt, lambda_hybrid):
        self.idx_comb = idx_comb
        self.idx_txt = idx_txt
        self.lambda_hybrid = lambda_hybrid

    def retrieve(self, ce, te, k):
        Df, If = self.idx_comb.search(np.expand_dims(ce, 0), k)
        Dt, It = self.idx_txt.search(np.expand_dims(te, 0), k)
        return Df[0], If[0], Dt[0], It[0]

class Reranker:
    def __init__(self, meta, bm25, lambda_hybrid, lambda_text):
        self.meta = meta
        self.bm25 = bm25
        self.lambda_hybrid = lambda_hybrid
        self.lambda_text = lambda_text

    def score(self, Df, If, Dt, It, query_terms):
        sp = self.bm25.get_scores(query_terms)
        nd, nt, ns = normalize(Df), normalize(Dt), normalize(sp[If])
        cb = self.lambda_hybrid * nd + (1 - self.lambda_hybrid) * (1 - ns)
        final = (1 - self.lambda_text) * cb + self.lambda_text * nt
        return final
def retrieve_and_rerank(image_path: str = None, text_query: str = "",
                        k: int = 50, lambda_hybrid: float = 0.5, lambda_text: float = 0.6, rank_query: str = None, img_weight: float = 0.5, text_weight: float = 0.5):
    """
    Performs retrieval and reranking in one go.
    Returns:
        - final_ranked_indices: np.ndarray of shape (top_k,)
        - metadata: list of dicts for each item
    """
    # Load artifacts
    idx_comb = faiss.read_index(os.path.join(INDEX_DIR, 'idx_comb.bin'))
    idx_txt = faiss.read_index(os.path.join(INDEX_DIR, 'idx_txt.bin'))
    with open(os.path.join(INDEX_DIR, 'meta.pkl'), 'rb') as f:
        meta = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'rb') as f:
        bm25 = pickle.load(f)

    # Encode query
    encoder = QueryEncoder()
    ie, te, ce = encoder.encode(image_path=image_path, text=text_query, weight_image=img_weight, weight_text=text_weight)

    # Retrieve
    Df, If, Dt, It = Retriever(idx_comb, idx_txt, lambda_hybrid).retrieve(ce, te, k)

    # Rerank
    query_terms = rank_query.lower().split()
    scores = Reranker(meta, bm25, lambda_hybrid, lambda_text).score(Df, If, Dt, It, query_terms)
    ranked = np.argsort(scores)
    final_indices = If[ranked]
    return final_indices, meta


def rerank_only(initial_indices: np.ndarray, image_path: str = None, text_query: str = "",
                lambda_hybrid: float = 0.5, lambda_text: float = 0.6):
    """
    Given initial retrieved indices, apply only the reranking step.
    Returns:
        - reranked_indices: np.ndarray of shape (len(initial_indices),)
        - metadata: list of dicts for each item
    """
    # Load metadata and BM25
    with open(os.path.join(INDEX_DIR, 'meta.pkl'), 'rb') as f:
        meta = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'rb') as f:
        bm25 = pickle.load(f)

    # Derive feature distances for reranking
    # For simplicity, load text-only index embeddings
    idx_txt = faiss.read_index(os.path.join(INDEX_DIR, 'idx_txt.bin'))
    # Encode query text
    encoder = QueryEncoder()
    _, te, _ = encoder.encode(image_path=image_path, text=text_query)
    Dt, It = idx_txt.search(np.expand_dims(te, 0), len(initial_indices))

    # Compute reranking scores
    Df = None  # not used in pure rerank-only mode
    scores = Reranker(meta, bm25, lambda_hybrid, lambda_text).score(
        Df if Df is not None else np.zeros_like(Dt),
        initial_indices,
        Dt[0],
        It[0],
        text_query.lower().split()
    )
    reranked_order = np.argsort(scores)
    reranked_indices = initial_indices[reranked_order]
    return reranked_indices, meta
