from datetime import date, datetime
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openpyxl import load_workbook
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.comparable import Comparable
from app.models.user import User, UserRole
from app.schemas.comparable import (
    ComparableCreate,
    ComparableImportResult,
    ComparableListOut,
    ComparableOut,
    NearbyQuery,
)

router = APIRouter()


def to_out(item: Comparable) -> ComparableOut:
    return ComparableOut(
        id=item.id,
        community=item.community,
        address=item.address,
        city=item.city,
        district=item.district,
        lng=item.lng,
        lat=item.lat,
        area=item.area,
        floor=item.floor,
        total_floor=item.total_floor,
        orientation=item.orientation,
        build_year=item.build_year,
        deal_price=item.deal_price,
        deal_date=item.deal_date,
        source=item.source,
        remark=item.remark,
    )


@router.get("", response_model=ComparableListOut)
def list_comparables(
    page: int = 1,
    size: int = 20,
    city: str = "",
    district: str = "",
    keyword: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Comparable)
    if city:
        q = q.filter(Comparable.city == city)
    if district:
        q = q.filter(Comparable.district == district)
    if keyword:
        q = q.filter(Comparable.community.contains(keyword))
    total = q.count()
    items = q.order_by(Comparable.deal_date.desc()).offset((page - 1) * size).limit(size).all()
    return ComparableListOut(total=total, items=[to_out(i) for i in items])


@router.post("", response_model=ComparableOut)
def create_comparable(
    body: ComparableCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.appraiser, UserRole.admin)),
):
    item = Comparable(**body.model_dump(), created_by=user.id)
    db.add(item)
    db.flush()
    return to_out(item)


@router.get("/{item_id}", response_model=ComparableOut)
def get_comparable(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.get(Comparable, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="案例不存在")
    return to_out(item)


@router.put("/{item_id}", response_model=ComparableOut)
def update_comparable(
    item_id: int,
    body: ComparableCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.appraiser, UserRole.admin)),
):
    item = db.get(Comparable, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="案例不存在")
    for k, v in body.model_dump().items():
        setattr(item, k, v)
    db.add(item)
    db.flush()
    return to_out(item)


@router.delete("/{item_id}")
def delete_comparable(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    item = db.get(Comparable, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="案例不存在")
    db.delete(item)
    return {"ok": True}


@router.post("/nearby", response_model=ComparableListOut)
def nearby(
    body: NearbyQuery,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    point = func.ST_SetSRID(func.ST_MakePoint(body.lng, body.lat), 4326)
    dist = func.ST_DistanceSphere(Comparable.location, point).label("dist")
    rows = (
        db.query(Comparable, dist)
        .filter(dist <= body.radius_m)
        .order_by(dist)
        .limit(body.limit)
        .all()
    )
    return ComparableListOut(total=len(rows), items=[to_out(c) for c, _ in rows])


def _parse_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


@router.post("/import", response_model=ComparableImportResult)
def import_comparables(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.appraiser, UserRole.admin)),
):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 文件")
    try:
        data = file.file.read()
        wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法读取 Excel: {e}")
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        headers = [str(h).strip() if h is not None else "" for h in next(rows_iter)]
    except StopIteration:
        return ComparableImportResult(inserted=0, skipped=0, errors=["空文件"])
    idx = {h: i for i, h in enumerate(headers)}
    required = ["community", "lng", "lat", "area", "deal_price", "deal_date"]
    missing = [c for c in required if c not in idx]
    if missing:
        raise HTTPException(status_code=400, detail=f"缺少必要列: {', '.join(missing)}")

    inserted = 0
    skipped = 0
    errors: list[str] = []
    for row_no, row in enumerate(rows_iter, start=2):
        try:
            def get(col, default=""):
                i = idx.get(col)
                if i is None or i >= len(row):
                    return default
                val = row[i]
                return default if val is None else val

            deal_date = _parse_date(get("deal_date"))
            if deal_date is None:
                raise ValueError("deal_date 格式错误，应为 YYYY-MM-DD")
            payload = ComparableCreate(
                community=str(get("community", "")).strip(),
                address=str(get("address", "")).strip(),
                city=str(get("city", "")).strip(),
                district=str(get("district", "")).strip(),
                lng=float(get("lng")),
                lat=float(get("lat")),
                area=float(get("area")),
                floor=int(get("floor", 0) or 0),
                total_floor=int(get("total_floor", 0) or 0),
                orientation=str(get("orientation", "")).strip(),
                build_year=int(get("build_year", 0) or 0),
                deal_price=float(get("deal_price")),
                deal_date=deal_date,
                source=str(get("source", "")).strip(),
                remark=str(get("remark", "")).strip(),
            )
            item = Comparable(**payload.model_dump(), created_by=user.id)
            db.add(item)
            inserted += 1
        except Exception as e:
            skipped += 1
            if len(errors) < 20:
                errors.append(f"第{row_no}行: {e}")
    db.flush()
    return ComparableImportResult(inserted=inserted, skipped=skipped, errors=errors)
