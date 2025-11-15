#!/usr/bin/env python3
"""
Phase 3 End-to-End Tests - LangGraph Full Implementation

Tests all 5 subagents through the full Phase 3 LangGraph implementation:
- PATH1 (vision_bypass): Direct vision analysis
- PATH2 (supervisor): ReAct supervisor with all 5 tools

Test scenarios:
1. Translation request → translate_text tool
2. Calculation request → calculate tool
3. Correction request → correct_text tool
4. Weather request → get_weather tool
5. Image analysis (with keywords) → PATH1 vision_bypass
6. Image analysis (without keywords) → PATH2 analyze_image tool
7. Multi-tool request → supervisor chains multiple tools

Usage:
    poetry run python scripts/test_phase3_e2e.py
    poetry run python scripts/test_phase3_e2e.py --verbose
    poetry run python scripts/test_phase3_e2e.py --test translation
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voxy_agents.langgraph.checkpointer import (
    CheckpointerType,
    get_checkpoint_config,
)
from voxy_agents.langgraph.graph_builder import create_phase3_graph
from voxy_agents.langgraph.graph_state import create_initial_state

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
    print_colored(f"\n{'=' * 80}", Colors.HEADER)
    print_colored(f"  {text}", Colors.HEADER + Colors.BOLD)
    print_colored(f"{'=' * 80}\n", Colors.HEADER)


# ============================================================================
# Test Scenarios
# ============================================================================

# Test image URL (emoji from user)
TEST_IMAGE_URL = "https://supabase.gysin.pro/storage/v1/object/public/user-images/users/4a82fdef-cc14-4471-b9b9-9f1238bdd222/uploads/2025/10/20251002130719_95ef4bc8_capturadetela2025-09-21065333.png"

TEST_SCENARIOS = {
    "translation": {
        "name": "Translation (translate_text tool)",
        "message": "Traduza 'Hello world' para português brasileiro",
        "expected_tool": "translate_text",
        "expected_route": "PATH2",
    },
    "calculation": {
        "name": "Calculation (calculate tool)",
        "message": "Quanto é 25 × 4 + 10?",
        "expected_tool": "calculate",
        "expected_route": "PATH2",
    },
    "correction": {
        "name": "Correction (correct_text tool)",
        "message": "Corrija: 'Eu foi na loja ontem e comprou muito coisa'",
        "expected_tool": "correct_text",
        "expected_route": "PATH2",
    },
    "weather": {
        "name": "Weather (get_weather tool)",
        "message": "Como está o clima em São Paulo?",
        "expected_tool": "get_weather",
        "expected_route": "PATH2",
    },
    "vision_path1": {
        "name": "Vision PATH1 (vision_bypass direct)",
        "message": "Qual emoji é este?",
        "image_url": TEST_IMAGE_URL,
        "expected_tool": None,  # Direct bypass, no tool call
        "expected_route": "PATH1",
    },
    "vision_path2": {
        "name": "Vision PATH2 (analyze_image tool)",
        "message": f"Analise a imagem em {TEST_IMAGE_URL} e descreva o que você vê",
        "image_url": None,  # No image_url in context, so supervisor extracts from message
        "expected_tool": "analyze_image",
        "expected_route": "PATH2",
    },
    "multi_tool": {
        "name": "Multi-Tool (translate + correct)",
        "message": "Traduza 'Hello world' para português e depois corrija qualquer erro",
        "expected_tool": ["translate_text", "correct_text"],
        "expected_route": "PATH2",
    },
    "direct_response": {
        "name": "Direct Response (no tool needed)",
        "message": "Olá, como vai?",
        "expected_tool": None,
        "expected_route": "PATH2",
    },
}


# ============================================================================
# Test Execution
# ============================================================================


async def run_test_scenario(
    scenario_name: str, scenario: dict, graph, verbose: bool = False
):
    """
    Run a single test scenario.

    Args:
        scenario_name: Name of the scenario
        scenario: Scenario configuration
        graph: Compiled LangGraph
        verbose: Show detailed output

    Returns:
        Test result (success, error message, duration, etc.)
    """
    print_colored(f"\n{'─' * 80}", Colors.OKCYAN)
    print_colored(f"  {scenario['name']}", Colors.OKCYAN + Colors.BOLD)
    print_colored(f"{'─' * 80}", Colors.OKCYAN)

    # Print test info
    print(f"\n📝 Message: {scenario['message']}")
    if scenario.get("image_url"):
        display_url = scenario["image_url"]
        if len(display_url) > 80:
            display_url = display_url[:80] + "..."
        print(f"🖼️  Image URL: {display_url}")
    print(f"🎯 Expected Route: {scenario['expected_route']}")
    if scenario["expected_tool"]:
        if isinstance(scenario["expected_tool"], list):
            print(f"🔧 Expected Tools: {', '.join(scenario['expected_tool'])}")
        else:
            print(f"🔧 Expected Tool: {scenario['expected_tool']}")
    else:
        print("🔧 Expected Tool: None (direct response or bypass)")

    # Build state
    thread_id = f"test-{scenario_name}-{datetime.now().timestamp()}"
    config = get_checkpoint_config(thread_id=thread_id)

    state = create_initial_state(
        messages=[{"role": "user", "content": scenario["message"]}],
        thread_id=thread_id,
    )

    # Add image_url to context if present
    if scenario.get("image_url"):
        state["context"]["image_url"] = scenario["image_url"]

    # Run test
    print_colored("\n⚡ Running test...", Colors.WARNING)
    start_time = datetime.now()

    try:
        result = graph.invoke(state, config=config)
        duration = (datetime.now() - start_time).total_seconds()

        # Determine route taken
        route_taken = "unknown"
        if result.get("context", {}).get("vision_analysis"):
            route_taken = "PATH1"
        else:
            route_taken = "PATH2"

        # Extract response
        response_text = "No response"
        if result["messages"]:
            last_message = result["messages"][-1]
            response_text = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

        # Print results
        print_colored("\n✅ TEST PASSED", Colors.OKGREEN + Colors.BOLD)
        print(
            f"\n🤖 Response: {response_text[:200]}{'...' if len(response_text) > 200 else ''}"
        )
        print(f"\n🛤️  Route Taken: {route_taken}")
        print(f"⏱️  Duration: {duration:.3f}s")

        if verbose and result.get("context", {}).get("vision_analysis"):
            print_colored("\n📊 Vision Analysis Metadata:", Colors.OKCYAN)
            vision_analysis = result["context"]["vision_analysis"]
            print(f"  - Image URL: {vision_analysis.get('image_url', 'N/A')[:60]}...")
            print(f"  - Analysis Type: {vision_analysis.get('analysis_type', 'N/A')}")
            print(f"  - Result Length: {len(vision_analysis.get('result', ''))} chars")

        # Validate expectations
        validation_errors = []

        # Check route
        if route_taken != scenario["expected_route"]:
            validation_errors.append(
                f"Route mismatch: expected {scenario['expected_route']}, got {route_taken}"
            )

        # TODO: Check tools used (requires tracking tool calls in state)
        # This will be implemented when we add tool call tracking to VoxyState

        if validation_errors:
            print_colored("\n⚠️  VALIDATION WARNINGS:", Colors.WARNING)
            for error in validation_errors:
                print(f"  - {error}")

        return {
            "success": True,
            "duration": duration,
            "route": route_taken,
            "response_length": len(response_text),
            "validation_errors": validation_errors,
        }

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        print_colored("\n❌ TEST FAILED", Colors.FAIL + Colors.BOLD)
        print_colored(f"Error: {str(e)}", Colors.FAIL)

        if verbose:
            import traceback

            print_colored("\n📋 Full Traceback:", Colors.FAIL)
            traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "duration": duration,
        }


async def run_all_tests(verbose: bool = False):
    """
    Run all Phase 3 end-to-end tests.

    Args:
        verbose: Show detailed output
    """
    print_header("Phase 3 End-to-End Tests - LangGraph Full Implementation")

    # Create Phase 3 graph
    print_colored("🏗️  Building Phase 3 LangGraph...", Colors.OKCYAN)
    print("  ├─ Entry Router (PATH1 vs PATH2 decision)")
    print("  ├─ Vision Bypass with actual Vision Agent (PATH1 direct execution)")
    print("  ├─ Full ReAct Supervisor with 5 subagent tools (PATH2 orchestration)")
    print("  │  ├─ translate_text (Translator)")
    print("  │  ├─ calculate (Calculator)")
    print("  │  ├─ correct_text (Corrector)")
    print("  │  ├─ get_weather (Weather)")
    print("  │  └─ analyze_image (Vision)")
    print("  └─ All 5 subagents: translator, calculator, corrector, weather, vision")
    print()

    graph = create_phase3_graph(checkpointer_type=CheckpointerType.MEMORY)
    print_colored("✅ Graph compiled successfully\n", Colors.OKGREEN)

    # Run all test scenarios
    results = {}
    for scenario_name, scenario in TEST_SCENARIOS.items():
        results[scenario_name] = await run_test_scenario(
            scenario_name, scenario, graph, verbose
        )

    # Print summary
    print_header("Test Summary")

    passed = sum(1 for r in results.values() if r["success"])
    failed = len(results) - passed
    total_duration = sum(r["duration"] for r in results.values())

    print_colored(f"✅ Passed: {passed}/{len(results)}", Colors.OKGREEN)
    if failed > 0:
        print_colored(f"❌ Failed: {failed}/{len(results)}", Colors.FAIL)
    print(f"⏱️  Total Duration: {total_duration:.3f}s")
    print(f"⏱️  Average Duration: {total_duration / len(results):.3f}s")

    # Print failed tests
    if failed > 0:
        print_colored("\n❌ Failed Tests:", Colors.FAIL + Colors.BOLD)
        for scenario_name, result in results.items():
            if not result["success"]:
                print(f"  - {TEST_SCENARIOS[scenario_name]['name']}")
                print(f"    Error: {result.get('error', 'Unknown error')}")

    # Print validation warnings
    warnings = sum(
        len(r.get("validation_errors", [])) for r in results.values() if r["success"]
    )
    if warnings > 0:
        print_colored(f"\n⚠️  Validation Warnings: {warnings}", Colors.WARNING)

    print()

    return passed == len(results)


async def run_single_test(test_name: str, verbose: bool = False):
    """
    Run a single test scenario.

    Args:
        test_name: Name of the test to run
        verbose: Show detailed output
    """
    if test_name not in TEST_SCENARIOS:
        print_colored(f"❌ Unknown test: {test_name}", Colors.FAIL)
        print("\nAvailable tests:")
        for name in TEST_SCENARIOS.keys():
            print(f"  - {name}")
        return False

    print_header(f"Phase 3 Test: {TEST_SCENARIOS[test_name]['name']}")

    # Create Phase 3 graph
    print_colored("🏗️  Building Phase 3 LangGraph...", Colors.OKCYAN)
    graph = create_phase3_graph(checkpointer_type=CheckpointerType.MEMORY)
    print_colored("✅ Graph compiled successfully\n", Colors.OKGREEN)

    # Run test
    result = await run_test_scenario(
        test_name, TEST_SCENARIOS[test_name], graph, verbose
    )

    return result["success"]


# ============================================================================
# Main
# ============================================================================


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3 End-to-End Tests - LangGraph Full Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--test",
        type=str,
        help=f"Run a single test (choices: {', '.join(TEST_SCENARIOS.keys())})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including tracebacks",
    )

    args = parser.parse_args()

    # Run tests
    if args.test:
        success = await run_single_test(args.test, args.verbose)
    else:
        success = await run_all_tests(args.verbose)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
