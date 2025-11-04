"""Test Ollama server limits to determine optimal concurrency settings."""

import asyncio
import httpx
import time
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Ollama configuration (from subagents_config.py)
OLLAMA_API_KEY = "6ddb812c07914107ba7c0e504fdcf9f1.gkld5OFtD8NRbDZvMiYtHG6P"
OLLAMA_BASE_URL = "http://localhost:11434/v1/"

# Models to test
MODELS = [
    "kimi-k2:1t-cloud",
    "minimax-m2:cloud",
    "glm-4.6:cloud",
]


async def make_ollama_request(
    client: httpx.AsyncClient,
    model: str,
    request_id: int
) -> Dict[str, Any]:
    """Make a single request to Ollama API."""
    start_time = time.time()

    try:
        response = await client.post(
            f"{OLLAMA_BASE_URL}chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": f"Say 'Test {request_id}' in 5 words or less."}
                ],
                "temperature": 0,
                "max_tokens": 20,
            },
            headers={
                "Authorization": f"Bearer {OLLAMA_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

        elapsed = time.time() - start_time

        return {
            "request_id": request_id,
            "model": model,
            "status": response.status_code,
            "success": response.status_code == 200,
            "elapsed": elapsed,
            "error": None if response.status_code == 200 else response.text[:200]
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_id": request_id,
            "model": model,
            "status": 0,
            "success": False,
            "elapsed": elapsed,
            "error": str(e)[:200]
        }


async def test_concurrency_level(
    concurrency: int,
    model: str,
    total_requests: int = 10
) -> Dict[str, Any]:
    """Test a specific concurrency level."""

    async with httpx.AsyncClient() as client:
        # Create batches of concurrent requests
        results = []
        start_time = time.time()

        for batch_start in range(0, total_requests, concurrency):
            batch_size = min(concurrency, total_requests - batch_start)
            tasks = [
                make_ollama_request(client, model, batch_start + i)
                for i in range(batch_size)
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        total_time = time.time() - start_time

        # Calculate statistics
        successes = [r for r in results if r["success"]]
        failures = [r for r in results if not r["success"]]

        return {
            "concurrency": concurrency,
            "model": model,
            "total_requests": total_requests,
            "total_time": total_time,
            "successes": len(successes),
            "failures": len(failures),
            "success_rate": len(successes) / total_requests * 100,
            "avg_response_time": sum(r["elapsed"] for r in successes) / len(successes) if successes else 0,
            "requests_per_minute": (len(successes) / total_time) * 60 if total_time > 0 else 0,
            "errors": [r["error"] for r in failures if r["error"]],
        }


async def run_full_benchmark():
    """Run comprehensive benchmark of Ollama server."""

    console.print("\n[bold cyan]🧪 Ollama Server Benchmark Test[/bold cyan]\n")
    console.print(f"[dim]Testing endpoint: {OLLAMA_BASE_URL}[/dim]")
    console.print(f"[dim]Models: {', '.join(MODELS)}[/dim]\n")

    # Test different concurrency levels
    concurrency_levels = [1, 2, 3, 5, 8, 10]
    total_requests_per_test = 10

    all_results = []

    for model in MODELS:
        console.print(f"\n[bold yellow]Testing model: {model}[/bold yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            for concurrency in concurrency_levels:
                task = progress.add_task(
                    f"Concurrency {concurrency}...",
                    total=None
                )

                result = await test_concurrency_level(
                    concurrency=concurrency,
                    model=model,
                    total_requests=total_requests_per_test
                )
                all_results.append(result)

                # Show immediate result
                status = "✓" if result["success_rate"] == 100 else "✗"
                console.print(
                    f"  {status} Concurrency {concurrency}: "
                    f"{result['success_rate']:.0f}% success, "
                    f"avg {result['avg_response_time']:.2f}s, "
                    f"{result['requests_per_minute']:.1f} req/min"
                )

                progress.remove_task(task)

                # Brief pause between tests
                await asyncio.sleep(2)

    return all_results


def display_results(results: List[Dict[str, Any]]):
    """Display benchmark results in a nice table."""

    console.print("\n\n[bold cyan]📊 Benchmark Results Summary[/bold cyan]\n")

    for model in MODELS:
        model_results = [r for r in results if r["model"] == model]

        if not model_results:
            continue

        console.print(f"\n[bold yellow]{model}[/bold yellow]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Concurrency", style="cyan", width=12)
        table.add_column("Success Rate", justify="right", width=14)
        table.add_column("Avg Response", justify="right", width=14)
        table.add_column("Req/Min", justify="right", width=12)
        table.add_column("Status", width=8)

        for result in model_results:
            status = "✓ Pass" if result["success_rate"] == 100 else "✗ Fail"
            status_color = "green" if result["success_rate"] == 100 else "red"

            table.add_row(
                str(result["concurrency"]),
                f"{result['success_rate']:.1f}%",
                f"{result['avg_response_time']:.2f}s",
                f"{result['requests_per_minute']:.1f}",
                f"[{status_color}]{status}[/{status_color}]"
            )

        console.print(table)

        # Find optimal concurrency (highest that maintains 100% success)
        successful = [r for r in model_results if r["success_rate"] == 100]
        if successful:
            optimal = max(successful, key=lambda x: x["concurrency"])
            console.print(
                f"\n[bold green]✓ Recommended max concurrency: {optimal['concurrency']}[/bold green]"
            )
            console.print(
                f"  [dim]Throughput: {optimal['requests_per_minute']:.1f} requests/minute[/dim]"
            )
        else:
            console.print("\n[bold red]✗ All concurrency levels failed - server may be down[/bold red]")

    # Overall recommendation
    console.print("\n\n[bold cyan]💡 Recommendations:[/bold cyan]\n")

    successful_results = [r for r in results if r["success_rate"] == 100]
    if successful_results:
        # Find the lowest safe concurrency across all models
        safe_concurrency = min(r["concurrency"] for r in successful_results)
        console.print(f"1. [green]Safe concurrent requests (all models): {safe_concurrency}[/green]")

        # Find optimal for mixed workload
        avg_requests_per_min = sum(r["requests_per_minute"] for r in successful_results) / len(successful_results)
        console.print(f"2. [green]Average throughput: {avg_requests_per_min:.1f} requests/minute[/green]")

        console.print(f"3. [yellow]For 6 parallel subagents: Consider sequential batching or reduce to {safe_concurrency} parallel agents[/yellow]")
    else:
        console.print("[red]Server appears to be overloaded or down. Check Ollama status.[/red]")


async def main():
    """Run the benchmark test."""
    try:
        results = await run_full_benchmark()
        display_results(results)

        console.print("\n\n[bold cyan]📝 Next Steps:[/bold cyan]\n")
        console.print("1. Review the recommended max concurrency above")
        console.print("2. Update agent config to limit parallel subagent spawns")
        console.print("3. Or implement sequential batching (run 3 agents, then next 3)")
        console.print("4. Monitor /bashes for ongoing Ollama processes\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Benchmark interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n\n[red]Error running benchmark: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
