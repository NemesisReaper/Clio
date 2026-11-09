"""Bilingual English and Modern Kannada historical and philosophical explanation generator."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from clio.decipherment.alignment.aligner import AlignmentReport
from clio.models.graph import TraversalResult
from clio.models.provenance import (
    DeciphermentConfidenceBreakdown,
    HumanVerificationStatus,
    OutputTier,
    RuleVerificationState,
)
from clio.decipherment.provenance.registry import provenance_registry


class DecodingStatus(str, Enum):
    VERIFIED_DECODING = "VERIFIED_DECODING"
    CANDIDATE_DECODING = "CANDIDATE_DECODING"
    TRANSLATION_ONLY = "TRANSLATION_ONLY"


class ComprehensiveDeciphermentReport(BaseModel):
    """Complete, evidence-backed bilingual decipherment report."""
    chakra_id: str
    bandha_name: str
    table_version: str
    decoding_status: DecodingStatus

    # 5 Output Tiers (Requirement 7)
    directly_extracted_tokens: List[str] = Field(default_factory=list, description="Tier 1: Verbatim unmerged raw tokens")
    algorithmically_generated_candidate_text: str = Field("", description="Tier 2: Ligature-synthesized candidate stream")
    candidate_alignment_with_shloka: Optional[AlignmentReport] = Field(None, description="Tier 3: Character-level alignment")
    historically_supported_interpretation: Optional[str] = Field(None, description="Tier 4: Attested historical translation")
    speculative_interpretation: Optional[str] = Field(None, description="Tier 5: Proposed/unverified candidate reading")

    # Primary texts (Backward compatibility)
    original_halegannada_reference: Optional[str] = None
    decoded_phonetic_sequence: str
    cleaned_segmented_verse: str

    # English Explanations
    english_translation: str
    english_philosophical_context: str
    english_historical_commentary: str

    # Modern Kannada Explanations (ಹೊಸಗನ್ನಡ ವಿವರಣೆ)
    modern_kannada_bhavartha: str
    modern_kannada_tika: str

    # Provenance, Evidence & Alternatives
    alignment_details: Optional[AlignmentReport] = None
    historical_entities_linked: List[str] = Field(default_factory=list)
    supporting_references: List[str] = Field(default_factory=list)
    alternative_interpretations: List[str] = Field(default_factory=list)

    # Multi-dimensional Confidence Metrics
    confidence_score: float
    confidence_breakdown: Dict[str, Any] = Field(default_factory=dict)
    detailed_confidence_breakdown: Optional[DeciphermentConfidenceBreakdown] = None
    uncertainty_notes: Optional[str] = None
    is_authoritative_claim: bool = False
    disclaimer: str = (
        "This decipherment report reports independent evidential dimensions. "
        "Linguistic plausibility alone does not claim or prove definitive historical authenticity."
    )


class BilingualDeciphermentExplainer:
    """Generates rigorous bilingual commentaries and historical contextualization."""

    # Curated knowledge base for authentic historical verses (e.g. Mangalacharana Chakra 1)
    KNOWN_EXPLANATIONS = {
        "ಶ್ರೀಮತ್ಪರಮ": {
            "english_translation": (
                "May the sacred doctrine of Jina, adorned with the supreme and profound "
                "hallmark of Syādvāda (the doctrine of manifold perspectives), prevail "
                "triumphant throughout the three worlds!"
            ),
            "english_context": (
                "This celebrated mangalacharana verse embodies the Digambara Jain philosophy "
                "of Syādvāda and Anekāntavāda (non-absolutism). In Siri Bhoovalaya, it is "
                "the foundational invocation extracted from Chakra 1, establishing that "
                "all knowledge encoded in the 729-cell matrix reflects multidimensional truth."
            ),
            "kannada_bhavartha": (
                "ಸ್ಯಾದ್ವಾದವೆಂಬ ಅಪ್ರತಿಹತವಾದ ಲಾಂಛನದಿಂದ ಶೋಭಿಸುವ, ಪರಮ ಗಂಭೀರವಾದ ತ್ರೈಲೋಕ್ಯನಾಥನಾದ "
                "ಜಿನೇಶ್ವರನ ಶಾಸನವು (ಧರ್ಮಬೋಧೆಯು) ಜಗತ್ತಿನಲ್ಲಿ ಸದಾ ವಿಜಯಶಾಲಿಯಾಗಿ ಬೆಳಗಲಿ!"
            ),
            "kannada_tika": (
                "ಇದು ಸಿರಿಭೂವಲಯದ ಮೊದಲ ಚಕ್ರದ ಮಂಗಳಾಚರಣೆಯಾಗಿದೆ. ಆಚಾರ್ಯ ಕುಮುದೇಂದು ಮುನಿಗಳು "
                "ಸರ್ವತೋಭದ್ರ ಬಂಧದ ಮೂಲಕ ಜೈನ ದರ್ಶನದ ಸ್ಯಾದ್ವಾದ ತತ್ತ್ವವನ್ನು ಇಲ್ಲಿ ಸ್ಥಾಪಿಸಿದ್ದಾರೆ. "
                "ಅಂಕಫಲದ ಪ್ರಕಾರ ಸಂಖ್ಯೆಗಳನ್ನು ಅಕ್ಷರಗಳಾಗಿ ಪರಿವರ್ತಿಸಿದಾಗ ಈ ಶ್ಲೋಕವು ಅನಾವರಣಗೊಳ್ಳುತ್ತದೆ."
            ),
            "references": [
                "Kumudendu Muni, Siri Bhoovalaya (Chakra 1, Mangaladhyaya).",
                "K. Yellappa Shastri & K. Srikantaiah (Eds.), Siri Bhoovalaya, Bangalore, 1953.",
                "Samantabhadra, Aptamimamsa, Verse 1.",
            ],
            "alternatives": [
                "Interpreted alternatively as an invocation to Tirthankara Mahavira.",
                "Some commentaries read the meter as classical Anushtup, while others classify it within Kanda Padya frame.",
            ],
        }
    }

    def generate_report(
        self,
        chakra_id: str,
        bandha_name: str,
        table_version: str,
        decoded_phonetics: str,
        reference_shloka: Optional[str],
        alignment: Optional[AlignmentReport],
        graph_context: Optional[TraversalResult],
        direct_extracted_tokens: Optional[List[str]] = None,
        matrix_completeness: float = 1.0,
    ) -> ComprehensiveDeciphermentReport:
        """Synthesize alignment, linguistic knowledge, and graph context into a bilingual report."""
        # 1. Determine decoding status
        if alignment and alignment.is_verified_match:
            status = DecodingStatus.VERIFIED_DECODING
        elif alignment and alignment.similarity_score >= 0.50:
            status = DecodingStatus.CANDIDATE_DECODING
        else:
            status = DecodingStatus.TRANSLATION_ONLY

        # 2. Look up rule and table verification states from provenance registry
        bandha_rule_id = f"RULE_BANDHA_{bandha_name.upper()}_CONCENTRIC_SPIRAL" if "SARVATOBHADRA" in bandha_name.upper() else f"RULE_BANDHA_{bandha_name.upper()}"
        bandha_verif_state = provenance_registry.get_rule_verification_state(bandha_rule_id)
        if bandha_verif_state == RuleVerificationState.UNVERIFIED:
            # Fallback check for general pattern name
            for r_id in provenance_registry.rules:
                if bandha_name.upper() in r_id:
                    bandha_verif_state = provenance_registry.get_rule_verification_state(r_id)
                    break

        bandha_score = (
            1.0 if bandha_verif_state == RuleVerificationState.VERIFIED
            else 0.65 if bandha_verif_state == RuleVerificationState.PARTIALLY_VERIFIED
            else 0.35 if bandha_verif_state == RuleVerificationState.EXPERIMENTAL
            else 0.10
        )

        table_verif_state = (
            RuleVerificationState.PARTIALLY_VERIFIED
            if "1953" in table_version
            else RuleVerificationState.EXPERIMENTAL
        )
        table_score = 0.70 if table_verif_state == RuleVerificationState.PARTIALLY_VERIFIED else 0.40

        # Multi-dimensional decoupled confidence measurements (Requirement 7)
        alignment_score = alignment.similarity_score if alignment else None
        evidence_coverage = 0.85 if reference_shloka else 0.30

        # Non-authoritative heuristic composite score
        heuristic_composite = round(
            ((alignment_score if alignment_score is not None else 0.40) * 0.40)
            + (matrix_completeness * 0.20)
            + (bandha_score * 0.20)
            + (table_score * 0.20),
            3,
        )

        detailed_breakdown = DeciphermentConfidenceBreakdown(
            matrix_extraction_completeness=min(1.0, max(0.0, matrix_completeness)),
            bandha_rule_verification=bandha_verif_state,
            bandha_rule_verification_score=bandha_score,
            ankaphala_table_verification=table_verif_state,
            ankaphala_table_verification_score=table_score,
            traversal_reproducibility=1.0,
            reference_alignment_quality=alignment_score,
            historical_evidence_coverage=evidence_coverage,
            human_verification_status=HumanVerificationStatus.PENDING,
            is_calibrated_heuristic=True,
            heuristic_composite_score=heuristic_composite,
        )

        confidence_breakdown_dict = {
            "matrix_extraction_completeness": matrix_completeness,
            "bandha_rule_verification": bandha_verif_state.value,
            "bandha_rule_score": bandha_score,
            "ankaphala_table_verification": table_verif_state.value,
            "ankaphala_table_score": table_score,
            "alignment_similarity": alignment_score or 0.0,
            "historical_evidence_coverage": evidence_coverage,
            "heuristic_composite_score": heuristic_composite,
            "overall_score": heuristic_composite,
        }

        # Check curated knowledge base for exact historical match
        commentary = None
        for key, data in self.KNOWN_EXPLANATIONS.items():
            if key in decoded_phonetics or (reference_shloka and key in reference_shloka):
                commentary = data
                break

        if commentary:
            eng_trans = commentary["english_translation"]
            eng_hist = commentary["english_context"]
            kan_bhav = commentary["kannada_bhavartha"]
            kan_tika = commentary["kannada_tika"]
            refs = commentary["references"]
            alts = commentary["alternatives"]
            hist_supported_interp = eng_trans
            speculative_interp = None
        else:
            eng_trans = (
                f"Candidate decipherment of passage from {chakra_id} via {bandha_name}. "
                "Decoded phoneme stream awaiting further contextual commentary."
            )
            eng_hist = (
                f"Extracted using Ankaphala table {table_version}. "
                "Linked to Halegannada historical context in Kumudendu Muni's tradition."
            )
            kan_bhav = f"{chakra_id} ರ {bandha_name} ಬಂಧದಿಂದ ಹೊರತೆಗೆಯಲಾದ ಅಭ್ಯರ್ಥಿ ಪಾಠದ ಭಾವಾರ್ಥ."
            kan_tika = "ಐತಿಹಾಸಿಕ ಹಳೆಗನ್ನಡ ಪಠ್ಯದ ಅನ್ವಯ ಹಾಗೂ ಪರಾಮರ್ಶೆ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ."
            refs = ["Kumudendu Muni, Siri Bhoovalaya (c. 850 CE)."]
            alts = ["Awaiting alternate readings from secondary manuscript copies."]
            hist_supported_interp = None
            speculative_interp = eng_trans

        # Linked historical entities
        linked_entities = []
        if graph_context:
            linked_entities.append(graph_context.anchor_entity.name)
            for e in graph_context.connected_entities[:5]:
                linked_entities.append(e.name)

        return ComprehensiveDeciphermentReport(
            chakra_id=chakra_id,
            bandha_name=bandha_name,
            table_version=table_version,
            decoding_status=status,
            directly_extracted_tokens=direct_extracted_tokens or [],
            algorithmically_generated_candidate_text=decoded_phonetics,
            candidate_alignment_with_shloka=alignment,
            historically_supported_interpretation=hist_supported_interp,
            speculative_interpretation=speculative_interp,
            original_halegannada_reference=reference_shloka,
            decoded_phonetic_sequence=decoded_phonetics,
            cleaned_segmented_verse=alignment.candidate_normalized if alignment else decoded_phonetics,
            english_translation=eng_trans,
            english_philosophical_context=eng_hist,
            english_historical_commentary=(
                f"Decipherment executed via {bandha_name} trajectory. "
                f"Historical verification status: {status.value}. "
                f"Bandha verification: {bandha_verif_state.value}."
            ),
            modern_kannada_bhavartha=kan_bhav,
            modern_kannada_tika=kan_tika,
            alignment_details=alignment,
            historical_entities_linked=linked_entities,
            supporting_references=refs,
            alternative_interpretations=alts,
            confidence_score=heuristic_composite,
            confidence_breakdown=confidence_breakdown_dict,
            detailed_confidence_breakdown=detailed_breakdown,
            uncertainty_notes=(
                None if status == DecodingStatus.VERIFIED_DECODING
                else "Candidate reading: Requires additional primary manuscript verification before asserting definitive truth."
            ),
            is_authoritative_claim=False,
        )


bilingual_explainer = BilingualDeciphermentExplainer()

