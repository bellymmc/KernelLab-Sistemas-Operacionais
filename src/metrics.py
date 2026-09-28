"""Cálculo de métricas e comparações dos escalonadores."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from .schedulers import ScheduleResult


@dataclass(frozen=True)
class ProcessMetrics:
    pid: str
    waiting: int
    turnaround: int
    response: int


def calculate_metrics(result: ScheduleResult) -> list[ProcessMetrics]:
    rows: list[ProcessMetrics] = []
    for p in result.processes:
        turnaround = result.completion[p.pid] - p.arrival
        waiting = turnaround - p.burst
        response = result.first_start[p.pid] - p.arrival
        rows.append(ProcessMetrics(p.pid, waiting, turnaround, response))
    return rows


def averages(result: ScheduleResult) -> dict[str, float]:
    rows = calculate_metrics(result)
    return {
        "waiting": mean(r.waiting for r in rows),
        "turnaround": mean(r.turnaround for r in rows),
        "response": mean(r.response for r in rows),
    }


def execution_order(result: ScheduleResult) -> list[str]:
    return [s.pid for s in result.gantt if s.pid != "IDLE"]


def excessive_delay_candidates(result: ScheduleResult) -> list[str]:
    """Sinaliza processos com espera >= 1,5x a média (indicador didático, não starvation real)."""
    rows = calculate_metrics(result)
    avg = mean(r.waiting for r in rows)
    threshold = 1.5 * avg
    return [r.pid for r in rows if r.waiting >= threshold]


def summary(result: ScheduleResult) -> dict[str, object]:
    avg = averages(result)
    return {
        "algorithm": result.name,
        "avg_waiting": avg["waiting"],
        "avg_turnaround": avg["turnaround"],
        "avg_response": avg["response"],
        "context_switches": result.context_switches,
        "excessive_delay": excessive_delay_candidates(result),
    }
