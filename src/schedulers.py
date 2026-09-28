"""Algoritmos de escalonamento de CPU usados pelo KernelLab."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class Process:
    pid: str
    function: str
    arrival: int
    burst: int
    priority: int
    memory_mb: int = 0
    devices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Slice:
    pid: str
    start: int
    end: int

    @property
    def duration(self) -> int:
        return self.end - self.start


@dataclass
class ScheduleResult:
    name: str
    gantt: list[Slice]
    completion: dict[str, int]
    first_start: dict[str, int]
    processes: list[Process]

    @property
    def context_switches(self) -> int:
        active = [s for s in self.gantt if s.pid != "IDLE"]
        return sum(1 for a, b in zip(active, active[1:]) if a.pid != b.pid)


def _validate(processes: Iterable[Process]) -> list[Process]:
    items = list(processes)
    if not items:
        raise ValueError("A lista de processos não pode estar vazia.")
    pids = [p.pid for p in items]
    if len(pids) != len(set(pids)):
        raise ValueError("Os identificadores de processo devem ser únicos.")
    for p in items:
        if p.arrival < 0 or p.burst <= 0 or p.priority < 0:
            raise ValueError(f"Dados inválidos para {p.pid}.")
    return items


def _non_preemptive(
    processes: Iterable[Process], name: str, key: Callable[[Process], tuple]
) -> ScheduleResult:
    items = _validate(processes)
    time = 0
    done: set[str] = set()
    gantt: list[Slice] = []
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}

    while len(done) < len(items):
        ready = [p for p in items if p.pid not in done and p.arrival <= time]
        if not ready:
            next_arrival = min(p.arrival for p in items if p.pid not in done)
            gantt.append(Slice("IDLE", time, next_arrival))
            time = next_arrival
            continue

        current = min(ready, key=key)
        start = time
        end = start + current.burst
        first_start.setdefault(current.pid, start)
        completion[current.pid] = end
        gantt.append(Slice(current.pid, start, end))
        time = end
        done.add(current.pid)

    return ScheduleResult(name, gantt, completion, first_start, items)


def fcfs(processes: Iterable[Process]) -> ScheduleResult:
    """First Come, First Served - não preemptivo."""
    return _non_preemptive(processes, "FCFS", lambda p: (p.arrival, p.pid))


def sjf(processes: Iterable[Process]) -> ScheduleResult:
    """Shortest Job First - não preemptivo."""
    return _non_preemptive(
        processes, "SJF", lambda p: (p.burst, p.arrival, p.pid)
    )


def priority(processes: Iterable[Process]) -> ScheduleResult:
    """Prioridade não preemptiva. Menor número = maior prioridade."""
    return _non_preemptive(
        processes, "Prioridade", lambda p: (p.priority, p.arrival, p.pid)
    )


def round_robin(processes: Iterable[Process], quantum: int = 3) -> ScheduleResult:
    """Round Robin preemptivo com fila FIFO e quantum configurável."""
    items = sorted(_validate(processes), key=lambda p: (p.arrival, p.pid))
    if quantum <= 0:
        raise ValueError("O quantum deve ser maior que zero.")

    remaining = {p.pid: p.burst for p in items}
    queue: deque[str] = deque()
    gantt: list[Slice] = []
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    by_pid = {p.pid: p for p in items}

    time = 0
    idx = 0
    while idx < len(items) or queue:
        if not queue:
            next_arrival = items[idx].arrival
            if time < next_arrival:
                gantt.append(Slice("IDLE", time, next_arrival))
                time = next_arrival
            while idx < len(items) and items[idx].arrival <= time:
                queue.append(items[idx].pid)
                idx += 1

        pid = queue.popleft()
        first_start.setdefault(pid, time)
        run = min(quantum, remaining[pid])
        start = time
        time += run
        remaining[pid] -= run
        gantt.append(Slice(pid, start, time))

        while idx < len(items) and items[idx].arrival <= time:
            queue.append(items[idx].pid)
            idx += 1

        if remaining[pid] > 0:
            queue.append(pid)
        else:
            completion[pid] = time

    return ScheduleResult("Round Robin", gantt, completion, first_start, items)
