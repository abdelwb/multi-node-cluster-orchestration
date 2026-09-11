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
    """Returns elapsed ms, or None on failure.

    Deliberately swallows request errors instead of letting them propagate:
    at high concurrency against a single starting replica, a request can
    queue longer than the timeout while the autoscaler is still adding
    capacity. One such timeout used to crash pool.map() and kill the whole
    run - and with it, the load that would have proven the point.
    """
    start = time.perf_counter()
    try:
        resp = requests.get(URL, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return None
    return (time.perf_counter() - start) * 1000


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--requests", type=int, default=200)
    p.add_argument("--concurrency", type=int, default=20)
    args = p.parse_args()

    print(f"Sending {args.requests} requests at concurrency={args.concurrency} to {URL}")
    results = []
    start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for result in pool.map(one_request, range(args.requests)):
            results.append(result)

    total_time = time.perf_counter() - start
    latencies = [r for r in results if r is not None]
    failed = len(results) - len(latencies)
    throughput = len(latencies) / total_time

    print("\n--- Results ---")
    print(f"Total time:     {total_time:.2f}s")
    print(f"Succeeded:      {len(latencies)}/{args.requests} ({failed} failed/timed out)")
    print(f"Throughput:     {throughput:.1f} req/sec")
    if latencies:
        print(f"Latency p50:    {statistics.median(latencies):.1f} ms")
        print(f"Latency mean:   {statistics.mean(latencies):.1f} ms")
        print(f"Latency max:    {max(latencies):.1f} ms")
    print("\nWatch replica count scale up during this run at http://localhost:8265")


if __name__ == "__main__":
    main()
