"""FastAPI routes for Historical Validation, Source Provenance, and Real-Data Integration."""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from clio.decipherment.provenance.registry import provenance_registry
from clio.models.provenance import (
    HistoricalSourceModel,
    ValidationResultModel,
)
from clio.storage.db import ValidationResultRecord, get_db
from clio.validation.engine import historical_validation_engine

router = APIRouter(tags=["Historical Validation & Provenance"])


class ValidationRunPayload(BaseModel):
    target_type: str = Field(..., description="Target type to validate: RULE, CHAKRA, or REAL_DATA")
    target_id: str = Field(..., description="Rule ID, Chakra ID, or 'ALL'")


@router.get("/api/v1/sources", response_model=List[HistoricalSourceModel])
def list_historical_sources():
    """Retrieve all canonical historical sources, critical editions, and manuscript references."""
    return provenance_registry.list_sources()


@router.get("/api/v1/sources/{source_id}", response_model=HistoricalSourceModel)
def get_historical_source(source_id: str):
    """Retrieve bibliographic details and physical location for a specific historical source."""
    source = provenance_registry.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Historical source '{source_id}' not found.",
        )
    return source


@router.get("/api/v1/validation/real-data-status")
def inspect_real_data_status(db: Session = Depends(get_db)):
    """Check availability of user-provided manuscript PDFs versus synthetic engineering fixtures."""
    return historical_validation_engine.inspect_real_data_availability(db=db)


@router.get("/api/v1/validation/{result_id}", response_model=ValidationResultModel)
def get_validation_result(result_id: str, db: Session = Depends(get_db)):
    """Retrieve a stored validation audit result by ID."""
    rec = db.query(ValidationResultRecord).filter(ValidationResultRecord.id == result_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation result '{result_id}' not found in database.",
        )
    return ValidationResultModel(
        validation_id=rec.id,
        target_type=rec.target_type,
        target_id=rec.target_id,
        is_valid=rec.is_valid,
        verification_state=rec.verification_state,
        validation_timestamp=rec.validation_timestamp,
        metrics=json.loads(rec.metrics_json or "{}"),
        warnings=json.loads(rec.warnings_json or "[]"),
        errors=json.loads(rec.errors_json or "[]"),
        provenance_chain=json.loads(rec.provenance_chain_json or "[]"),
    )


@router.post("/api/v1/validation/run", response_model=ValidationResultModel)
def run_validation(payload: ValidationRunPayload, db: Session = Depends(get_db)):
    """Execute a formal validation check against a rule or stored Chakra matrix."""
    return historical_validation_engine.run_validation(
        target_type=payload.target_type,
        target_id=payload.target_id,
        db=db,
    )

