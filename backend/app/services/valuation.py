from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.comparable import Comparable
from app.models.valuation import FactorConfig, ValuationAdjustment, ValuationTask


@dataclass
class CalcResult:
    result_price: float
    unit_price: float
    adjustments: list[dict[str, Any]]
    meta: dict[str, Any] | None = None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _load_factor_rules(db: Session) -> dict[str, dict[str, Any]]:
    defaults: dict[str, dict[str, Any]] = {
        "area": {"per_10pct": 0.1, "min": 0.9, "max": 1.1},
        "floor": {"per_relative": 0.05, "min": 0.95, "max": 1.05},
        "build_year": {"per_year": 0.005, "min": 0.9, "max": 1.1},
        "distance": {"base_m": 500.0},
    }
    rows = db.query(FactorConfig).filter(FactorConfig.type == "comparison").all()
    for r in rows:
        if isinstance(r.rules, dict):
            defaults[r.name] = {**defaults.get(r.name, {}), **r.rules}
    return defaults


def calculate_comparison(
    db: Session,
    subject: dict[str, Any],
    radius_m: int = 2000,
    max_comparables: int = 5,
) -> CalcResult:
    lng = float(subject["lng"])
    lat = float(subject["lat"])
    area = float(subject["area"])
    subject_floor = int(subject.get("floor") or 0)
    subject_total = int(subject.get("total_floor") or 0)
    subject_year = int(subject.get("build_year") or 0)
    rules = _load_factor_rules(db)

    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    dist_expr = func.ST_DistanceSphere(Comparable.location, point).label("dist")
    rows = (
        db.query(Comparable, dist_expr)
        .filter(dist_expr <= radius_m)
        .order_by(dist_expr)
        .limit(max_comparables)
        .all()
    )
    if not rows:
        return CalcResult(result_price=0.0, unit_price=0.0, adjustments=[], meta={"factor_rules": rules})

    adjustments: list[dict[str, Any]] = []
    weighted_sum = 0.0
    weight_sum = 0.0

    area_rule = rules.get("area", {})
    floor_rule = rules.get("floor", {})
    year_rule = rules.get("build_year", {})
    dist_rule = rules.get("distance", {})

    for comp, dist in rows:
        base_unit = float(comp.deal_price) / float(comp.area) if comp.area else 0.0
        factors: dict[str, float] = {}

        # 面积修正：与标的面积差异每10%按 per_10pct 调整
        if area > 0 and comp.area:
            diff = (comp.area - area) / area
            per_10 = float(area_rule.get("per_10pct", 0.1))
            factors["area"] = _clamp(1.0 + diff * per_10, float(area_rule.get("min", 0.9)), float(area_rule.get("max", 1.1)))
        else:
            factors["area"] = 1.0

        # 楼层修正：相对楼层差异
        if subject_total and comp.total_floor and subject_floor and comp.floor:
            rel_s = subject_floor / subject_total
            rel_c = comp.floor / comp.total_floor
            per_rel = float(floor_rule.get("per_relative", 0.05))
            factors["floor"] = _clamp(1.0 + (rel_s - rel_c) * per_rel, float(floor_rule.get("min", 0.95)), float(floor_rule.get("max", 1.05)))
        else:
            factors["floor"] = 1.0

        # 建成年代修正
        if subject_year and comp.build_year:
            year_diff = subject_year - comp.build_year
            per_year = float(year_rule.get("per_year", 0.005))
            factors["build_year"] = _clamp(1.0 + year_diff * per_year, float(year_rule.get("min", 0.9)), float(year_rule.get("max", 1.1)))
        else:
            factors["build_year"] = 1.0

        d = float(dist or 0.0)
        base_m = float(dist_rule.get("base_m", 500.0)) or 500.0
        weight = 1.0 / (1.0 + d / base_m)
        total_factor = factors["area"] * factors["floor"] * factors["build_year"]
        adjusted_unit = base_unit * total_factor
        adjusted_price = adjusted_unit * area

        adjustments.append(
            {
                "comparable_id": comp.id,
                "base_unit_price": round(base_unit, 2),
                "distance_m": round(d, 1),
                "factor_scores": {k: round(v, 4) for k, v in factors.items()},
                "total_factor": round(total_factor, 4),
                "adjusted_unit_price": round(adjusted_unit, 2),
                "adjusted_price": round(adjusted_price, 2),
                "weight": round(weight, 4),
            }
        )
        weighted_sum += adjusted_unit * weight
        weight_sum += weight

    unit_price = (weighted_sum / weight_sum) if weight_sum else 0.0
    result_price = unit_price * area
    return CalcResult(
        result_price=round(result_price, 2),
        unit_price=round(unit_price, 2),
        adjustments=adjustments,
        meta={"factor_rules": rules},
    )


def calculate_income(subject: dict[str, Any]) -> CalcResult:
    area = float(subject.get("area") or 0.0)
    monthly_rent = float(subject.get("monthly_rent") or 0.0)  # 元/月
    vacancy_rate = float(subject.get("vacancy_rate") or 0.05)
    annual_cost_rate = float(subject.get("annual_cost_rate") or 0.2)  # 运营/维修等占毛租金比例
    cap_rate = float(subject.get("cap_rate") or subject.get("yield_rate") or 0.03)
    if monthly_rent <= 0 or cap_rate <= 0:
        return CalcResult(0.0, 0.0, [], meta={"reason": "缺少 monthly_rent 或 cap_rate/yield_rate"})
    annual_gross = monthly_rent * 12.0
    annual_net = annual_gross * (1.0 - vacancy_rate) * (1.0 - annual_cost_rate)
    result_price = annual_net / cap_rate
    unit_price = (result_price / area) if area > 0 else 0.0
    return CalcResult(
        round(result_price, 2),
        round(unit_price, 2),
        [],
        meta={
            "annual_gross": round(annual_gross, 2),
            "annual_net": round(annual_net, 2),
            "cap_rate": cap_rate,
            "vacancy_rate": vacancy_rate,
            "annual_cost_rate": annual_cost_rate,
        },
    )


def calculate_cost(subject: dict[str, Any]) -> CalcResult:
    area = float(subject.get("area") or 0.0)
    land_unit_price = float(subject.get("land_unit_price") or 0.0)  # 元/㎡
    replacement_unit_cost = float(subject.get("replacement_unit_cost") or 0.0)  # 重置单价 元/㎡
    depreciation_rate = float(subject.get("depreciation_rate") or 0.0)  # 0~1
    other_cost = float(subject.get("other_cost") or 0.0)
    if area <= 0 or (land_unit_price <= 0 and replacement_unit_cost <= 0):
        return CalcResult(0.0, 0.0, [], meta={"reason": "缺少 area、land_unit_price 或 replacement_unit_cost"})
    depreciation_rate = _clamp(depreciation_rate, 0.0, 0.95)
    land_value = land_unit_price * area
    building_value = replacement_unit_cost * area * (1.0 - depreciation_rate)
    result_price = land_value + building_value + other_cost
    unit_price = result_price / area if area > 0 else 0.0
    return CalcResult(
        round(result_price, 2),
        round(unit_price, 2),
        [],
        meta={
            "land_value": round(land_value, 2),
            "building_value": round(building_value, 2),
            "depreciation_rate": depreciation_rate,
            "other_cost": other_cost,
        },
    )


def create_valuation_task(
    db: Session,
    user_id: int,
    subject_info: dict[str, Any],
    method: str,
    remark: str,
    radius_m: int,
    max_comparables: int,
) -> ValuationTask:
    task = ValuationTask(
        user_id=user_id,
        subject_info=subject_info,
        method=method,
        status="calculating",
        remark=remark,
    )
    db.add(task)
    db.flush()

    if method == "comparison":
        calc = calculate_comparison(db, subject_info, radius_m, max_comparables)
        task.result_price = calc.result_price
        task.unit_price = calc.unit_price
        task.status = "completed" if calc.adjustments else "no_comparables"
        # 保存计算元信息（含系数规则）到 subject_info 快照外的 remark 不合适，放入首条无；这里并入 task.subject_info 的副本会改输入，改为附加到 status 信息不便。
        # 简化：将 meta 合并写回 subject_info 的 _calc_meta 字段用于追溯
        si = dict(subject_info)
        if calc.meta:
            si["_calc_meta"] = calc.meta
            task.subject_info = si
        for adj in calc.adjustments:
            db.add(
                ValuationAdjustment(
                    task_id=task.id,
                    comparable_id=adj["comparable_id"],
                    factor_scores={
                        **adj["factor_scores"],
                        "base_unit_price": adj["base_unit_price"],
                        "distance_m": adj["distance_m"],
                        "total_factor": adj["total_factor"],
                        "adjusted_unit_price": adj["adjusted_unit_price"],
                    },
                    adjusted_price=adj["adjusted_price"],
                    weight=adj["weight"],
                )
            )
    elif method == "income":
        calc = calculate_income(subject_info)
        task.result_price = calc.result_price
        task.unit_price = calc.unit_price
        task.status = "completed" if calc.result_price > 0 else "insufficient_params"
        if calc.meta:
            si = dict(subject_info)
            si["_calc_meta"] = calc.meta
            task.subject_info = si
    elif method == "cost":
        calc = calculate_cost(subject_info)
        task.result_price = calc.result_price
        task.unit_price = calc.unit_price
        task.status = "completed" if calc.result_price > 0 else "insufficient_params"
        if calc.meta:
            si = dict(subject_info)
            si["_calc_meta"] = calc.meta
            task.subject_info = si
    else:
        task.status = "unsupported_method"

    db.add(task)
    db.flush()
    return task
