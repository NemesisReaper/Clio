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
from clio.models.decipherment import BandhaPattern, DeciphermentRequest
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
    }
