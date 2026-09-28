"""Simulação de substituição de páginas: FIFO, LRU e Optimal."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MemoryStep:
    reference: int
    frames: tuple[int | None, ...]
    hit: bool


@dataclass(frozen=True)
class MemoryResult:
    algorithm: str
    steps: tuple[MemoryStep, ...]
    hits: int
    faults: int

    @property
    def fault_rate(self) -> float:
        total = self.hits + self.faults
        return self.faults / total if total else 0.0


def _validate(references: Iterable[int], frame_count: int) -> list[int]:
    refs = list(references)
    if frame_count <= 0:
        raise ValueError("A quantidade de frames deve ser maior que zero.")
    if not refs:
        raise ValueError("A sequência de referências não pode estar vazia.")
    return refs


def _snapshot(frames: list[int], frame_count: int) -> tuple[int | None, ...]:
    return tuple(frames + [None] * (frame_count - len(frames)))


def fifo(references: Iterable[int], frame_count: int) -> MemoryResult:
    refs = _validate(references, frame_count)
    frames: list[int] = []
    order: deque[int] = deque()
    steps: list[MemoryStep] = []
    hits = faults = 0

    for ref in refs:
        hit = ref in frames
        if hit:
            hits += 1
        else:
            faults += 1
            if len(frames) < frame_count:
                frames.append(ref)
                order.append(ref)
            else:
                victim = order.popleft()
                frames[frames.index(victim)] = ref
                order.append(ref)
        steps.append(MemoryStep(ref, _snapshot(frames, frame_count), hit))

    return MemoryResult("FIFO", tuple(steps), hits, faults)


def lru(references: Iterable[int], frame_count: int) -> MemoryResult:
    refs = _validate(references, frame_count)
    frames: list[int] = []
    last_used: dict[int, int] = {}
    steps: list[MemoryStep] = []
    hits = faults = 0

    for index, ref in enumerate(refs):
        hit = ref in frames
        if hit:
            hits += 1
        else:
            faults += 1
            if len(frames) < frame_count:
                frames.append(ref)
            else:
                victim = min(frames, key=lambda page: last_used[page])
                frames[frames.index(victim)] = ref
        last_used[ref] = index
        steps.append(MemoryStep(ref, _snapshot(frames, frame_count), hit))

    return MemoryResult("LRU", tuple(steps), hits, faults)


def optimal(references: Iterable[int], frame_count: int) -> MemoryResult:
    refs = _validate(references, frame_count)
    frames: list[int] = []
    steps: list[MemoryStep] = []
    hits = faults = 0

    for index, ref in enumerate(refs):
        hit = ref in frames
        if hit:
            hits += 1
        else:
            faults += 1
            if len(frames) < frame_count:
                frames.append(ref)
            else:
                future = refs[index + 1 :]

                def next_use(page: int) -> float:
                    try:
                        return float(future.index(page))
                    except ValueError:
                        return float("inf")

                victim = max(frames, key=next_use)
                frames[frames.index(victim)] = ref
        steps.append(MemoryStep(ref, _snapshot(frames, frame_count), hit))

    return MemoryResult("Optimal", tuple(steps), hits, faults)
