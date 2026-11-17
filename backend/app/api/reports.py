import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.report import Report
from app.models.user import User, UserRole
from app.models.valuation import ValuationAdjustment, ValuationTask
from app.schemas.report import ReportGenerateRequest, ReportListOut, ReportOut
from app.services.report import generate_valuation_report_docx

router = APIRouter()


def _can_access_task(user: User, task: ValuationTask) -> bool:
    return user.role == UserRole.admin or task.user_id == user.id


@router.post("/generate", response_model=ReportOut)
def generate_report(
    body: ReportGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(ValuationTask, body.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="估价任务不存在")
    if not _can_access_task(user, task):
        raise HTTPException(status_code=403, detail="无权为该任务生成报告")
    if body.file_format != "docx":
        raise HTTPException(status_code=400, detail="当前仅支持 docx 报告")

    adjustments = db.query(ValuationAdjustment).filter(ValuationAdjustment.task_id == task.id).all()
    file_name, file_path = generate_valuation_report_docx(task, adjustments)
    report = Report(
        task_id=task.id,
        file_format=body.file_format,
        file_name=file_name,
        file_path=file_path,
    )
    db.add(report)
    db.flush()
    return ReportOut.model_validate(report)


@router.get("", response_model=ReportListOut)
def list_reports(
    task_id: int | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Report).join(ValuationTask, Report.task_id == ValuationTask.id)
    if task_id is not None:
        q = q.filter(Report.task_id == task_id)
    if user.role != UserRole.admin:
        q = q.filter(ValuationTask.user_id == user.id)
    total = q.count()
    items = q.order_by(Report.generated_at.desc()).offset((page - 1) * size).limit(size).all()
    return ReportListOut(total=total, items=[ReportOut.model_validate(i) for i in items])


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    task = db.get(ValuationTask, report.task_id)
    if task is None or not _can_access_task(user, task):
        raise HTTPException(status_code=403, detail="无权查看该报告")
    return ReportOut.model_validate(report)


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    task = db.get(ValuationTask, report.task_id)
    if task is None or not _can_access_task(user, task):
        raise HTTPException(status_code=403, detail="无权下载该报告")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="报告文件不存在，请重新生成")
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path=report.file_path, filename=report.file_name, media_type=media)
