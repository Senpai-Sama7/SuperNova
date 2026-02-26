#!/usr/bin/env python3
"""
Performance Benchmark Tool
Measures endpoint latency, throughput, and error rates under load.
"""

import argparse
import asyncio
import json
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Optional

import aiohttp
import requests


@dataclass
class RequestResult:
    status: int
    latency: float
    error: Optional[str] = None
    timestamp: float = 0


class PerformanceBenchmark:
    def __init__(self, endpoint, concurrency=10, duration=60, timeout=30):
        self.endpoint = endpoint
        self.concurrency = concurrency
        self.duration = duration
        self.timeout = timeout
        self.results = []
        self.errors = defaultdict(int)
        
    async def run(self):
        """Run the benchmark."""
        print(f"Benchmarking {self.endpoint}")
        print(f"Concurrency: {self.concurrency}, Duration: {self.duration}s")
        print("-" * 50)
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._worker(session, start_time)
                for _ in range(self.concurrency)
            ]
            await asyncio.gather(*tasks)
        
        return self._generate_report(start_time)
    
    async def _worker(self, session, start_time):
        """Worker that makes requests until duration expires."""
        while time.time() - start_time < self.duration:
            result = await self._make_request(session)
            self.results.append(result)
            
            if result.error:
                self.errors[result.error] += 1
    
    async def _make_request(self, session) -> RequestResult:
        """Make a single request and measure."""
        start = time.perf_counter()
        timestamp = time.time()
        
        try:
            async with session.get(
                self.endpoint,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                await response.read()
                latency = time.perf_counter() - start
                return RequestResult(
                    status=response.status,
                    latency=latency,
                    timestamp=timestamp
                )
        except asyncio.TimeoutError:
            return RequestResult(
                status=0,
                latency=time.perf_counter() - start,
                error="TIMEOUT",
                timestamp=timestamp
            )
        except Exception as e:
            return RequestResult(
                status=0,
                latency=time.perf_counter() - start,
                error=str(type(e).__name__),
                timestamp=timestamp
            )
    
    def _generate_report(self, start_time) -> dict:
        """Generate benchmark report."""
        total_time = time.time() - start_time
        successful = [r for r in self.results if 200 <= r.status < 300]
        failed = [r for r in self.results if r.status >= 400 or r.error]
        
        latencies = [r.latency for r in successful]
        
        report = {
            'endpoint': self.endpoint,
            'configuration': {
                'concurrency': self.concurrency,
                'duration': self.duration,
                'timeout': self.timeout
            },
            'summary': {
                'total_requests': len(self.results),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'requests_per_second': len(self.results) / total_time,
                'total_time_seconds': total_time
            },
            'latency': {
                'unit': 'seconds'
            },
            'errors': dict(self.errors),
            'status_codes': defaultdict(int)
        }
        
        # Latency statistics
        if latencies:
            latencies.sort()
            report['latency'].update({
                'min': round(min(latencies), 4),
                'max': round(max(latencies), 4),
                'mean': round(statistics.mean(latencies), 4),
                'median': round(statistics.median(latencies), 4),
                'p50': round(self._percentile(latencies, 50), 4),
                'p90': round(self._percentile(latencies, 90), 4),
                'p95': round(self._percentile(latencies, 95), 4),
                'p99': round(self._percentile(latencies, 99), 4),
                'stdev': round(statistics.stdev(latencies), 4) if len(latencies) > 1 else 0
            })
        
        # Status code distribution
        for r in self.results:
            report['status_codes'][str(r.status)] += 1
        report['status_codes'] = dict(report['status_codes'])
        
        return report
    
    @staticmethod
    def _percentile(sorted_data, percentile):
        """Calculate percentile from sorted data."""
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        
        if f == c:
            return sorted_data[f]
        
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


def print_report(report):
    """Print formatted benchmark report."""
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    s = report['summary']
    print(f"\nTotal Requests: {s['total_requests']:,}")
    print(f"Successful: {s['successful_requests']:,}")
    print(f"Failed: {s['failed_requests']:,}")
    print(f"Requests/sec: {s['requests_per_second']:.2f}")
    
    print("\n" + "-" * 60)
    print("LATENCY DISTRIBUTION")
    print("-" * 60)
    
    l = report['latency']
    print(f"  Min:    {l['min']*1000:.2f} ms")
    print(f"  Mean:   {l['mean']*1000:.2f} ms")
    print(f"  Median: {l['median']*1000:.2f} ms")
    print(f"  Max:    {l['max']*1000:.2f} ms")
    print(f"  P90:    {l['p90']*1000:.2f} ms")
    print(f"  P95:    {l['p95']*1000:.2f} ms")
    print(f"  P99:    {l['p99']*1000:.2f} ms")
    print(f"  Stdev:  {l['stdev']*1000:.2f} ms")
    
    if report['errors']:
        print("\n" + "-" * 60)
        print("ERRORS")
        print("-" * 60)
        for error, count in report['errors'].items():
            print(f"  {error}: {count}")
    
    if report['status_codes']:
        print("\n" + "-" * 60)
        print("STATUS CODES")
        print("-" * 60)
        for code, count in sorted(report['status_codes'].items()):
            print(f"  {code}: {count}")


def main():
    parser = argparse.ArgumentParser(description='Performance benchmark tool')
    parser.add_argument('--endpoint', '-e', required=True, help='Endpoint URL')
    parser.add_argument('--concurrency', '-c', type=int, default=10, help='Concurrent connections')
    parser.add_argument('--duration', '-d', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--timeout', '-t', type=int, default=30, help='Request timeout')
    parser.add_argument('--output', '-o', help='Output JSON file')
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(
        endpoint=args.endpoint,
        concurrency=args.concurrency,
        duration=args.duration,
        timeout=args.timeout
    )
    
    report = asyncio.run(benchmark.run())
    
    print_report(report)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: {args.output}")


if __name__ == '__main__':
    main()
