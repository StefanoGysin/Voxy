#!/usr/bin/env python3
"""
Quick LangGraph Test - Validate feature flag and basic functionality

Usage:
    poetry run python scripts/test_langgraph_quick.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env with override to ensure latest values
load_dotenv(override=True)


def check_feature_flag():
    """Check if VOXY_LANGGRAPH_ENABLED is set correctly."""
    flag = os.getenv("VOXY_LANGGRAPH_ENABLED", "not set")
    print("\n" + "=" * 60)
    print("🔧 Feature Flag Check")
    print("=" * 60)
    print(f"VOXY_LANGGRAPH_ENABLED = {flag}")

    if flag.lower() == "true":
        print("✅ LangGraph is ENABLED")
        return True
    elif flag.lower() == "false":
        print("⚠️  LangGraph is DISABLED (using OpenAI Agents SDK)")
        return False
    else:
        print("❌ Feature flag not set correctly!")
        return False


async def test_langgraph_orchestrator():
    """Test LangGraph orchestrator directly."""
    print("\n" + "=" * 60)
    print("🧪 Testing LangGraph Orchestrator")
    print("=" * 60)

    try:
        from voxy_agents.langgraph.checkpointer import CheckpointerType
        from voxy_agents.langgraph.orchestrator import LangGraphOrchestrator

        print("\n✓ LangGraph imports successful")

        # Create orchestrator
        print("\n🔧 Creating LangGraphOrchestrator with SQLite checkpointer...")
        orchestrator = LangGraphOrchestrator(
            checkpointer_type=CheckpointerType.SQLITE, db_path="voxy_langgraph_test.db"
        )
        print("✓ Orchestrator created successfully")

        # Test simple message
        print("\n📝 Testing simple translation request...")
        test_message = "Translate 'Hello, how are you?' to Portuguese"

        result = await orchestrator.process_message(
            message=test_message, session_id="test-session-123", user_id="test-user-456"
        )

        print("\n📊 Result:")
        print(f"  Response: {result['content'][:100]}...")
        print(f"  Route taken: {result.get('route_taken', 'N/A')}")
        print(f"  Thread ID: {result.get('thread_id', 'N/A')}")

        if result.get("usage"):
            usage = result["usage"]
            print("\n💰 Token Usage:")
            print(f"  Input tokens: {usage.input_tokens}")
            print(f"  Output tokens: {usage.output_tokens}")
            print(f"  Total tokens: {usage.total_tokens}")
            if hasattr(usage, "estimated_cost"):
                print(f"  Estimated cost: ${usage.estimated_cost:.6f}")

        print("\n✅ LangGraph orchestrator test PASSED!")
        return True

    except Exception as e:
        print("\n❌ LangGraph orchestrator test FAILED!")
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test runner."""
    print("\n" + "=" * 60)
    print("🚀 VOXY LangGraph Quick Test")
    print("=" * 60)

    # Check feature flag
    is_enabled = check_feature_flag()

    if not is_enabled:
        print("\n⚠️  To enable LangGraph, set in backend/.env:")
        print("    VOXY_LANGGRAPH_ENABLED=true")
        print("\nExiting...")
        return

    # Test orchestrator
    success = await test_langgraph_orchestrator()

    # Final summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests PASSED!")
        print("\nNext steps:")
        print(
            "1. Start backend: cd backend && poetry run uvicorn src.voxy_agents.api.fastapi_server:app --reload"
        )
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Open VOXY Web OS: http://localhost:3000")
        print("4. Login and test chat with LangGraph!")
    else:
        print("❌ Tests FAILED - check errors above")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
