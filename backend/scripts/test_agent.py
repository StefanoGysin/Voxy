#!/usr/bin/env python3
"""
CLI para Teste Isolado de Subagentes VOXY

Script de linha de comando para testar subagentes individuais rapidamente,
sem necessidade de passar pelo fluxo completo do VOXY Orchestrator.

Uso:
    # Testar tradutor
    poetry run python scripts/test_agent.py translator \\
        --text "Hello world" \\
        --target-language "pt-BR"

    # Testar Vision Agent
    poetry run python scripts/test_agent.py vision \\
        --image-url "https://example.com/image.jpg" \\
        --query "O que você vê?"

    # Listar agentes disponíveis
    poetry run python scripts/test_agent.py --list

    # Modo interativo
    poetry run python scripts/test_agent.py --interactive

    # Benchmark de performance
    poetry run python scripts/test_agent.py calculator \\
        --expression "2+2" \\
        --benchmark --iterations 5
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voxy_agents.utils.test_subagents import SubagentTester

# ============================================================================
# Colors for terminal output
# ============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_colored(text: str, color: str = Colors.ENDC):
    """Print text with color."""
    print(f"{color}{text}{Colors.ENDC}")


def print_header(text: str):
    """Print header with formatting."""
    print_colored(f"\n{'=' * 70}", Colors.HEADER)
    print_colored(f"  {text}", Colors.HEADER + Colors.BOLD)
    print_colored(f"{'=' * 70}\n", Colors.HEADER)


# ============================================================================
# Test Execution Functions
# ============================================================================


async def test_translator(args):
    """Test translator agent."""
    input_data = {
        "text": args.text,
        "target_language": args.target_language,
    }
    if args.source_language:
        input_data["source_language"] = args.source_language

    return await run_test("translator", input_data, args)


async def test_corrector(args):
    """Test corrector agent."""
    input_data = {"text": args.text}
    return await run_test("corrector", input_data, args)


async def test_weather(args):
    """Test weather agent."""
    input_data = {"city": args.city}
    if args.country:
        input_data["country"] = args.country

    return await run_test("weather", input_data, args)


async def test_calculator(args):
    """Test calculator agent."""
    input_data = {"expression": args.expression}
    return await run_test("calculator", input_data, args)


async def test_vision(args):
    """Test vision agent."""
    input_data = {
        "image_url": args.image_url,
        "query": args.query,
    }
    if args.analysis_type:
        input_data["analysis_type"] = args.analysis_type
    if args.detail_level:
        input_data["detail_level"] = args.detail_level

    return await run_test("vision", input_data, args)


async def test_voxy(args):
    """Test VOXY Orchestrator."""
    from voxy_agents.utils.test_subagents import test_voxy_orchestrator

    print_header("Testing VOXY ORCHESTRATOR")

    # Print input data
    print_colored("📝 Input Data:", Colors.OKCYAN + Colors.BOLD)
    print(f"  message: {args.message}")
    if args.image_url:
        # Truncate long URLs
        display_url = args.image_url
        if len(display_url) > 100:
            display_url = display_url[:100] + "..."
        print(f"  image_url: {display_url}")

    print()

    # Benchmark mode
    if args.benchmark:
        print_colored(
            f"🏁 Benchmark Mode: {args.iterations} iterations\n", Colors.WARNING
        )

        times = []
        costs = []
        tools_used_list = []

        for i in range(args.iterations):
            print_colored(f"Iteration {i + 1}/{args.iterations}...", Colors.OKBLUE)

            start = datetime.now()
            result = await test_voxy_orchestrator(
                message=args.message,
                image_url=args.image_url if hasattr(args, "image_url") else None,
                bypass_cache=args.bypass_cache,
                bypass_rate_limit=args.bypass_rate_limit,
                include_tools_metadata=True,
            )
            elapsed = (datetime.now() - start).total_seconds()

            times.append(elapsed)
            if result.metadata.cost:
                costs.append(result.metadata.cost)
            if result.metadata.tools_used:
                tools_used_list.append(result.metadata.tools_used)

        # Print benchmark results
        print_header("Benchmark Results")

        print_colored("⏱️  Timing Statistics:", Colors.OKCYAN + Colors.BOLD)
        print(f"  Min:     {min(times):.3f}s")
        print(f"  Max:     {max(times):.3f}s")
        print(f"  Average: {sum(times) / len(times):.3f}s")
        print(f"  Total:   {sum(times):.3f}s")

        if costs:
            print_colored("\n💰 Cost Statistics:", Colors.OKCYAN + Colors.BOLD)
            print(f"  Min:     ${min(costs):.6f}")
            print(f"  Max:     ${max(costs):.6f}")
            print(f"  Average: ${sum(costs) / len(costs):.6f}")
            print(f"  Total:   ${sum(costs):.6f}")

        if tools_used_list:
            # Count tool usage frequency
            from collections import Counter

            all_tools = [tool for tools in tools_used_list for tool in tools]
            tool_counts = Counter(all_tools)

            print_colored("\n🔧 Tools Usage:", Colors.OKCYAN + Colors.BOLD)
            for tool, count in tool_counts.most_common():
                print(f"  {tool}: {count} times")

        return result  # Return last result

    # Single test execution
    print_colored("⚡ Running test...\n", Colors.WARNING)

    start_time = datetime.now()
    result = await test_voxy_orchestrator(
        message=args.message,
        image_url=args.image_url if hasattr(args, "image_url") else None,
        bypass_cache=args.bypass_cache,
        bypass_rate_limit=args.bypass_rate_limit,
        include_tools_metadata=True,
    )
    total_time = (datetime.now() - start_time).total_seconds()

    # Print results
    print_results(result, total_time)

    # Export if requested
    if args.export:
        export_results(result, args.export)

    return result


async def run_test(agent_name: str, input_data: dict, args):
    """
    Run test for specified agent.

    Args:
        agent_name: Name of the agent to test
        input_data: Input data for the agent
        args: Command line arguments

    Returns:
        TestResult from the agent
    """
    # Create tester with bypass configuration
    tester = SubagentTester(
        bypass_cache=args.bypass_cache,
        bypass_rate_limit=args.bypass_rate_limit,
    )

    print_header(f"Testing {agent_name.upper()} Agent")

    # Print input data
    print_colored("📝 Input Data:", Colors.OKCYAN + Colors.BOLD)
    for key, value in input_data.items():
        # Truncate long values
        display_value = str(value)
        if len(display_value) > 100:
            display_value = display_value[:100] + "..."
        print(f"  {key}: {display_value}")

    print()

    # Benchmark mode
    if args.benchmark:
        return await run_benchmark(tester, agent_name, input_data, args.iterations)

    # Single test execution
    print_colored("⚡ Running test...\n", Colors.WARNING)

    start_time = datetime.now()
    result = await tester.test_subagent(agent_name, input_data)
    total_time = (datetime.now() - start_time).total_seconds()

    # Print results
    print_results(result, total_time)

    # Export if requested
    if args.export:
        export_results(result, args.export)

    return result


async def run_benchmark(tester, agent_name, input_data, iterations):
    """
    Run benchmark with multiple iterations.

    Args:
        tester: SubagentTester instance
        agent_name: Name of agent to test
        input_data: Input data for agent
        iterations: Number of iterations to run

    Returns:
        Final TestResult
    """
    print_colored(f"🏁 Benchmark Mode: {iterations} iterations\n", Colors.WARNING)

    times = []
    costs = []
    cache_hits = 0

    for i in range(iterations):
        print_colored(f"Iteration {i + 1}/{iterations}...", Colors.OKBLUE)

        start = datetime.now()
        result = await tester.test_subagent(agent_name, input_data)
        elapsed = (datetime.now() - start).total_seconds()

        times.append(elapsed)
        if result.metadata.cost:
            costs.append(result.metadata.cost)
        if result.metadata.cache_hit:
            cache_hits += 1

    # Print benchmark results
    print_header("Benchmark Results")

    print_colored("⏱️  Timing Statistics:", Colors.OKCYAN + Colors.BOLD)
    print(f"  Min:     {min(times):.3f}s")
    print(f"  Max:     {max(times):.3f}s")
    print(f"  Average: {sum(times) / len(times):.3f}s")
    print(f"  Total:   {sum(times):.3f}s")

    if costs:
        print_colored("\n💰 Cost Statistics:", Colors.OKCYAN + Colors.BOLD)
        print(f"  Min:     ${min(costs):.6f}")
        print(f"  Max:     ${max(costs):.6f}")
        print(f"  Average: ${sum(costs) / len(costs):.6f}")
        print(f"  Total:   ${sum(costs):.6f}")

    if agent_name == "vision":
        print_colored("\n📊 Cache Statistics:", Colors.OKCYAN + Colors.BOLD)
        print(f"  Cache Hits: {cache_hits}/{iterations}")
        print(f"  Hit Rate:   {(cache_hits / iterations) * 100:.1f}%")

    return result  # Return last result


def print_results(result, total_time=None):
    """Print test results with formatting."""
    if result.success:
        print_colored("✅ TEST SUCCESS", Colors.OKGREEN + Colors.BOLD)
    else:
        print_colored("❌ TEST FAILED", Colors.FAIL + Colors.BOLD)

    print()

    # Response
    print_colored("💬 Response:", Colors.OKCYAN + Colors.BOLD)
    print(f"  {result.response}\n")

    # Metadata - Hierarchical format
    print_colored("📊 Metadata:", Colors.OKCYAN + Colors.BOLD)

    # Check if this is a VOXY Orchestrator test (has raw_metadata with orchestrator info)
    is_voxy_test = result.metadata.raw_metadata and result.metadata.raw_metadata.get(
        "orchestrator_model"
    )

    if is_voxy_test:
        # VOXY Orchestrator + Subagent flow
        raw_meta = result.metadata.raw_metadata
        orchestrator_model = raw_meta.get("orchestrator_model", "unknown")
        subagent_name = result.agent_name

        # Extract subagent model from tools_used or metadata
        subagent_model = result.metadata.model_used
        tools_used = result.metadata.tools_used or []

        print("   ├─ 🤖 VOXY Orchestrator")
        print(f"   │  ├─ Model: {orchestrator_model}")
        print("   │  ├─ Reasoning: medium")
        print("   │  └─ Orchestration: ~0.5s")
        print("   │")
        print(f"   ├─ 🔧 Subagent: {subagent_name.title()}")
        print(f"   │  ├─ Model: {subagent_model}")

        if tools_used:
            tools_str = ", ".join(tools_used)
            print(f"   │  ├─ Tools: {tools_str}")

        # Estimate subagent time (total - orchestration overhead)
        subagent_time = result.metadata.processing_time - 0.5
        if subagent_time < 0:
            subagent_time = result.metadata.processing_time
        print(f"   │  └─ Execution Time: {subagent_time:.2f}s")
        print("   │")
        print("   └─ 📈 Performance")
        print(f"      ├─ Total Time: {result.metadata.processing_time:.3f}s")

        if result.metadata.cost:
            print(f"      ├─ Cost: ${result.metadata.cost:.6f}")

        if result.metadata.tokens_used:
            tokens = result.metadata.tokens_used
            total = tokens.get("total_tokens", "N/A")
            print(f"      ├─ Tokens: {total}")

        print(f"      └─ Cache Hit: {result.metadata.cache_hit}")

    else:
        # Standard agent test (no orchestrator)
        print(f"   ├─ Agent: {result.agent_name.title()}")
        print(f"   ├─ Model: {result.metadata.model_used}")
        print(f"   ├─ Processing Time: {result.metadata.processing_time:.3f}s")

        if total_time:
            print(f"   ├─ Total Time: {total_time:.3f}s")

        if result.metadata.cost:
            print(f"   ├─ Cost: ${result.metadata.cost:.6f}")

        if result.metadata.tokens_used:
            tokens = result.metadata.tokens_used
            print(f"   ├─ Tokens: {tokens.get('total_tokens', 'N/A')}")

        print(f"   └─ Cache Hit: {result.metadata.cache_hit}")

        # Vision-specific metadata
        if result.agent_name == "vision":
            if result.metadata.confidence:
                print(f"   ├─ Confidence: {result.metadata.confidence:.1%}")
            if result.metadata.analysis_type:
                print(f"   ├─ Analysis Type: {result.metadata.analysis_type}")
            if result.metadata.reasoning_level:
                print(f"   └─ Reasoning Level: {result.metadata.reasoning_level}")

    # Error
    if result.error:
        print_colored(f"\n⚠️  Error: {result.error}", Colors.FAIL)

    print()


def export_results(result, export_path):
    """
    Export test results to file.

    Args:
        result: TestResult to export
        export_path: Path to export file (JSON or CSV)
    """
    try:
        if export_path.endswith(".json"):
            # Export as JSON
            with open(export_path, "w") as f:
                json.dump(result.dict(), f, indent=2, default=str)

            print_colored(f"💾 Results exported to {export_path}", Colors.OKGREEN)

        elif export_path.endswith(".csv"):
            # Export as CSV
            import csv

            with open(export_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Field", "Value"])
                writer.writerow(["Success", result.success])
                writer.writerow(["Agent", result.agent_name])
                writer.writerow(["Response", result.response])
                writer.writerow(["Processing Time", result.metadata.processing_time])
                writer.writerow(["Model", result.metadata.model_used])
                writer.writerow(["Cost", result.metadata.cost])
                writer.writerow(["Cache Hit", result.metadata.cache_hit])

            print_colored(f"💾 Results exported to {export_path}", Colors.OKGREEN)

        else:
            print_colored("⚠️  Unknown export format. Use .json or .csv", Colors.WARNING)

    except Exception as e:
        print_colored(f"❌ Export failed: {e}", Colors.FAIL)


# ============================================================================
# Interactive Mode
# ============================================================================


async def interactive_mode():
    """Run interactive testing mode."""
    print_header("VOXY Subagent Tester - Interactive Mode")

    tester = SubagentTester(bypass_cache=True, bypass_rate_limit=True)

    print("Available agents:")
    for agent in tester.get_available_agents():
        print(f"  - {agent}")

    print("\nType 'quit' or 'exit' to quit\n")

    while True:
        try:
            # Get agent name
            agent_name = input(
                f"{Colors.OKBLUE}Enter agent name:{Colors.ENDC} "
            ).strip()

            if agent_name.lower() in ["quit", "exit"]:
                print_colored("\n👋 Goodbye!", Colors.OKGREEN)
                break

            if agent_name not in tester.get_available_agents():
                print_colored(f"❌ Unknown agent: {agent_name}", Colors.FAIL)
                continue

            # Special handling for VOXY Orchestrator
            if agent_name == "voxy":
                from voxy_agents.utils.test_subagents import test_voxy_orchestrator

                print_colored("\n📋 VOXY Orchestrator", Colors.OKCYAN + Colors.BOLD)
                print("  Test strategy: orchestrator_direct")
                print("  Required params: message")
                print("  Optional params: image_url")

                # Get input data
                print()
                message = input("  message: ").strip()
                image_url = input("  image_url (optional): ").strip()

                # Run test
                print()
                result = await test_voxy_orchestrator(
                    message=message,
                    image_url=image_url if image_url else None,
                    bypass_cache=True,
                    bypass_rate_limit=True,
                    include_tools_metadata=True,
                )
                print_results(result)
            else:
                # Get agent info for standard subagents
                info = tester.get_agent_info(agent_name)
                print_colored(f"\n📋 {agent_name} Agent", Colors.OKCYAN + Colors.BOLD)
                print(f"  Model: {info['model']}")
                print(
                    f"  Required params: {', '.join(info.get('required_params', []))}"
                )

                # Get input data
                input_data = {}
                print()
                for param in info.get("required_params", []):
                    value = input(f"  {param}: ").strip()
                    input_data[param] = value

                for param in info.get("optional_params", []):
                    value = input(f"  {param} (optional): ").strip()
                    if value:
                        input_data[param] = value

                # Run test
                print()
                result = await tester.test_subagent(agent_name, input_data)
                print_results(result)

        except KeyboardInterrupt:
            print_colored("\n\n👋 Goodbye!", Colors.OKGREEN)
            break
        except Exception as e:
            print_colored(f"\n❌ Error: {e}\n", Colors.FAIL)


# ============================================================================
# Argument Parsing
# ============================================================================


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="CLI para Teste Isolado de Subagentes VOXY",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Global options
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available agents",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--bypass-cache",
        action="store_true",
        default=True,
        help="Bypass cache (default: True)",
    )
    parser.add_argument(
        "--bypass-rate-limit",
        action="store_true",
        default=True,
        help="Bypass rate limiting (default: True)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark mode",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations (default: 5)",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export results to file (.json or .csv)",
    )

    # Subparsers for each agent
    subparsers = parser.add_subparsers(dest="agent", help="Agent to test")

    # Translator
    translator_parser = subparsers.add_parser("translator", help="Test translator")
    translator_parser.add_argument("--text", required=True, help="Text to translate")
    translator_parser.add_argument(
        "--target-language", required=True, help="Target language"
    )
    translator_parser.add_argument("--source-language", help="Source language")

    # Corrector
    corrector_parser = subparsers.add_parser("corrector", help="Test corrector")
    corrector_parser.add_argument("--text", required=True, help="Text to correct")

    # Weather
    weather_parser = subparsers.add_parser("weather", help="Test weather")
    weather_parser.add_argument("--city", required=True, help="City name")
    weather_parser.add_argument("--country", help="Country code (default: BR)")

    # Calculator
    calculator_parser = subparsers.add_parser("calculator", help="Test calculator")
    calculator_parser.add_argument(
        "--expression", required=True, help="Math expression"
    )

    # Vision
    vision_parser = subparsers.add_parser("vision", help="Test vision")
    vision_parser.add_argument("--image-url", required=True, help="Image URL")
    vision_parser.add_argument(
        "--query", default="Analise esta imagem", help="Query about image"
    )
    vision_parser.add_argument(
        "--analysis-type",
        choices=["general", "ocr", "technical", "artistic", "document"],
        default="general",
        help="Analysis type",
    )
    vision_parser.add_argument(
        "--detail-level",
        choices=["basic", "standard", "detailed", "comprehensive"],
        default="standard",
        help="Detail level",
    )

    # VOXY Orchestrator
    voxy_parser = subparsers.add_parser("voxy", help="Test VOXY Orchestrator")
    voxy_parser.add_argument("--message", required=True, help="Message to send to VOXY")
    voxy_parser.add_argument(
        "--image-url", help="Optional image URL for vision analysis"
    )

    return parser


# ============================================================================
# Main
# ============================================================================


async def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # List agents
    if args.list:
        tester = SubagentTester()
        print_header("Available Agents")
        for agent_name in tester.get_available_agents():
            info = tester.get_agent_info(agent_name)
            print_colored(f"\n{agent_name}", Colors.OKBLUE + Colors.BOLD)
            print(f"  Model: {info['model']}")
            print(f"  Strategy: {info['test_strategy']}")
            if info.get("capabilities"):
                print("  Capabilities:")
                for cap in info["capabilities"]:
                    print(f"    - {cap}")
        print()
        return

    # Interactive mode
    if args.interactive:
        await interactive_mode()
        return

    # Test specific agent
    if not args.agent:
        parser.print_help()
        return

    # Route to appropriate test function
    test_functions = {
        "translator": test_translator,
        "corrector": test_corrector,
        "weather": test_weather,
        "calculator": test_calculator,
        "vision": test_vision,
        "voxy": test_voxy,
    }

    test_func = test_functions.get(args.agent)
    if test_func:
        await test_func(args)
    else:
        print_colored(f"❌ Unknown agent: {args.agent}", Colors.FAIL)
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
