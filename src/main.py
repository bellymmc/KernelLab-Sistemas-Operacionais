"""Interface de terminal do KernelLab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .devices import ACCESS_MATRIX, EXCLUSIVE, EXECUTE, READ, USE, WRITE, simulate_disk_concurrency
from .memory import fifo as mem_fifo, lru, optimal
from .metrics import averages, calculate_metrics, excessive_delay_candidates, execution_order
from .schedulers import Process, fcfs, priority, round_robin, sjf

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSES = ROOT / "data" / "processes.json"
DEFAULT_PAGES = ROOT / "data" / "pages.json"


def load_processes(path: Path) -> list[Process]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        Process(
            pid=item["pid"],
            function=item["function"],
            arrival=int(item["arrival"]),
            burst=int(item["burst"]),
            priority=int(item["priority"]),
            memory_mb=int(item.get("memory_mb", 0)),
            devices=tuple(item.get("devices", [])),
        )
        for item in data
    ]


def load_pages(path: Path) -> tuple[list[int], int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [int(x) for x in data["references"]], int(data["frames"])


def parse_pages(raw: str) -> list[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    text_rows = [[str(x) for x in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in text_rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))
    line = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print(line)
    print("| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(line)
    for row in text_rows:
        print("| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) + " |")
    print(line)


def gantt_text(result) -> str:
    return " | ".join(f"{s.pid} [{s.start}-{s.end}]" for s in result.gantt)


def export_charts(results, memory_results, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib não instalado; gráficos não foram exportados.")
        return

    names = [r.name for r in results]
    waits = [averages(r)["waiting"] for r in results]
    responses = [averages(r)["response"] for r in results]
    turnarounds = [averages(r)["turnaround"] for r in results]

    x = range(len(names))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - width for i in x], waits, width, label="Espera")
    ax.bar(list(x), responses, width, label="Resposta")
    ax.bar([i + width for i in x], turnarounds, width, label="Retorno")
    ax.set_xticks(list(x), names)
    ax.set_ylabel("Unidades de tempo")
    ax.set_title("Comparação das métricas médias de escalonamento")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "comparacao_escalonadores.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, [r.context_switches for r in results])
    ax.set_ylabel("Trocas de contexto")
    ax.set_title("Trocas de contexto por algoritmo")
    fig.tight_layout()
    fig.savefig(output / "trocas_contexto.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    mem_names = [m.algorithm for m in memory_results]
    ax.bar(mem_names, [m.faults for m in memory_results], label="Page faults")
    ax.bar(mem_names, [m.hits for m in memory_results], bottom=[m.faults for m in memory_results], label="Page hits")
    ax.set_ylabel("Quantidade")
    ax.set_title("Resultados dos algoritmos de substituição de páginas")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "memoria_hits_faults.png", dpi=180)
    plt.close(fig)

    for result in results:
        fig, ax = plt.subplots(figsize=(10, 2.6))
        y = 0
        for sl in result.gantt:
            if sl.pid == "IDLE":
                continue
            ax.barh(y, sl.duration, left=sl.start, edgecolor="black")
            ax.text(sl.start + sl.duration / 2, y, sl.pid, ha="center", va="center", fontsize=9)
        ax.set_yticks([])
        ax.set_xlabel("Tempo")
        ax.set_title(f"Diagrama de Gantt - {result.name}")
        ax.set_xlim(0, max(s.end for s in result.gantt))
        fig.tight_layout()
        safe = result.name.lower().replace(" ", "_")
        fig.savefig(output / f"gantt_{safe}.png", dpi=180)
        plt.close(fig)


def run(process_file: Path, page_file: Path, quantum: int, frames: int | None, pages_override: str | None, export: Path | None) -> None:
    processes = load_processes(process_file)
    page_refs, default_frames = load_pages(page_file)
    if pages_override:
        page_refs = parse_pages(pages_override)
    frame_count = frames if frames is not None else default_frames

    results = [fcfs(processes), sjf(processes), round_robin(processes, quantum), priority(processes)]

    print("\n=== KERNELLAB: ESCALONAMENTO DE CPU ===")
    for result in results:
        print(f"\n{result.name}")
        print("Ordem:", " -> ".join(execution_order(result)))
        print("Gantt:", gantt_text(result))
        metric_rows = calculate_metrics(result)
        print_table(
            ["PID", "Espera", "Retorno", "Resposta"],
            [[m.pid, m.waiting, m.turnaround, m.response] for m in metric_rows],
        )
        avg = averages(result)
        print(
            f"Médias: espera={avg['waiting']:.2f}, retorno={avg['turnaround']:.2f}, "
            f"resposta={avg['response']:.2f}; trocas de contexto={result.context_switches}"
        )
        delayed = excessive_delay_candidates(result)
        print("Indicador de atraso excessivo:", ", ".join(delayed) if delayed else "nenhum")

    print("\n=== KERNELLAB: MEMÓRIA ===")
    memory_results = [mem_fifo(page_refs, frame_count), lru(page_refs, frame_count), optimal(page_refs, frame_count)]
    for mem in memory_results:
        print(f"\n{mem.algorithm} - hits={mem.hits}, faults={mem.faults}, taxa={mem.fault_rate:.2%}")
        rows = []
        for i, step in enumerate(mem.steps, start=1):
            rows.append([i, step.reference, " ".join("-" if f is None else str(f) for f in step.frames), "HIT" if step.hit else "FAULT"])
        print_table(["#", "Ref", "Frames", "Resultado"], rows)

    print("\n=== KERNELLAB: CONTROLE DE ACESSO ===")
    permission_name = {READ: "L", WRITE: "G", EXECUTE: "X", USE: "U", EXCLUSIVE: "E"}
    matrix_rows = []
    for pid in sorted(ACCESS_MATRIX):
        for device in ("disco", "rede", "audio", "logs"):
            permissions = ACCESS_MATRIX.get(pid, {}).get(device, set())
            if permissions:
                matrix_rows.append([pid, device, "".join(permission_name[p] for p in (READ, WRITE, EXECUTE, USE, EXCLUSIVE) if p in permissions)])
    print_table(["PID", "Dispositivo", "Permissões (L/G/X/U/E)"], matrix_rows)

    print("\nSimulação concorrente no disco com mutex:")
    manager = simulate_disk_concurrency()
    for event in manager.events:
        print(" -", event)
    print("Máximo de processos simultâneos dentro da seção crítica do disco:", manager.max_parallel_inside["disco"])

    print("\n=== ANÁLISE FINAL ===")
    print("- Menor espera média: SJF e Prioridade (empate neste conjunto de dados).")
    print("- Melhor resposta média: Round Robin, pois distribui a CPU em fatias curtas.")
    print("- P4 (alarme): SJF/Prioridade iniciam em t=8; RR inicia em t=9; FCFS apenas em t=21.")
    print("- Maior risco teórico de starvation: Prioridade (P5 é o de menor prioridade); SJF também pode postergar jobs longos.")
    print("- Maior justiça temporal: Round Robin, ao garantir oportunidades periódicas de CPU.")
    print("- Recomendação para MedControl: política híbrida/preemptiva por prioridade para eventos críticos, com Round Robin entre processos de mesma classe e aging para reduzir starvation.")

    if export:
        export_charts(results, memory_results, export)
        print(f"\nGráficos exportados para: {export}")


def main() -> None:
    parser = argparse.ArgumentParser(description="KernelLab - simulador de CPU, memória e dispositivos")
    parser.add_argument("--processes", type=Path, default=DEFAULT_PROCESSES, help="Arquivo JSON de processos")
    parser.add_argument("--page-file", type=Path, default=DEFAULT_PAGES, help="Arquivo JSON de páginas")
    parser.add_argument("--quantum", type=int, default=3, help="Quantum do Round Robin")
    parser.add_argument("--frames", type=int, default=None, help="Quantidade de frames")
    parser.add_argument("--pages", type=str, default=None, help="Sequência alternativa, ex.: 1,2,3,1,4")
    parser.add_argument("--export", type=Path, default=None, help="Diretório para exportar gráficos")
    args = parser.parse_args()
    run(args.processes, args.page_file, args.quantum, args.frames, args.pages, args.export)


if __name__ == "__main__":
    main()
