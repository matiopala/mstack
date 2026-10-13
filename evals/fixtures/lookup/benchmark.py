"""A fixed dataset and hit/miss workload for the lookup experiment."""

import json
from statistics import median
from time import perf_counter

from catalog import Catalog


rows = [{"id": number, "name": f"Item {number}"} for number in range(20_000)]
queries = [19_990 + number % 20 for number in range(400)]
build_times = []
lookup_times = []
for _ in range(5):
    started = perf_counter()
    catalog = Catalog(rows)
    build_times.append(perf_counter() - started)
    started = perf_counter()
    results = [catalog.get(item_id) for item_id in queries]
    lookup_times.append(perf_counter() - started)
    assert results == [rows[item_id] if item_id < len(rows) else None for item_id in queries]

print(json.dumps({
    "rows": len(rows),
    "queries": len(queries),
    "median_build_seconds": median(build_times),
    "median_lookup_seconds": median(lookup_times),
}))
