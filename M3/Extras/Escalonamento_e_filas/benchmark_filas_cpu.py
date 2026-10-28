#!/usr/bin/env python3
"""Mede a vazão de um lote de tarefas CPU-bound com diferentes números de processos.

Uso:
  python benchmark_filas_cpu.py --tasks 120 --rounds 50000 --workers 1,2,4,6,8 --repeats 3

Não cria Kubernetes nem simula heterogeneidade. Saídas são medições reais na máquina.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import os
import statistics
import time


def tarefa_cpu(job_id: int, rounds: int) -> int:
    state = hashlib.sha256(f"tarefa-{job_id}".encode()).digest()
    for _ in range(rounds):
        state = hashlib.sha256(state).digest()
    return state[0]


def executar_lote(num_tasks: int, rounds: int, workers: int) -> float:
    inicio = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        resultados = list(executor.map(tarefa_cpu, range(num_tasks), [rounds] * num_tasks, chunksize=1))
    assert len(resultados) == num_tasks
    return time.perf_counter() - inicio


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, default=120)
    parser.add_argument("--rounds", type=int, default=50000)
    parser.add_argument("--workers", type=str, default="1,2,4,6,8")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=str, default="medicoes_filas_usl.csv")
    args = parser.parse_args()
    workers_values = sorted(set(int(w.strip()) for w in args.workers.split(",")))
    if min(workers_values) < 1 or args.tasks < 1 or args.rounds < 1 or args.repeats < 1:
        parser.error("Todos os valores numéricos devem ser positivos")
    if 1 not in workers_values:
        parser.error("Inclua 1 na lista de workers para calcular speedup")
    print(f"CPUs lógicas detectadas: {os.cpu_count()} (a cota do contêiner pode ser menor)")
    print("Tarefa: iterações de SHA-256 em processos separados; custo de criação do pool incluído.")
    records = []
    for p in workers_values:
        tempos = []
        for rep in range(1, args.repeats + 1):
            secs = executar_lote(args.tasks, args.rounds, p)
            tempos.append(secs)
            records.append({"workers": p, "repeat": rep, "tasks": args.tasks,
                            "rounds": args.rounds, "seconds": f"{secs:.6f}",
                            "throughput": f"{args.tasks / secs:.6f}"})
        print(f"p={p:>2} | mediana = {statistics.median(tempos):>8.3f} s | "
              f"vazão = {args.tasks/statistics.median(tempos):>8.2f} tarefas/s")
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["workers", "repeat", "tasks", "rounds", "seconds", "throughput"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Medições salvas em {args.output}")
    print("Não é garantido que a curva apresente retrocesso: depende dos recursos e do gargalo da máquina.")


if __name__ == "__main__":
    main()
