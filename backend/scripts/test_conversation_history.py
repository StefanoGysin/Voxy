#!/usr/bin/env python3
"""
Conversation History Validation Script (Phase 4E)

Tests that SQLite checkpoint loading enables proper conversation history:
- First message creates new checkpoint
- Second message loads checkpoint and appends to history
- VOXY remembers previous context
"""

import asyncio
from uuid import uuid4

from voxy_agents.langgraph.checkpointer import CheckpointerType
from voxy_agents.langgraph.orchestrator import LangGraphOrchestrator


async def test_conversation_history():
    """Test that conversation history persists across multiple invocations."""

    print("\n" + "=" * 60)
    print("🧪 Conversation History Validation (Phase 4E)")
    print("=" * 60 + "\n")

    # Create orchestrator with SQLite checkpointer
    print("🔧 Creating orchestrator with SQLite checkpointer...")
    orchestrator = LangGraphOrchestrator(
        checkpointer_type=CheckpointerType.SQLITE,
        db_path="test_conversation_history.db",
    )
    print("✓ Orchestrator created\n")

    # Use consistent session_id for the conversation
    session_id = f"test-session-{uuid4()}"
    user_id = "test-user"

    print(f"📝 Session ID: {session_id}")
    print(f"👤 User ID: {user_id}\n")

    # ===== MESSAGE 1: First message (creates checkpoint) =====
    print("=" * 60)
    print("1️⃣  FIRST MESSAGE: 'My name is Alice'")
    print("=" * 60 + "\n")

    response1 = await orchestrator.process_message(
        message="My name is Alice. Remember this.",
        session_id=session_id,
        user_id=user_id,
    )

    print(f"🤖 VOXY Response:\n{response1['content'][:200]}...\n")
    print(
        f"📊 Usage: {response1['usage'].total_tokens if response1['usage'] else 0} tokens"
    )
    print(f"🔗 Thread ID: {response1['thread_id']}\n")

    # ===== MESSAGE 2: Second message (should load checkpoint) =====
    print("=" * 60)
    print("2️⃣  SECOND MESSAGE: 'What is my name?'")
    print("=" * 60 + "\n")

    print("🔍 Testing if VOXY remembers 'Alice' from previous message...\n")

    response2 = await orchestrator.process_message(
        message="What is my name?",
        session_id=session_id,  # Same session_id!
        user_id=user_id,
    )

    print(f"🤖 VOXY Response:\n{response2['content']}\n")
    print(
        f"📊 Usage: {response2['usage'].total_tokens if response2['usage'] else 0} tokens"
    )
    print(f"🔗 Thread ID: {response2['thread_id']}\n")

    # ===== VALIDATION =====
    print("=" * 60)
    print("✅ VALIDATION")
    print("=" * 60 + "\n")

    # Check if response mentions "Alice"
    response_text = response2["content"].lower()
    has_alice = "alice" in response_text

    print(f"Thread ID Match: {response1['thread_id'] == response2['thread_id']}")
    print(f"Response mentions 'Alice': {has_alice}\n")

    if has_alice:
        print("🎉 SUCCESS! Conversation history is working!")
        print("   VOXY remembered the name from the previous message.")
        return True
    else:
        print("❌ FAILURE! Conversation history NOT working!")
        print("   VOXY did not remember the name from previous message.")
        print(f"\n   Response was: {response2['content']}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Conversation History Test...\n")
    success = asyncio.run(test_conversation_history())

    exit_code = 0 if success else 1
    print(f"\n{'=' * 60}")
    print(f"Exit code: {exit_code}")
    print(f"{'=' * 60}\n")

    exit(exit_code)
