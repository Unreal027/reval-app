from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.shared import Pt

from app.core.config import get_settings
from app.models.valuation import ValuationAdjustment, ValuationTask


METHOD_LABELS = {
    "comparison": "市场比较法",
    "income": "收益法",
    "cost": "成本法",
}


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _add_kv_table(doc: Document, rows: list[tuple[str, str]]) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light List"
    hdr = table.rows[0].cells
    hdr[0].text = "项目"
    hdr[1].text = "内容"
    for k, v in rows:
        r = table.add_row().cells
        r[0].text = str(k)
        r[1].text = str(v)


def generate_valuation_report_docx(
    task: ValuationTask,
    adjustments: list[ValuationAdjustment],
) -> tuple[str, str]:
    settings = get_settings()
    reports_dir = settings.reports_dir
    _ensure_dir(reports_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"valuation_task_{task.id}_{ts}.docx"
    file_path = os.path.join(reports_dir, file_name)

    si: dict[str, Any] = task.subject_info or {}
    doc = Document()

    title = doc.add_heading("房地产估价报告（系统生成）", level=0)
    for run in title.runs:
        run.font.size = Pt(20)

    doc.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph(f"任务编号：{task.id}    估价方法：{METHOD_LABELS.get(task.method, task.method)}    状态：{task.status}")

    doc.add_heading("一、估价对象信息", level=1)
    subject_rows = [
        ("小区/项目", si.get("community", "")),
        ("地址", si.get("address", "")),
        ("城市/区域", f"{si.get('city','')} {si.get('district','')}".strip()),
        ("坐标(经度,纬度)", f"{si.get('lng','')}, {si.get('lat','')}"),
        ("建筑面积(㎡)", str(si.get("area", ""))),
        ("楼层/总层", f"{si.get('floor','')}/{si.get('total_floor','')}"),
        ("朝向", si.get("orientation", "")),
        ("建成年份", str(si.get("build_year", ""))),
        ("用途", si.get("purpose", "")),
    ]
    _add_kv_table(doc, subject_rows)

    doc.add_heading("二、估价结果", level=1)
    result_rows = [
        ("评估单价(元/㎡)", f"{task.unit_price:,.2f}" if task.unit_price else "0.00"),
        ("评估总价(元)", f"{task.result_price:,.2f}" if task.result_price else "0.00"),
        ("备注", task.remark or ""),
    ]
    _add_kv_table(doc, result_rows)

    calc_meta = si.get("_calc_meta")
    if calc_meta:
        doc.add_heading("三、计算参数/元信息", level=1)
        meta_rows = [(str(k), str(v)) for k, v in calc_meta.items()]
        _add_kv_table(doc, meta_rows)

    if task.method == "comparison":
        doc.add_heading("四、可比案例修正明细", level=1)
        if not adjustments:
            doc.add_paragraph("未找到可用可比案例或未生成修正记录。")
        else:
            table = doc.add_table(rows=1, cols=6)
            table.style = "Light Grid"
            headers = ["案例ID", "基准单价", "距离(m)", "综合系数", "修正后单价", "权重/修正后总价"]
            for i, h in enumerate(headers):
                table.rows[0].cells[i].text = h
            for a in adjustments:
                fs = a.factor_scores or {}
                row = table.add_row().cells
                row[0].text = str(a.comparable_id)
                row[1].text = str(fs.get("base_unit_price", ""))
                row[2].text = str(fs.get("distance_m", ""))
                row[3].text = str(fs.get("total_factor", ""))
                row[4].text = str(fs.get("adjusted_unit_price", ""))
                row[5].text = f"w={a.weight}, {a.adjusted_price:,.2f}"
    else:
        doc.add_heading("四、方法说明", level=1)
        if task.method == "income":
            doc.add_paragraph("本次采用收益法（简化模型）估算，基于年净收益资本化计算结果，具体参数见“计算参数/元信息”。")
        elif task.method == "cost":
            doc.add_paragraph("本次采用成本法（简化模型）估算，基于土地价值与建筑重置成本扣减折旧计算结果，具体参数见“计算参数/元信息”。")
        else:
            doc.add_paragraph("当前方法暂未实现详细测算说明。")

    doc.add_heading("五、免责声明", level=1)
    doc.add_paragraph(
        "1. 本报告由系统根据录入数据与预设规则自动生成，仅供内部参考或辅助决策使用。"
    )
    doc.add_paragraph(
        "2. 估价结果受案例质量、参数设置、市场波动及数据完整性影响，实际价值可能存在偏差。"
    )
    doc.add_paragraph(
        "3. 如用于正式业务、抵押、司法或其他法定用途，请由具备资质的估价专业人员复核并出具正式报告。"
    )

    doc.save(file_path)
    return file_name, file_path
