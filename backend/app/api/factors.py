from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.valuation import FactorConfig
from app.schemas.factor import FactorConfigCreate, FactorConfigListOut, FactorConfigOut

router = APIRouter()

DEFAULT_COMPARISON_FACTORS = [
    {"name": "area", "type": "comparison", "rules": {"per_10pct": 0.1, "min": 0.9, "max": 1.1}, "remark": "面积修正：与标的差异每10%调整"},
    {"name": "floor", "type": "comparison", "rules": {"per_relative": 0.05, "min": 0.95, "max": 1.05}, "remark": "楼层修正：相对楼层差异调整"},
    {"name": "build_year", "type": "comparison", "rules": {"per_year": 0.005, "min": 0.9, "max": 1.1}, "remark": "建成年代修正：每年差异调整"},
    {"name": "distance", "type": "comparison", "rules": {"base_m": 500.0}, "remark": "距离权重：weight=1/(1+d/base_m)"},
]


@router.get("", response_model=FactorConfigListOut)
def list_factors(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items = db.query(FactorConfig).order_by(FactorConfig.type, FactorConfig.name).all()
    return FactorConfigListOut(total=len(items), items=[FactorConfigOut.model_validate(i) for i in items])


@router.post("", response_model=FactorConfigOut)
def create_factor(
    body: FactorConfigCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    exists = db.query(FactorConfig).filter(FactorConfig.name == body.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="同名系数配置已存在")
    item = FactorConfig(**body.model_dump())
    db.add(item)
    db.flush()
    return FactorConfigOut.model_validate(item)


@router.put("/{item_id}", response_model=FactorConfigOut)
def update_factor(
    item_id: int,
    body: FactorConfigCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    item = db.get(FactorConfig, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="配置不存在")
    dup = db.query(FactorConfig).filter(FactorConfig.name == body.name, FactorConfig.id != item_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="同名系数配置已存在")
    for k, v in body.model_dump().items():
        setattr(item, k, v)
    db.add(item)
    db.flush()
    return FactorConfigOut.model_validate(item)


@router.delete("/{item_id}")
def delete_factor(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    item = db.get(FactorConfig, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(item)
    return {"ok": True}


@router.post("/seed-defaults", response_model=FactorConfigListOut)
def seed_defaults(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    created = []
    for d in DEFAULT_COMPARISON_FACTORS:
        exists = db.query(FactorConfig).filter(FactorConfig.name == d["name"]).first()
        if exists:
            continue
        item = FactorConfig(**d)
        db.add(item)
        created.append(item)
    db.flush()
    items = db.query(FactorConfig).order_by(FactorConfig.type, FactorConfig.name).all()
    return FactorConfigListOut(total=len(items), items=[FactorConfigOut.model_validate(i) for i in items])