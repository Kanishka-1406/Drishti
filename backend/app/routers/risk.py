from fastapi import APIRouter, HTTPException, Query

from app.services.risk_service import calculate_region_risk


router = APIRouter(
    prefix="/risk",
    tags=["risk"],
)


@router.get("")
def get_risk(
    region_id: int = Query(..., gt=0),
):
    try:
        return calculate_region_risk(
            region_id=region_id,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )