"""Controle de acesso e demonstração de exclusão mútua em dispositivos."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

READ = "R"
WRITE = "W"
EXECUTE = "X"
USE = "U"
EXCLUSIVE = "E"

# Princípio do menor privilégio, alinhado às funções informadas no enunciado.
ACCESS_MATRIX: dict[str, dict[str, set[str]]] = {
    "P1": {
        "rede": {READ, WRITE, USE},
        "logs": {WRITE, USE},
    },
    "P2": {
        "rede": {READ, WRITE, USE},
        "logs": {WRITE, USE},
    },
    "P3": {
        "disco": {READ, WRITE, USE},
        "logs": {READ, WRITE, USE},
    },
    "P4": {
        "audio": {USE, EXCLUSIVE},
        "rede": {WRITE, USE, EXCLUSIVE},
        "logs": {WRITE, USE},
    },
    "P5": {
        "disco": {READ, WRITE, USE, EXCLUSIVE},
        "logs": {WRITE, USE},
    },
    "P6": {
        "disco": {READ, WRITE, EXECUTE, USE},
        "rede": {READ, WRITE, USE},
        "logs": {WRITE, USE},
    },
}


@dataclass(frozen=True)
class AccessDecision:
    pid: str
    device: str
    operation: str
    allowed: bool


def is_allowed(pid: str, device: str, operation: str) -> bool:
    return operation in ACCESS_MATRIX.get(pid, {}).get(device, set())


def check_access(pid: str, device: str, operation: str) -> AccessDecision:
    return AccessDecision(pid, device, operation, is_allowed(pid, device, operation))


class DeviceManager:
    """Mantém um mutex por dispositivo para impedir seção crítica simultânea."""

    def __init__(self, devices: tuple[str, ...] = ("disco", "rede", "audio", "logs")):
        self._locks = {device: threading.Lock() for device in devices}
        self._state_lock = threading.Lock()
        self._active = {device: 0 for device in devices}
        self.max_parallel_inside = {device: 0 for device in devices}
        self.events: list[str] = []

    def use_device(self, pid: str, device: str, duration: float = 0.03) -> None:
        if not is_allowed(pid, device, USE):
            self.events.append(f"NEGADO: {pid} não possui permissão U em {device}.")
            return
        if device not in self._locks:
            raise ValueError(f"Dispositivo desconhecido: {device}")

        self.events.append(f"FILA: {pid} solicitou {device}.")
        with self._locks[device]:
            with self._state_lock:
                self._active[device] += 1
                self.max_parallel_inside[device] = max(
                    self.max_parallel_inside[device], self._active[device]
                )
            self.events.append(f"ENTROU: {pid} está usando {device}.")
            time.sleep(duration)
            self.events.append(f"SAIU: {pid} liberou {device}.")
            with self._state_lock:
                self._active[device] -= 1


def simulate_disk_concurrency() -> DeviceManager:
    """P3, P5 e P6 disputam o disco; o mutex serializa o acesso."""
    manager = DeviceManager()
    pids = ["P3", "P5", "P6"]

    def worker(pid: str, delay: float) -> None:
        time.sleep(delay)
        manager.use_device(pid, "disco")

    threads = [
        threading.Thread(target=worker, args=(pid, i * 0.005), daemon=True)
        for i, pid in enumerate(pids)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return manager
