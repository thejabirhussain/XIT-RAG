"""Field mapping service for auto-mapping source to target fields."""

import logging
import time
from typing import List, Dict, Tuple, Optional

from models import MappingRequest, MappingResponse, FieldMapping, TargetMappingResult, TargetField
from services.rag_services.fuzzy_service import fuzzy_similarity
from helpers.rag_helpers.mappers import build_label, is_description_field

# Import sentence transformers directly
try:
    from sentence_transformers import SentenceTransformer, util
    SEMANTIC_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    SEMANTIC_MODEL = None

logger = logging.getLogger(__name__)


class FieldMappingService:
    """Service for hybrid fuzzy + semantic field mapping."""
    
    def __init__(self, embedding_service=None):
        # We'll use our own sentence transformer for simplicity
        self.semantic_model = SEMANTIC_MODEL
        logger.info("FieldMappingService initialized")
    
    def _compute_embeddings(self, texts: List[str]):
        """Compute embeddings for a list of texts."""
        if self.semantic_model is None or not texts:
            return None
        return self.semantic_model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
    
    def _compute_semantic_similarity(
        self,
        target_idx: int,
        source_idx: int,
        target_embs,
        source_embs
    ) -> float:
        """Compute cosine similarity between embeddings."""
        if target_embs is None or source_embs is None:
            return 0.0
        
        try:
            sim_tensor = util.cos_sim(target_embs[target_idx], source_embs[source_idx])
            sim_val = float(sim_tensor.item())
            return max(0.0, sim_val)  # Floor negative similarities
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def map_fields(self, req: MappingRequest) -> MappingResponse:
        """
        One-to-one hybrid fuzzy + semantic matching from targets -> sources.
        """
        start_total = time.time()
        logger.info("=" * 60)
        logger.info("🚀 Starting field mapping process")
        
        # Stage 1: Flatten targets
        start = time.time()
        flat_targets: List[TargetField] = []
        for group in req.target_groups:
            flat_targets.extend(group.fields)
        sources = req.sources
        logger.info(f"📊 Sources: {len(sources)}, Targets: {len(flat_targets)}")
        logger.info(f"⏱️  Stage 1 (Flatten): {(time.time() - start) * 1000:.2f}ms")

        # Stage 2: Build labels
        start = time.time()
        source_labels = [build_label(s.name, s.id, s.description or "") for s in sources]
        target_labels = [build_label(t.name, t.id, t.description or "") for t in flat_targets]
        logger.info(f"⏱️  Stage 2 (Build labels): {(time.time() - start) * 1000:.2f}ms")

        # Stage 3: Compute embeddings
        start = time.time()
        source_embs = self._compute_embeddings(source_labels) if source_labels else None
        target_embs = self._compute_embeddings(target_labels) if target_labels else None
        embedding_time = (time.time() - start) * 1000
        logger.info(
            f"⏱️  Stage 3 (Embeddings): {embedding_time:.2f}ms "
            f"{'[SEMANTIC MODEL ACTIVE]' if source_embs is not None else '[FALLBACK - NO SEMANTIC]'}"
        )

        # Stage 4: Score all candidates
        start = time.time()
        candidates: List[Tuple[int, int, float]] = []
        total_comparisons = 0

        for ti, t_label in enumerate(target_labels):
            if not t_label:
                continue
            for si, s_label in enumerate(source_labels):
                if not s_label:
                    continue
                
                total_comparisons += 1
                f = fuzzy_similarity(t_label, s_label)
                s = self._compute_semantic_similarity(ti, si, target_embs, source_embs)

                total_weight = max(req.fuzzy_weight + req.semantic_weight, 1e-6)
                wf = req.fuzzy_weight / total_weight
                ws = req.semantic_weight / total_weight

                final_score = wf * f + ws * s

                # Penalize description fields
                if is_description_field(sources[si].name, sources[si].id):
                    final_score *= 0.7

                if final_score >= req.min_confidence:
                    candidates.append((ti, si, final_score))

        scoring_time = (time.time() - start) * 1000
        logger.info(f"⏱️  Stage 4 (Scoring): {scoring_time:.2f}ms")
        logger.info(f"   💡 Comparisons: {total_comparisons}, Candidates above threshold: {len(candidates)}")

        # Stage 5: One-to-one assignment
        start = time.time()
        candidates.sort(key=lambda x: x[2], reverse=True)

        used_targets = set()
        used_sources = set()
        assignment: Dict[int, int] = {}

        for ti, si, score in candidates:
            if ti in used_targets or si in used_sources:
                continue
            used_targets.add(ti)
            used_sources.add(si)
            assignment[ti] = si
        
        assignment_time = (time.time() - start) * 1000
        logger.info(f"⏱️  Stage 5 (Assignment): {assignment_time:.2f}ms")
        logger.info(f"   ✅ Final mappings: {len(assignment)}")

        # Stage 6: Build results
        start = time.time()
        results: List[TargetMappingResult] = []

        for ti, target in enumerate(flat_targets):
            if ti in assignment:
                si = assignment[ti]
                src = sources[si]

                t_label = target_labels[ti]
                s_label = source_labels[si]

                f = fuzzy_similarity(t_label, s_label)
                s = self._compute_semantic_similarity(ti, si, target_embs, source_embs)

                total_weight = max(req.fuzzy_weight + req.semantic_weight, 1e-6)
                wf = req.fuzzy_weight / total_weight
                ws = req.semantic_weight / total_weight
                final_score = wf * f + ws * s

                # Apply description field penalty
                if is_description_field(src.name, src.id):
                    final_score *= 0.7

                mapping_obj = FieldMapping(
                    source_id=src.id,
                    source_name=src.name,
                    source_datatype=src.datatype,
                    confidence=round(final_score, 4),
                    transform=None
                )
            else:
                mapping_obj = None

            results.append(
                TargetMappingResult(
                    id=target.id,
                    name=target.name,
                    description=target.description,
                    datatype=target.datatype,
                    required=target.required,
                    mapping=mapping_obj
                )
            )
        
        build_results_time = (time.time() - start) * 1000
        logger.info(f"⏱️  Stage 6 (Build results): {build_results_time:.2f}ms")

        # Total time
        total_time = (time.time() - start_total) * 1000
        logger.info(f"⏱️  ⚡ TOTAL TIME: {total_time:.2f}ms")
        logger.info("=" * 60)

        return MappingResponse(mappings=results)
