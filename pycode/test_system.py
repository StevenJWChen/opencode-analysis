#!/usr/bin/env python3
"""
PyCode System Test Suite

Comprehensive test program that validates all PyCode systems:
- Configuration
- Storage
- Sessions
- Message History
- Agents
- Tools
- Tool Registry
- Runner
- Doom Loop Detection
- CLI

All tests use real components (only LLM is mocked).
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, 'src')

from pycode.config import ConfigManager, load_config, PyCodeConfig, ModelConfig
from pycode.storage import Storage
from pycode.session_manager import SessionManager
from pycode.history import MessageHistory, ContextManager
from pycode.core import Session, Message, TextPart, ToolPart, ToolState, Identifier
from pycode.agents import BuildAgent, PlanAgent
from pycode.tools import (
    ToolRegistry,
    WriteTool,
    ReadTool,
    EditTool,
    BashTool,
    GrepTool,
    GlobTool,
    LsTool,
)
from pycode.runner import AgentRunner, RunConfig


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✅ {test_name}")

    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ❌ {test_name}: {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"  Test Results: {self.passed}/{total} passed")
        print(f"{'='*70}")

        if self.failed > 0:
            print(f"\n❌ {self.failed} tests failed:")
            for test_name, error in self.errors:
                print(f"   - {test_name}: {error}")
            return False
        else:
            print("\n✅ All tests passed!")
            return True


results = TestResults()


def test_header(name: str):
    """Print test section header"""
    print(f"\n{'-'*70}")
    print(f"  Testing: {name}")
    print(f"{'-'*70}")


# Mock provider for testing
class StreamEvent:
    """Mock event for provider streaming"""
    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data


class TestMockProvider:
    """Mock provider for testing"""
    def __init__(self):
        self.call_count = 0

    async def stream(self, model: str, messages: list, system: str, tools: list):
        """Simulate a simple LLM response"""
        self.call_count += 1

        if self.call_count == 1:
            # Return a simple text response
            yield StreamEvent("text_delta", {"text": "Test response from mock LLM"})
        else:
            # Just text, no tools
            yield StreamEvent("text_delta", {"text": "Done"})


# ============================================================================
# TEST 1: Configuration System
# ============================================================================

def test_configuration():
    """Test configuration system"""
    test_header("Configuration System")

    try:
        # Test 1.1: Load default config
        config = load_config()
        if isinstance(config, PyCodeConfig):
            results.record_pass("Load default configuration")
        else:
            results.record_fail("Load default configuration", "Wrong type returned")

        # Test 1.2: Verify runtime settings
        if config.runtime.max_iterations > 0:
            results.record_pass("Runtime settings present")
        else:
            results.record_fail("Runtime settings", "Invalid max_iterations")

        # Test 1.3: Verify model settings
        if config.default_model.model_id:
            results.record_pass("Model configuration present")
        else:
            results.record_fail("Model configuration", "No model_id")

        # Test 1.4: Verify agent configs
        if "build" in config.agents and "plan" in config.agents:
            results.record_pass("Agent configurations present")
        else:
            results.record_fail("Agent configurations", "Missing agents")

        # Test 1.5: ConfigManager
        manager = ConfigManager()
        if manager is not None:
            results.record_pass("ConfigManager instantiation")
        else:
            results.record_fail("ConfigManager", "Failed to create")

    except Exception as e:
        results.record_fail("Configuration system", str(e))


# ============================================================================
# TEST 2: Storage System
# ============================================================================

async def test_storage():
    """Test storage system"""
    test_header("Storage System")

    try:
        # Test 2.1: Create storage
        storage = Storage()
        results.record_pass("Storage instantiation")

        # Test 2.2: Write data
        test_key = ["test", "key", "path"]
        test_data = {"value": "test"}
        await storage.write(test_key, test_data)
        results.record_pass("Write data to storage")

        # Test 2.3: Read data
        read_data = await storage.read(test_key)
        if read_data == test_data:
            results.record_pass("Read data from storage")
        else:
            results.record_fail("Read data", f"Expected {test_data}, got {read_data}")

        # Test 2.4: Delete data
        await storage.delete(test_key)
        deleted_data = await storage.read(test_key)
        if deleted_data is None:
            results.record_pass("Delete data from storage")
        else:
            results.record_fail("Delete data", "Data still exists")

    except Exception as e:
        results.record_fail("Storage system", str(e))


# ============================================================================
# TEST 3: Identifiers
# ============================================================================

def test_identifiers():
    """Test identifier generation"""
    test_header("Identifier System")

    try:
        # Test 3.1: Generate ascending ID
        id1 = Identifier.ascending("message")
        if id1.startswith("message_"):
            results.record_pass("Generate ascending identifier")
        else:
            results.record_fail("Ascending ID", f"Invalid format: {id1}")

        # Test 3.2: Generate descending ID
        id2 = Identifier.descending("session")
        if id2.startswith("session_"):
            results.record_pass("Generate descending identifier")
        else:
            results.record_fail("Descending ID", f"Invalid format: {id2}")

        # Test 3.3: Uniqueness
        id3 = Identifier.ascending("message")
        if id1 != id3:
            results.record_pass("Identifier uniqueness")
        else:
            results.record_fail("Uniqueness", "Generated duplicate ID")

    except Exception as e:
        results.record_fail("Identifier system", str(e))


# ============================================================================
# TEST 4: Sessions
# ============================================================================

async def test_sessions():
    """Test session management"""
    test_header("Session Management")

    try:
        storage = Storage()
        manager = SessionManager(storage)

        # Test 4.1: Create session
        session = await manager.create_session(
            project_id="test-project",
            directory="/tmp",
            title="Test Session"
        )
        if session.id.startswith("session_"):
            results.record_pass("Create session")
        else:
            results.record_fail("Create session", "Invalid session ID")

        # Test 4.2: Load session
        loaded = await manager.load_session(session.id, session.project_id)
        if loaded and loaded.id == session.id:
            results.record_pass("Load session")
        else:
            results.record_fail("Load session", "Failed to load")

        # Test 4.3: List sessions
        sessions = await manager.list_sessions("test-project", limit=10)
        if len(sessions) > 0:
            results.record_pass("List sessions")
        else:
            results.record_fail("List sessions", "No sessions found")

        # Test 4.4: Session stats
        stats = await manager.get_session_stats(session.id, session.project_id)
        if "created" in stats:
            results.record_pass("Get session statistics")
        else:
            results.record_fail("Session stats", "Missing data")

        # Test 4.5: Delete session
        await manager.delete_session(session.id, session.project_id)
        deleted = await manager.load_session(session.id, session.project_id)
        if deleted is None:
            results.record_pass("Delete session")
        else:
            results.record_fail("Delete session", "Session still exists")

    except Exception as e:
        results.record_fail("Session management", str(e))


# ============================================================================
# TEST 5: Message History
# ============================================================================

async def test_message_history():
    """Test message history"""
    test_header("Message History")

    try:
        storage = Storage()
        history = MessageHistory(storage)

        # Create a test session
        session = Session(
            project_id="test-project",
            directory="/tmp",
            title="Test"
        )

        # Test 5.1: Create message
        message = Message(session_id=session.id, role="user")
        message.add_part(TextPart(
            session_id=session.id,
            message_id=message.id,
            text="Test message"
        ))
        results.record_pass("Create message with parts")

        # Test 5.2: Save message
        await history.save_message(session.id, message)
        results.record_pass("Save message to history")

        # Test 5.3: Load messages
        messages = await history.load_messages(session.id, limit=10)
        if len(messages) > 0:
            results.record_pass("Load messages from history")
        else:
            results.record_fail("Load messages", "No messages found")

        # Test 5.4: Get conversation for LLM
        conversation = await history.get_conversation_for_llm(session.id, max_messages=10)
        if isinstance(conversation, list):
            results.record_pass("Build conversation for LLM")
        else:
            results.record_fail("Conversation build", "Invalid format")

        # Test 5.5: Message count
        count = await history.get_message_count(session.id)
        if count > 0:
            results.record_pass("Count messages")
        else:
            results.record_fail("Message count", f"Expected > 0, got {count}")

        # Test 5.6: Clear history
        await history.clear_history(session.id)
        count_after = await history.get_message_count(session.id)
        if count_after == 0:
            results.record_pass("Clear message history")
        else:
            results.record_fail("Clear history", f"Count is {count_after}")

    except Exception as e:
        results.record_fail("Message history", str(e))


# ============================================================================
# TEST 6: Context Management
# ============================================================================

def test_context_manager():
    """Test context management"""
    test_header("Context Management")

    try:
        manager = ContextManager()

        # Test 6.1: Estimate tokens
        text = "This is a test message"
        tokens = manager.estimate_tokens(text)
        if tokens > 0:
            results.record_pass("Estimate tokens")
        else:
            results.record_fail("Token estimation", f"Got {tokens}")

        # Test 6.2: Prune conversation
        conversation = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
        ]
        pruned = manager.prune_conversation(conversation, target_tokens=1000)
        if isinstance(pruned, list):
            results.record_pass("Prune conversation")
        else:
            results.record_fail("Prune conversation", "Invalid result")

    except Exception as e:
        results.record_fail("Context management", str(e))


# ============================================================================
# TEST 7: Agents
# ============================================================================

async def test_agents():
    """Test agent system"""
    test_header("Agent System")

    try:
        # Test 7.1: Create BuildAgent
        build_agent = BuildAgent()
        if build_agent.name == "build":
            results.record_pass("Create BuildAgent")
        else:
            results.record_fail("BuildAgent", f"Wrong name: {build_agent.name}")

        # Test 7.2: Get system prompt
        prompt = await build_agent.get_system_prompt()
        if len(prompt) > 0:
            results.record_pass("Get agent system prompt")
        else:
            results.record_fail("System prompt", "Empty prompt")

        # Test 7.3: Check tool access
        can_use_write = build_agent.can_use_tool("write")
        if can_use_write:
            results.record_pass("Agent tool permissions")
        else:
            results.record_fail("Tool permissions", "Can't use write tool")

        # Test 7.4: Create PlanAgent
        plan_agent = PlanAgent()
        if plan_agent.name == "plan":
            results.record_pass("Create PlanAgent")
        else:
            results.record_fail("PlanAgent", f"Wrong name: {plan_agent.name}")

        # Test 7.5: PlanAgent restrictions
        can_edit = plan_agent.can_use_tool("write")
        if not can_edit:
            results.record_pass("PlanAgent restrictions")
        else:
            results.record_fail("Plan restrictions", "Can use write tool")

    except Exception as e:
        results.record_fail("Agent system", str(e))


# ============================================================================
# TEST 8: Tools
# ============================================================================

async def test_tools():
    """Test tool system"""
    test_header("Tool System")

    # Create temp directory for tests
    temp_dir = tempfile.mkdtemp()

    try:
        from pycode.tools import ToolContext

        context = ToolContext(
            session_id="test_session",
            message_id="test_message",
            agent_name="test_agent",
            working_directory=temp_dir
        )

        # Test 8.1: WriteTool
        write_tool = WriteTool()
        test_file = os.path.join(temp_dir, "test.txt")
        result = await write_tool.execute({
            "file_path": test_file,
            "content": "Hello, PyCode!"
        }, context)
        if result.error is None and os.path.exists(test_file):
            results.record_pass("WriteTool execution")
        else:
            results.record_fail("WriteTool", result.error or "File not created")

        # Test 8.2: ReadTool
        read_tool = ReadTool()
        result = await read_tool.execute({
            "file_path": test_file
        }, context)
        if "Hello, PyCode!" in result.output:
            results.record_pass("ReadTool execution")
        else:
            results.record_fail("ReadTool", "Content mismatch")

        # Test 8.3: BashTool
        bash_tool = BashTool()
        result = await bash_tool.execute({
            "command": "echo 'test'",
            "description": "Test echo command"
        }, context)
        if result.error is None and "test" in result.output:
            results.record_pass("BashTool execution")
        else:
            results.record_fail("BashTool", result.error or f"Output: {result.output}")

        # Test 8.4: GlobTool
        glob_tool = GlobTool()
        result = await glob_tool.execute({
            "pattern": "*.txt",
            "path": temp_dir
        }, context)
        if "test.txt" in result.output:
            results.record_pass("GlobTool execution")
        else:
            results.record_fail("GlobTool", "File not found")

        # Test 8.5: LsTool
        ls_tool = LsTool()
        result = await ls_tool.execute({
            "path": temp_dir
        }, context)
        if "test.txt" in result.output:
            results.record_pass("LsTool execution")
        else:
            results.record_fail("LsTool", "File not listed")

    except Exception as e:
        results.record_fail("Tool system", str(e))
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# TEST 9: Tool Registry
# ============================================================================

def test_tool_registry():
    """Test tool registry"""
    test_header("Tool Registry")

    try:
        registry = ToolRegistry()

        # Test 9.1: Register tool
        write_tool = WriteTool()
        registry.register(write_tool)
        results.record_pass("Register tool")

        # Test 9.2: Get tool
        tool = registry.get("write")
        if tool is not None:
            results.record_pass("Retrieve tool")
        else:
            results.record_fail("Get tool", "Tool not found")

        # Test 9.3: Get all tools
        all_tools = registry.get_all()
        if "write" in all_tools:
            results.record_pass("List all tools")
        else:
            results.record_fail("List tools", "Tool not in list")

        # Test 9.4: Register multiple tools
        registry.register(ReadTool())
        registry.register(BashTool())
        if len(registry.get_all()) >= 3:
            results.record_pass("Register multiple tools")
        else:
            results.record_fail("Multiple tools", f"Only {len(registry.get_all())} tools")

    except Exception as e:
        results.record_fail("Tool registry", str(e))


# ============================================================================
# TEST 10: Agent Runner
# ============================================================================

async def test_runner():
    """Test agent runner"""
    test_header("Agent Runner")

    try:
        # Setup
        storage = Storage()
        session_manager = SessionManager(storage)
        session = await session_manager.create_session(
            project_id="test-runner",
            directory="/tmp",
            title="Runner Test"
        )

        agent = BuildAgent()
        provider = TestMockProvider()

        registry = ToolRegistry()
        registry.register(WriteTool())
        registry.register(ReadTool())
        registry.register(BashTool())

        config = RunConfig(
            max_iterations=5,
            verbose=False,
            auto_approve_tools=True,
            doom_loop_detection=True,
            doom_loop_threshold=3,
        )

        # Test 10.1: Create runner
        runner = AgentRunner(
            session=session,
            agent=agent,
            provider=provider,
            registry=registry,
            config=config,
            storage=storage,
        )
        results.record_pass("Create AgentRunner")

        # Test 10.2: Run simple request
        full_response = ""
        async for chunk in runner.run("Test request"):
            full_response += chunk

        if "Test response" in full_response:
            results.record_pass("Run agent with request")
        else:
            results.record_fail("Run agent", f"Response: {full_response}")

        # Test 10.3: Verify message persistence
        history = MessageHistory(storage)
        messages = await history.load_messages(session.id)
        if len(messages) >= 2:  # User + Assistant
            results.record_pass("Message persistence")
        else:
            results.record_fail("Message persistence", f"Only {len(messages)} messages")

        # Cleanup
        await session_manager.delete_session(session.id, session.project_id)

    except Exception as e:
        results.record_fail("Agent runner", str(e))


# ============================================================================
# TEST 11: Doom Loop Detection
# ============================================================================

async def test_doom_loop():
    """Test doom loop detection"""
    test_header("Doom Loop Detection")

    class DoomLoopProvider:
        """Provider that triggers doom loop"""
        async def stream(self, model: str, messages: list, system: str, tools: list):
            # Always request the same tool
            yield StreamEvent("text_delta", {"text": "Running same command\n"})
            yield StreamEvent("tool_use", {
                "id": "call_doom",
                "name": "bash",
                "arguments": {"command": "echo 'test'"}
            })

    try:
        storage = Storage()
        session_manager = SessionManager(storage)
        session = await session_manager.create_session(
            project_id="test-doom",
            directory="/tmp",
            title="Doom Loop Test"
        )

        agent = BuildAgent()
        provider = DoomLoopProvider()

        registry = ToolRegistry()
        registry.register(BashTool())

        config = RunConfig(
            max_iterations=10,
            verbose=False,
            auto_approve_tools=True,
            doom_loop_detection=True,
            doom_loop_threshold=3,
        )

        runner = AgentRunner(
            session=session,
            agent=agent,
            provider=provider,
            registry=registry,
            config=config,
            storage=storage,
        )

        # Test 11.1: Doom loop detection
        full_response = ""
        async for chunk in runner.run("Cause doom loop"):
            full_response += chunk

        if "DOOM LOOP DETECTED" in full_response:
            results.record_pass("Doom loop detection")
        else:
            results.record_fail("Doom loop", "Loop not detected")

        # Cleanup
        await session_manager.delete_session(session.id, session.project_id)

    except Exception as e:
        results.record_fail("Doom loop detection", str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  PyCode System Test Suite")
    print("  Testing all components with real implementations")
    print("=" * 70)

    # Run all tests
    test_configuration()
    await test_storage()
    test_identifiers()
    await test_sessions()
    await test_message_history()
    test_context_manager()
    await test_agents()
    await test_tools()
    test_tool_registry()
    await test_runner()
    await test_doom_loop()

    # Print summary
    success = results.summary()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
