"""Phonetic and Akshara-Level Reference Alignment Engine with Meter Analysis."""
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from clio.decipherment.alignment.akshara_tokenizer import akshara_tokenizer
from clio.decipherment.alignment.sandhi import sandhi_resolver


class MatchType(str, Enum):
    EXACT = "EXACT"
    PHONETIC_SANDHI = "PHONETIC_SANDHI"
    MISMATCH = "MISMATCH"
    INSERTION = "INSERTION"
    DELETION = "DELETION"


class AlignedTokenPair(BaseModel):
    position: int
    candidate_akshara: Optional[str] = None
    reference_akshara: Optional[str] = None
    match_type: MatchType
    score: float


class AlignmentReport(BaseModel):
    """Detailed character-and-akshara level alignment and mismatch report."""
    candidate_raw: str
    reference_raw: str
    candidate_normalized: str
    reference_normalized: str
    candidate_aksharas: List[str]
    reference_aksharas: List[str]
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    exact_matches: int = 0
    phonetic_sandhi_matches: int = 0
    mismatches: int = 0
    insertions: int = 0
    deletions: int = 0
    aligned_pairs: List[AlignedTokenPair] = Field(default_factory=list)
    character_level_diff: List[Dict[str, Any]] = Field(default_factory=list)
    meter_analysis: Dict[str, Any] = Field(default_factory=dict)
    is_verified_match: bool = False


class HalegannadaAligner:
    """Needleman-Wunsch inspired dynamic programming aligner for Halegannada verses."""

    # Scoring constants
    SCORE_EXACT = 2.0
    SCORE_SANDHI = 1.5
    SCORE_MISMATCH = -1.0
    SCORE_GAP = -1.2

    def __init__(self):
        self.tokenizer = akshara_tokenizer
        self.sandhi = sandhi_resolver

    def align(
        self,
        candidate_text: str,
        reference_shloka_text: str,
        verification_threshold: float = 0.85,
    ) -> AlignmentReport:
        """Perform comprehensive phonetic alignment between candidate sequence and reference shloka."""
        # 1. Unicode Normalization (separate from raw)
        cand_norm = self.tokenizer.normalize(candidate_text.strip())
        ref_norm = self.tokenizer.normalize(reference_shloka_text.strip())

        # 2. Akshara Segmentation
        cand_tokens = self.tokenizer.tokenize(cand_norm)
        ref_tokens = self.tokenizer.tokenize(ref_norm)

        # If candidate stream is much longer than reference verse (e.g. full 729-cell matrix stream),
        # extract the matching candidate segment/window corresponding to the verse size
        if len(cand_tokens) > int(len(ref_tokens) * 1.4):
            best_cand_slice = cand_tokens[:len(ref_tokens) + 4]
            # Also check if verse ends with ||
            for end_idx in range(len(ref_tokens) - 5, min(len(cand_tokens), len(ref_tokens) + 15)):
                if end_idx < len(cand_tokens) and cand_tokens[end_idx] in ("||", "॥"):
                    best_cand_slice = cand_tokens[:end_idx + 1]
                    break
            target_cand_tokens = best_cand_slice
        else:
            target_cand_tokens = cand_tokens

        # 3. Dynamic Programming Global Alignment (Needleman-Wunsch)
        aligned_pairs, score = self._needleman_wunsch(target_cand_tokens, ref_tokens)

        # 4. Compute statistics
        exact = sum(1 for p in aligned_pairs if p.match_type == MatchType.EXACT)
        sandhi_cnt = sum(1 for p in aligned_pairs if p.match_type == MatchType.PHONETIC_SANDHI)
        mismatch_cnt = sum(1 for p in aligned_pairs if p.match_type == MatchType.MISMATCH)
        ins_cnt = sum(1 for p in aligned_pairs if p.match_type == MatchType.INSERTION)
        del_cnt = sum(1 for p in aligned_pairs if p.match_type == MatchType.DELETION)

        # Maximum possible score is len(ref_tokens) * SCORE_EXACT
        max_possible = max(len(ref_tokens), 1) * self.SCORE_EXACT
        normalized_similarity = max(0.0, min(1.0, (exact * self.SCORE_EXACT + sandhi_cnt * self.SCORE_SANDHI) / max_possible))

        # 5. Character-level diff report
        char_diff = self._build_character_diff(aligned_pairs)

        # 6. Meter Analysis (Chhandas)
        meter = self._analyze_meter(cand_tokens)

        is_verified = (
            normalized_similarity >= verification_threshold
            and mismatch_cnt <= 2
            and del_cnt == 0
        )

        return AlignmentReport(
            candidate_raw=candidate_text,
            reference_raw=reference_shloka_text,
            candidate_normalized=cand_norm,
            reference_normalized=ref_norm,
            candidate_aksharas=cand_tokens,
            reference_aksharas=ref_tokens,
            similarity_score=round(normalized_similarity, 3),
            exact_matches=exact,
            phonetic_sandhi_matches=sandhi_cnt,
            mismatches=mismatch_cnt,
            insertions=ins_cnt,
            deletions=del_cnt,
            aligned_pairs=aligned_pairs,
            character_level_diff=char_diff,
            meter_analysis=meter,
            is_verified_match=is_verified,
        )

    def _needleman_wunsch(
        self, cand: List[str], ref: List[str]
    ) -> Tuple[List[AlignedTokenPair], float]:
        """Global sequence alignment with Sandhi awareness."""
        m, n = len(cand), len(ref)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i * self.SCORE_GAP
        for j in range(n + 1):
            dp[0][j] = j * self.SCORE_GAP

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                t_cand = cand[i - 1]
                t_ref = ref[j - 1]

                if t_cand == t_ref:
                    sim = self.SCORE_EXACT
                elif self.sandhi.are_sandhi_equivalent(t_cand, t_ref):
                    sim = self.SCORE_SANDHI
                else:
                    sim = self.SCORE_MISMATCH

                dp[i][j] = max(
                    dp[i - 1][j - 1] + sim,        # Match / Mismatch
                    dp[i - 1][j] + self.SCORE_GAP,  # Insertion
                    dp[i][j - 1] + self.SCORE_GAP,  # Deletion
                )

        # Traceback
        i, j = m, n
        aligned_pairs: List[AlignedTokenPair] = []
        pos = max(m, n)

        while i > 0 or j > 0:
            if i > 0 and j > 0 and (
                dp[i][j] == dp[i - 1][j - 1] + (
                    self.SCORE_EXACT if cand[i - 1] == ref[j - 1]
                    else (self.SCORE_SANDHI if self.sandhi.are_sandhi_equivalent(cand[i - 1], ref[j - 1]) else self.SCORE_MISMATCH)
                )
            ):
                t_c, t_r = cand[i - 1], ref[j - 1]
                if t_c == t_r:
                    m_type = MatchType.EXACT
                    sc = self.SCORE_EXACT
                elif self.sandhi.are_sandhi_equivalent(t_c, t_r):
                    m_type = MatchType.PHONETIC_SANDHI
                    sc = self.SCORE_SANDHI
                else:
                    m_type = MatchType.MISMATCH
                    sc = self.SCORE_MISMATCH

                aligned_pairs.append(
                    AlignedTokenPair(
                        position=pos,
                        candidate_akshara=t_c,
                        reference_akshara=t_r,
                        match_type=m_type,
                        score=sc,
                    )
                )
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i - 1][j] + self.SCORE_GAP:
                aligned_pairs.append(
                    AlignedTokenPair(
                        position=pos,
                        candidate_akshara=cand[i - 1],
                        reference_akshara=None,
                        match_type=MatchType.INSERTION,
                        score=self.SCORE_GAP,
                    )
                )
                i -= 1
            else:
                aligned_pairs.append(
                    AlignedTokenPair(
                        position=pos,
                        candidate_akshara=None,
                        reference_akshara=ref[j - 1] if j > 0 else None,
                        match_type=MatchType.DELETION,
                        score=self.SCORE_GAP,
                    )
                )
                j -= 1
            pos -= 1

        aligned_pairs.reverse()
        # Re-index position 1..len
        for idx, p in enumerate(aligned_pairs, start=1):
            p.position = idx

        return aligned_pairs, dp[m][n]

    def _build_character_diff(
        self, pairs: List[AlignedTokenPair]
    ) -> List[Dict[str, Any]]:
        diffs = []
        for p in pairs:
            if p.match_type != MatchType.EXACT:
                diffs.append({
                    "position": p.position,
                    "type": p.match_type.value,
                    "candidate": p.candidate_akshara,
                    "reference": p.reference_akshara,
                    "explanation": (
                        f"Phonetic Sandhi match between '{p.candidate_akshara}' and '{p.reference_akshara}'"
                        if p.match_type == MatchType.PHONETIC_SANDHI
                        else f"Mismatch: decoded '{p.candidate_akshara}', expected '{p.reference_akshara}'"
                    ),
                })
        return diffs

    def _analyze_meter(self, tokens: List[str]) -> Dict[str, Any]:
        """Examine syllabic weights and test for classical Halegannada Kanda / Anushtup meter."""
        matras = self.tokenizer.compute_matra_sequence(tokens)
        total_matras = sum(matras)
        total_syllables = len(matras)

        # Kanda padya has 4 padas (lines): 12, 20, 12, 20 = 64 matras total!
        is_kanda = 60 <= total_matras <= 68
        # Anushtup shloka has 32 syllables (4 padas of 8 syllables)
        is_anushtup = 30 <= total_syllables <= 34

        meter_name = "Unknown Prosody"
        if is_kanda:
            meter_name = "Kanda Padya (ಕಂದ ಪದ್ಯ, ~64 matras)"
        elif is_anushtup:
            meter_name = "Anushtup Chhandas (ಅನುಷ್ಟುಪ್ ಛಂದಸ್ಸು, 32 aksharas)"

        return {
            "total_syllables": total_syllables,
            "total_matras": total_matras,
            "matra_sequence": matras[:32],  # Preview
            "detected_meter": meter_name,
            "is_kanda_meter": is_kanda,
            "is_anushtup_meter": is_anushtup,
        }


halegannada_aligner = HalegannadaAligner()
