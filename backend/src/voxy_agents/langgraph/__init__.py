"""
LangGraph Migration Module

This module contains the LangGraph-based implementation of VOXY Agents,
implementing a gradual migration from OpenAI Agents SDK to LangGraph.

Architecture:
- graph_state.py: State management (VoxyState extending MessagesState)
- checkpointer.py: Checkpoint persistence utilities
- nodes/: LangGraph node implementations (translator, corrector, etc.)
- orchestrator.py: LangGraph supervisor service (replaces VoxyOrchestrator)

Migration Phases:
- Phase 1: Translator POC + basic graph structure ✅
- Phase 2: Supervisor graph + entry router
- Phase 3: All subagents migrated
- Phase 4: Observability + token tracking
- Phase 5: Testing + hard cut-over prep
- Phase 6: Arcade MCP readiness
"""

__version__ = "0.1.0"
