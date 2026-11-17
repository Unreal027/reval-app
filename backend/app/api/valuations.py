from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.valuation import ValuationAdjustment, ValuationTask
from app.schemas.valuation import AdjustmentOut, ValuationTaskCreate, ValuationTaskListOut, ValuationTaskOut
from app.services.valuation import create_valuation_task

router = APIRouter()


def to_out(task: ValuationTask, adjustments: list[ValuationAdjustment] | None = None) -> ValuationTaskOut:
    adjs = adjustments if adjustments is not None else []
    return ValuationTaskOut(
        id=task.id,
        user_id=task.user_id,
        subject_info=task.subject_info,
        method=task.method,
        result_price=task.result_price,
        unit_price=task.unit_price,
        status=task.status,
        remark=task.remark,
        created_at=task.created_at,
        adjustments=[
            AdjustmentOut(
                id=a.id,
                comparable_id=a.comparable_id,
                factor_scores=a.factor_scores,
                adjusted_price=a.adjusted_price,
                weight=a.weight,
            )
            for a in adjs
        ],
    )


@router.post("", response_model=ValuationTaskOut)
def create_task(
    body: ValuationTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = create_valuation_task(
        db=db,
        user_id=user.id,
        subject_info=body.subject_info.model_dump(),
        method=body.method,
        remark=body.remark,
        radius_m=body.radius_m,
        max_comparables=body.max_comparables,
    )
    adjs = db.query(ValuationAdjustment).filter(ValuationAdjustment.task_id == task.id).all()
    return to_out(task, adjs)


@router.get("", response_model=ValuationTaskListOut)
def list_tasks(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ValuationTask)
    if user.role != UserRole.admin:
        q = q.filter(ValuationTask.user_id == user.id)
    total = q.count()
    items = q.order_by(ValuationTask.created_at.desc()).offset((page - 1) * size).limit(size).all()
    result = []
    for t in items:
        adjs = db.query(ValuationAdjustment).filter(ValuationAdjustment.task_id == t.id).all()
        result.append(to_out(t, adjs))
    return ValuationTaskListOut(total=total, items=result)


@router.get("/{task_id}", response_model=ValuationTaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(ValuationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="估价任务不存在")
    if user.role != UserRole.admin and task.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看该任务")
    adjs = db.query(ValuationAdjustment).filter(ValuationAdjustment.task_id == task.id).all()
    return to_out(task, adjs)
