"""ERP account mapping service with semantic similarity and business rules."""

import logging
import time
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from models import (
    ERPMappingRequest, ERPMappingResponse, ERPMappingResult,
    ScoredCandidate, Weights, Thresholds
)
from services.rag_services.fuzzy_service import fuzzy_similarity
from helpers.rag_helpers.erp_helpers import (
    normalize_text, normalize_type, extract_natural_account,
    mutex_penalty, keyword_boost, subset_boost,
    code_quality, digit_match_bonus
)

# Import sentence transformers
try:
    from sentence_transformers import SentenceTransformer, util
    import numpy as np
    SEMANTIC_MODEL = None  # Will be loaded lazily
except Exception:
    SEMANTIC_MODEL = None

logger = logging.getLogger(__name__)


class ERPMappingService:
    """Service for ERP account to COA mapping with semantic similarity."""
    
    def __init__(self):
        self.model = None
        self.weights = Weights()
        self.thresholds = Thresholds()
        
        # Caches for performance
        self._coa_cache: Dict[str, Dict] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        
        logger.info("ERPMappingService initialized")
    
    def _get_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            logger.info("Loading SentenceTransformer model (one-time)...")
            start = time.time()
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            load_time = time.time() - start
            logger.info(f"Model loaded in {load_time:.3f}s")
        return self.model
    
    def _embed_texts(self, texts: List[str], cache_prefix: str = "") -> List[List[float]]:
        """Embed texts with caching."""
        if not texts:
            return []
        
        model = self._get_model()
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache
        for i, text in enumerate(texts):
            cache_key = f"{cache_prefix}:{hash(text)}"
            if cache_key in self._embedding_cache:
                results.append(self._embedding_cache[cache_key])
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Embed uncached texts
        if uncached_texts:
            logger.info(f"Embedding {len(uncached_texts)}/{len(texts)} texts")
            embeddings = model.encode(
                uncached_texts,
                normalize_embeddings=True,
                batch_size=256,
                show_progress_bar=False,
                convert_to_tensor=False
            )
            
            # Update cache and results
            for idx, emb in zip(uncached_indices, embeddings):
                emb_list = emb.tolist()
                cache_key = f"{cache_prefix}:{hash(texts[idx])}"
                self._embedding_cache[cache_key] = emb_list
                results[idx] = emb_list
            
            # Limit cache size
            if len(self._embedding_cache) > 50000:
                keys_to_remove = list(self._embedding_cache.keys())[:len(self._embedding_cache)//4]
                for key in keys_to_remove:
                    self._embedding_cache.pop(key, None)
        
        return results
    
    def _cosine_similarity(self, u: List[float], v: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not u or not v or len(u) != len(v):
            return 0.0
        
        u_arr = np.array(u, dtype=np.float32)
        v_arr = np.array(v, dtype=np.float32)
        
        dot_product = np.dot(u_arr, v_arr)
        norm_product = np.linalg.norm(u_arr) * np.linalg.norm(v_arr)
        
        if norm_product == 0.0:
            return 0.0
        
        return float(dot_product / norm_product)
    
    def _prepare_coa(self, system_coa: List[Dict]) -> Dict:
        """Prepare and cache COA data."""
        # Create cache key
        coa_signature = str(sorted([(x.get('id'), x.get('name'), x.get('type')) 
                                     for x in system_coa]))
        coa_hash = hash(coa_signature)
        
        # Check cache
        if coa_hash in self._coa_cache:
            logger.info("Using cached COA data")
            return self._coa_cache[coa_hash]
        
        logger.info(f"Processing COA with {len(system_coa)} accounts")
        start = time.time()
        
        # Pre-compute normalized values
        coa_data = {
            'accounts': system_coa,
            'norm_names': [normalize_text(x.get('name', '')) for x in system_coa],
            'norm_types': [normalize_type(x.get('type', '')) for x in system_coa],
            'type_groups': defaultdict(list)
        }
        
        # Build type groups for fast filtering
        for i, acc_type in enumerate(coa_data['norm_types']):
            if acc_type:
                coa_data['type_groups'][acc_type].append(i)
        
        # Embed COA texts
        coa_texts = [f"{x.get('name', '')} {x.get('category', '') or ''} {x.get('type', '') or ''}" 
                     for x in system_coa]
        coa_data['embeddings'] = self._embed_texts(coa_texts, "COA")
        
        # Cache the data
        self._coa_cache[coa_hash] = coa_data
        
        prep_time = time.time() - start
        logger.info(f"COA prepared in {prep_time:.3f}s")
        
        return coa_data
    
    def _filter_candidates(self, local: Dict, coa_data: Dict) -> List[int]:
        """Filter COA candidates for a local account."""
        ltype = normalize_type(local.get('type', ''))
        
        # Start with type-matched candidates
        candidates = list(coa_data['type_groups'].get(ltype, []))
        
        # If no type matches, use all accounts
        if not candidates:
            candidates = list(range(len(coa_data['accounts'])))
        
        # Aggressive filtering for performance
        if len(candidates) > 50:
            lname_norm = normalize_text(local.get('name', ''))
            lname_tokens = set(lname_norm.split())
            
            # Score candidates by name overlap
            scored_candidates = []
            for idx in candidates:
                sname_norm = coa_data['norm_names'][idx]
                sname_tokens = set(sname_norm.split())
                overlap = len(lname_tokens & sname_tokens)
                scored_candidates.append((idx, overlap))
            
            # Keep top 30 by overlap
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = [idx for idx, _ in scored_candidates[:30]]
        
        return candidates
    
    def _score_candidate(self, local: Dict, local_emb: List[float], 
                         sys_idx: int, coa_data: Dict) -> ScoredCandidate:
        """Score a COA candidate for a local account."""
        sys = coa_data['accounts'][sys_idx]
        w = self.weights
        
        # Extract normalized values
        lname = local.get('name', '') or ""
        lname_norm = normalize_text(lname)
        sname = sys.get('name', '') or ""
        sname_norm = coa_data['norm_names'][sys_idx]
        
        ltype = normalize_type(local.get('type', '') or "")
        stype = coa_data['norm_types'][sys_idx]
        
        # Component scores
        scores = {}
        
        # 1. Type match (critical)
        scores['type_match'] = 1.0 if ltype and (ltype == stype) else 0.0
        
        # 2. Exact name match
        scores['exact_name'] = 1.0 if lname_norm and (lname_norm == sname_norm) else 0.0
        
        # 3. Semantic similarity
        scores['semantic'] = self._cosine_similarity(local_emb, coa_data['embeddings'][sys_idx])
        
        # 4. Fuzzy similarity
        scores['fuzzy'] = fuzzy_similarity(lname, sname)
        
        # 5. Category match
        lcategory = normalize_text(local.get('category', '') or "")
        scategory = normalize_text(sys.get('category', '') or "")
        scores['category'] = 1.0 if lcategory and (lcategory == scategory) else 0.0
        
        # 6. Code quality
        scores['code_quality'] = code_quality(
            local.get('code', ''),
            local.get('type', ''),
            sys.get('type', '')
        )
        
        # 7. Digit match bonus
        scores['digit_bonus'] = digit_match_bonus(
            local.get('code', ''),
            sys.get('code', '')
        )
        
        # Business rule adjustments
        scores['mutex_penalty'] = mutex_penalty(lname, sname)
        scores['keyword_boost'] = keyword_boost(lname, sname)
        scores['subset_boost'] = subset_boost(lname, sname)
        
        # Calculate aggregate score
        aggregate = (
            w.type * scores['type_match'] +
            w.semantic * scores['semantic'] +
            w.fuzzy * scores['fuzzy'] +
            w.category * scores['category'] +
            w.code * scores['code_quality'] +
            w.digit_bonus * scores['digit_bonus'] +
            (3.0 * scores['exact_name']) +  # Strong weight for exact match
            scores['keyword_boost'] +
            scores['subset_boost'] -
            scores['mutex_penalty']
        )
        
        return ScoredCandidate(
            system_id=sys.get('id'),
            system_code=sys.get('code'),
            system_name=sys.get('name'),
            system_type=sys.get('type'),
            system_category=sys.get('category'),
            scores=scores,
            aggregate=float(aggregate)
        )
    
    def _process_account(self, local: Dict, local_emb: List[float], 
                         coa_data: Dict) -> Dict:
        """Process a single local account and find best COA match."""
        # Filter candidates
        candidates = self._filter_candidates(local, coa_data)
        
        # Score all candidates
        scored = [self._score_candidate(local, local_emb, idx, coa_data) 
                  for idx in candidates]
        
        # Sort by score
        scored.sort(key=lambda x: x.aggregate, reverse=True)
        
        # Get best match
        best = scored[0] if scored else None
        
        # Calculate confidence
        if best:
            max_score = (
                self.weights.type + 
                self.weights.semantic + 
                self.weights.fuzzy + 
                self.weights.category +
                self.weights.code +
                self.weights.digit_bonus +
                3.0 +  # exact name weight
                0.15 + 0.12  # max keyword_boost + subset_boost
            )
            confidence = max(0.0, min(1.0, best.aggregate / max_score))
        else:
            confidence = 0.0
        
        # Make decision
        if confidence >= self.thresholds.auto and best and best.scores.get('type_match', 0) > 0:
            decision = "auto"
        elif confidence >= self.thresholds.review:
            decision = "review"
        else:
            decision = "manual"
        
        return {
            'best': best,
            'decision': decision,
            'confidence': confidence
        }
    
    def map_accounts(self, request: ERPMappingRequest) -> ERPMappingResponse:
        """Map local GL accounts to system COA."""
        start_total = time.time()
        logger.info("=" * 60)
        logger.info("🚀 Starting ERP account mapping")
        logger.info(f"📊 Local Accounts: {len(request.localAccounts)}, COA: {len(request.systemCOA)}")
        
        # Update thresholds
        self.thresholds.auto = request.auto_threshold
        self.thresholds.review = request.review_threshold
        
        # Prepare COA
        start = time.time()
        coa_accounts = [{
            "id": x.Id,
            "code": x.Id,
            "name": x.Name,
            "type": x.Category or "",
            "category": x.Category or ""
        } for x in request.systemCOA]
        coa_data = self._prepare_coa(coa_accounts)
        logger.info(f"⏱️  COA Preparation: {(time.time() - start) * 1000:.2f}ms")
        
        # Prepare local accounts
        start = time.time()
        gl_accounts = []
        local_texts = []
        
        for acc in request.localAccounts:
            name = acc.Description.split(" - ")[0].strip() if acc.Description else ""
            extracted = extract_natural_account(acc.Code)
            
            gl_accounts.append({
                "name": name,
                "code": acc.Code,
                "type": acc.ExpectedType or "",
                "category": "",
                "extracted": extracted,
                "erp": acc.ERP or ""
            })
            
            local_text = f"{name} {acc.ExpectedType or ''}"
            if local_text.strip():
                local_texts.append(local_text)
        
        logger.info(f"⏱️  Local Account Preparation: {(time.time() - start) * 1000:.2f}ms")
        
        # Embed local accounts
        start = time.time()
        local_embeddings = self._embed_texts(local_texts, "LOCAL")
        logger.info(f"⏱️  Local Account Embedding: {(time.time() - start) * 1000:.2f}ms")
        
        # Process each account
        start = time.time()
        results = []
        successful_count = 0
        
        for i, gl_account in enumerate(gl_accounts):
            if not gl_account.get('extracted'):
                # No natural account extracted
                results.append(ERPMappingResult(
                    ERP=gl_account.get('erp', ''),
                    Code=gl_account.get('code', ''),
                    Extracted=None,
                    MappedCOAID=None,
                    COAName="",
                    COADescription="",
                    Type="",
                    Score=0.0,
                    NeedsReview="Yes",
                    DescriptionProvided=gl_account.get('name', ''),
                    ExpectedType=gl_account.get('type', ''),
                    TypeMismatch="No"
                ))
            else:
                # Process mapping
                local_emb = local_embeddings[i] if i < len(local_embeddings) else []
                mapping_result = self._process_account(gl_account, local_emb, coa_data)
                
                best = mapping_result.get('best')
                confidence = mapping_result.get('confidence', 0.0)
                decision = mapping_result.get('decision', 'manual')
                
                if best:
                    needs_review = "No" if decision == "auto" else "Yes"
                    results.append(ERPMappingResult(
                        ERP=gl_account.get('erp', ''),
                        Code=gl_account.get('code', ''),
                        Extracted=gl_account.get('extracted'),
                        MappedCOAID=best.system_code,
                        COAName=best.system_name,
                        COADescription="Natural Account",
                        Type=normalize_type(best.system_type or ''),
                        Score=round(confidence, 3),
                        NeedsReview=needs_review,
                        DescriptionProvided=gl_account.get('name', ''),
                        ExpectedType=gl_account.get('type', ''),
                        TypeMismatch="No"
                    ))
                    
                    if needs_review == "No":
                        successful_count += 1
                else:
                    results.append(ERPMappingResult(
                        ERP=gl_account.get('erp', ''),
                        Code=gl_account.get('code', ''),
                        Extracted=gl_account.get('extracted'),
                        MappedCOAID=None,
                        COAName="",
                        COADescription="",
                        Type="",
                        Score=0.0,
                        NeedsReview="Yes",
                        DescriptionProvided=gl_account.get('name', ''),
                        ExpectedType=gl_account.get('type', ''),
                        TypeMismatch="No"
                    ))
        
        processing_time = (time.time() - start) * 1000
        logger.info(f"⏱️  Account Processing: {processing_time:.2f}ms")
        
        # Calculate total time
        total_time = (time.time() - start_total) * 1000
        success_rate = (successful_count / len(results)) * 100 if results else 0
        
        logger.info(f"✅ Successful Mappings: {successful_count}/{len(results)} ({success_rate:.1f}%)")
        logger.info(f"⏱️  ⚡ TOTAL TIME: {total_time:.2f}ms")
        logger.info("=" * 60)
        
        return ERPMappingResponse(
            ProcessedAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            TotalRecords=len(results),
            SuccessfulMappings=successful_count,
            RequireReview=len(results) - successful_count,
            MappingResult=results,
            ProcessingTimeMs=round(total_time, 2)
        )
