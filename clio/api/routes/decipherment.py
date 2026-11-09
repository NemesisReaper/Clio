"""FastAPI routes for Stage B Decipherment operations."""
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from clio.decipherment.ankaphala.engine import ankaphala_engine
from clio.decipherment.ankaphala.tables import AnkaphalaVersion
from clio.decipherment.bandhas.selector import bandha_engine
from clio.decipherment.explainer import ComprehensiveDeciphermentReport
from clio.decipherment.orchestrator import decipherment_orchestrator
from clio.decipherment.provenance.registry import provenance_registry
from clio.models.decipherment import BandhaPattern, DeciphermentRequest
from clio.models.provenance import RuleProvenanceModel
from clio.storage.db import get_db

router = APIRouter(prefix="/api/v1/decipher", tags=["Decipherment"])


class DecipherPayload(BaseModel):
    chakra_id: str
    selected_bandha: BandhaPattern = BandhaPattern.SARVATOBHADRA
    start_coordinate: Tuple[int, int] = (13, 13)
    custom_parameters: Dict[str, str] = Field(default_factory=dict)
    reference_shloka_text: Optional[str] = None
    table_version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953


@router.post("", response_model=ComprehensiveDeciphermentReport)
async def execute_decipherment(
    payload: DecipherPayload,
    db: Session = Depends(get_db),
):
    """Execute reproducible numerical-to-phonetic decipherment pipeline on a stored Chakra."""
    req = DeciphermentRequest(
        chakra_id=payload.chakra_id,
        selected_bandha=payload.selected_bandha,
        start_coordinate=payload.start_coordinate,
        custom_parameters=payload.custom_parameters,
    )
    try:
        report = await decipherment_orchestrator.decipher(
            request=req,
            db=db,
            reference_shloka_text=payload.reference_shloka_text,
            table_version=payload.table_version,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decipherment execution failed: {e}",
        )


@router.get("/bandhas")
def list_supported_bandhas():
    """Retrieve metadata and mathematical rules for all supported Bandhas."""
    bandhas = bandha_engine.get_supported_bandhas()
    result = []
    for b in bandhas:
        impl = bandha_engine.get_bandha(b)
        result.append(impl.metadata.model_dump())
    return result


@router.get("/tables")
def list_supported_tables():
    """Retrieve versioned Ankaphala tables and supported encoding schemes."""
    return {
        "supported_versions": ankaphala_engine.list_supported_versions(),
        "default_version": AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953.value,
        "historical_source": "Siri Bhoovalaya (1953 Bangalore Edition, K. Yellappa Shastri)",
        "audit_provenance": ankaphala_engine.get_table_provenance().model_dump(),
    }


@router.get("/rules", response_model=List[RuleProvenanceModel])
def list_decipherment_rules(rule_type: Optional[str] = None):
    """Retrieve all registered decipherment rules, documentation levels, and verification states."""
    return provenance_registry.list_rules(rule_type=rule_type)


@router.get("/rules/{rule_id}/provenance", response_model=RuleProvenanceModel)
def get_rule_provenance(rule_id: str):
    """Retrieve complete bibliographic provenance and verification audit for a specific rule."""
    rule = provenance_registry.get_rule_provenance(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decipherment rule '{rule_id}' is not registered in the provenance database.",
        )
    return rule

