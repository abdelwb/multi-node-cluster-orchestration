"""
Simple concurrent load generator for the Ray Serve /predict endpoint.

Generates enough concurrent request pressure to trigger the deployment's
autoscaler (see serve_app.py's autoscaling_config), and reports latency and
throughput - the "performance monitoring and analysis" half of the JD
requirement, measured directly at the client.

    docker compose exec ray-head python /home/ray/app/load_test.py
"""
import argparse
import concurrent.futures
import statistics
import time

import requests

URL = "http://localhost:8000/predict"


def one_request(_):
    start = time.perf_counter()
    resp = requests.get(URL, timeout=10)
    elapsed_ms = (time.perf_counter() - start) * 1000
    resp.raise_for_status()
    return elapsed_ms


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--requests", type=int, default=200)
    p.add_argument("--concurrency", type=int, default=20)
    args = p.parse_args()

    print(f"Sending {args.requests} requests at concurrency={args.concurrency} to {URL}")
    latencies = []
    start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for latency_ms in pool.map(one_request, range(args.requests)):
            latencies.append(latency_ms)

    total_time = time.perf_counter() - start
    throughput = args.requests / total_time

    print("\n--- Results ---")
    print(f"Total time:     {total_time:.2f}s")
    print(f"Throughput:     {throughput:.1f} req/sec")
    print(f"Latency p50:    {statistics.median(latencies):.1f} ms")
    print(f"Latency mean:   {statistics.mean(latencies):.1f} ms")
    print(f"Latency max:    {max(latencies):.1f} ms")
    print("\nWatch replica count scale up during this run at http://localhost:8265")


if __name__ == "__main__":
    main()
