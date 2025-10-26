# simple async load generator using httpx
import asyncio, httpx, time
from statistics import mean

URL = "https://localhost/infer"
NUM = 50
CONCURRENCY = 10

async def single(client, payload):
    start = time.time()
    try:
        r = await client.post(URL, json=payload, timeout=10.0, verify=False)
        latency = (time.time() - start) * 1000
        return r.status_code, latency
    except Exception as e:
        return None, None

async def worker(q, results):
    async with httpx.AsyncClient(verify=False) as client:
        while not q.empty():
            payload = await q.get()
            status, lat = await single(client, payload)
            if status is None:
                results.append(("err", 0))
            else:
                results.append((status, lat))
            q.task_done()

async def main():
    q = asyncio.Queue()
    for _ in range(NUM):
        await q.put({"prompt":"hello", "max_tokens":32})
    results = []
    tasks = [asyncio.create_task(worker(q, results)) for _ in range(CONCURRENCY)]
    await q.join()
    for t in tasks: t.cancel()
    latencies = [r[1] for r in results if r[0] and r[1] > 0]
    lat_sorted = sorted(latencies)
    if lat_sorted:
        p50 = lat_sorted[int(0.5*len(lat_sorted))]
        p95 = lat_sorted[int(0.95*len(lat_sorted))]
    else:
        p50 = p95 = 0
    print("count:", len(latencies))
    print("p50:", p50)
    print("p95:", p95)
    print("mean:", mean(latencies) if latencies else 0)

if __name__ == "__main__":
    asyncio.run(main())
