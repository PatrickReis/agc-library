"""
Agent execution tracing for understanding agent behavior and tool usage
"""

import time
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
from contextlib import contextmanager

from ..logger.logger import get_logger

logger = get_logger("agent_tracer")

@dataclass
class TraceEvent:
    """Single trace event"""
    trace_id: str
    event_id: str
    parent_id: Optional[str]
    timestamp: float
    event_type: str
    agent_id: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None

@dataclass
class ExecutionTrace:
    """Complete execution trace"""
    trace_id: str
    start_time: float
    end_time: Optional[float]
    agent_id: str
    total_duration_ms: Optional[float]
    events: List[TraceEvent]
    metadata: Dict[str, Any]

class AgentTracer:
    """
    Trace agent executions to understand behavior patterns
    """

    def __init__(self):
        self.active_traces: Dict[str, ExecutionTrace] = {}
        self.completed_traces: List[ExecutionTrace] = []
        self.max_completed_traces = 100
        self.lock = threading.Lock()

        # Event stack for nested operations
        self._event_stack = threading.local()

    def start_trace(self, agent_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Start a new execution trace

        Args:
            agent_id: Unique identifier for the agent
            metadata: Additional metadata for the trace

        Returns:
            Trace ID
        """
        trace_id = str(uuid.uuid4())

        trace = ExecutionTrace(
            trace_id=trace_id,
            start_time=time.time(),
            end_time=None,
            agent_id=agent_id,
            total_duration_ms=None,
            events=[],
            metadata=metadata or {}
        )

        with self.lock:
            self.active_traces[trace_id] = trace

        logger.info(f"🔍 Started trace {trace_id[:8]} for agent {agent_id}")
        return trace_id

    def end_trace(self, trace_id: str):
        """
        End an execution trace

        Args:
            trace_id: ID of the trace to end
        """
        with self.lock:
            if trace_id not in self.active_traces:
                logger.warning(f"Unknown trace ID: {trace_id}")
                return

            trace = self.active_traces.pop(trace_id)
            trace.end_time = time.time()
            trace.total_duration_ms = (trace.end_time - trace.start_time) * 1000

            # Add to completed traces
            self.completed_traces.append(trace)

            # Keep only recent traces
            if len(self.completed_traces) > self.max_completed_traces:
                self.completed_traces = self.completed_traces[-self.max_completed_traces:]

        logger.info(f"✅ Completed trace {trace_id[:8]} in {trace.total_duration_ms:.0f}ms")

    @contextmanager
    def trace_event(self,
                   trace_id: str,
                   event_type: str,
                   data: Optional[Dict] = None):
        """
        Context manager for tracing events

        Args:
            trace_id: ID of the active trace
            event_type: Type of event being traced
            data: Event data

        Example:
            with tracer.trace_event(trace_id, "tool_call", {"tool": "search"}):
                # ... perform tool call
                pass
        """
        event_id = str(uuid.uuid4())
        start_time = time.time()

        # Get parent event ID if nested
        parent_id = None
        if hasattr(self._event_stack, 'stack') and self._event_stack.stack:
            parent_id = self._event_stack.stack[-1]

        # Initialize event stack if needed
        if not hasattr(self._event_stack, 'stack'):
            self._event_stack.stack = []

        self._event_stack.stack.append(event_id)

        try:
            yield event_id
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Remove from stack
            if self._event_stack.stack and self._event_stack.stack[-1] == event_id:
                self._event_stack.stack.pop()

            # Create event
            event = TraceEvent(
                trace_id=trace_id,
                event_id=event_id,
                parent_id=parent_id,
                timestamp=start_time,
                event_type=event_type,
                agent_id=self._get_agent_id_for_trace(trace_id),
                data=data or {},
                duration_ms=duration_ms
            )

            # Add to trace
            with self.lock:
                if trace_id in self.active_traces:
                    self.active_traces[trace_id].events.append(event)

            logger.debug(f"📊 {event_type} completed in {duration_ms:.1f}ms")

    def add_event(self,
                 trace_id: str,
                 event_type: str,
                 data: Optional[Dict] = None):
        """
        Add a simple event to the trace

        Args:
            trace_id: ID of the active trace
            event_type: Type of event
            data: Event data
        """
        event_id = str(uuid.uuid4())

        # Get parent event ID if nested
        parent_id = None
        if hasattr(self._event_stack, 'stack') and self._event_stack.stack:
            parent_id = self._event_stack.stack[-1]

        event = TraceEvent(
            trace_id=trace_id,
            event_id=event_id,
            parent_id=parent_id,
            timestamp=time.time(),
            event_type=event_type,
            agent_id=self._get_agent_id_for_trace(trace_id),
            data=data or {}
        )

        with self.lock:
            if trace_id in self.active_traces:
                self.active_traces[trace_id].events.append(event)

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Get a trace by ID"""
        with self.lock:
            # Check active traces
            if trace_id in self.active_traces:
                return self.active_traces[trace_id]

            # Check completed traces
            for trace in self.completed_traces:
                if trace.trace_id == trace_id:
                    return trace

        return None

    def get_traces_for_agent(self, agent_id: str) -> List[ExecutionTrace]:
        """Get all traces for a specific agent"""
        traces = []

        with self.lock:
            # Active traces
            for trace in self.active_traces.values():
                if trace.agent_id == agent_id:
                    traces.append(trace)

            # Completed traces
            for trace in self.completed_traces:
                if trace.agent_id == agent_id:
                    traces.append(trace)

        return traces

    def analyze_agent_behavior(self, agent_id: str) -> Dict[str, Any]:
        """
        Analyze behavior patterns for an agent

        Args:
            agent_id: Agent to analyze

        Returns:
            Analysis results
        """
        traces = self.get_traces_for_agent(agent_id)

        if not traces:
            return {"error": "No traces found for agent"}

        # Aggregate statistics
        total_executions = len(traces)
        completed_executions = len([t for t in traces if t.end_time is not None])

        # Duration analysis
        durations = [t.total_duration_ms for t in traces if t.total_duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Event type analysis
        event_types = defaultdict(int)
        tool_usage = defaultdict(int)
        error_count = 0

        for trace in traces:
            for event in trace.events:
                event_types[event.event_type] += 1

                if event.event_type == "tool_call":
                    tool_name = event.data.get("tool_name", "unknown")
                    tool_usage[tool_name] += 1

                if event.event_type == "error":
                    error_count += 1

        # Success rate
        success_rate = (completed_executions - error_count) / completed_executions if completed_executions > 0 else 0

        return {
            "agent_id": agent_id,
            "summary": {
                "total_executions": total_executions,
                "completed_executions": completed_executions,
                "avg_duration_ms": avg_duration,
                "success_rate": success_rate
            },
            "event_patterns": dict(event_types),
            "tool_usage": dict(tool_usage),
            "most_used_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def find_performance_bottlenecks(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Find performance bottlenecks in a trace

        Args:
            trace_id: Trace to analyze

        Returns:
            List of potential bottlenecks
        """
        trace = self.get_trace(trace_id)
        if not trace:
            return []

        bottlenecks = []

        # Find slow events (> 1 second)
        slow_events = [
            e for e in trace.events
            if e.duration_ms and e.duration_ms > 1000
        ]

        for event in slow_events:
            bottlenecks.append({
                "type": "slow_event",
                "event_type": event.event_type,
                "duration_ms": event.duration_ms,
                "data": event.data
            })

        # Find repeated tool calls
        tool_calls = [e for e in trace.events if e.event_type == "tool_call"]
        tool_counts = defaultdict(int)

        for event in tool_calls:
            tool_name = event.data.get("tool_name", "unknown")
            tool_counts[tool_name] += 1

        for tool_name, count in tool_counts.items():
            if count > 3:  # More than 3 calls to same tool
                bottlenecks.append({
                    "type": "repeated_tool_calls",
                    "tool_name": tool_name,
                    "call_count": count
                })

        return bottlenecks

    def export_trace(self, trace_id: str, output_path: str):
        """
        Export trace to file

        Args:
            trace_id: Trace to export
            output_path: Path to save trace
        """
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")

        # Convert to serializable format
        output_data = {
            "trace": asdict(trace),
            "analysis": self.analyze_agent_behavior(trace.agent_id),
            "bottlenecks": self.find_performance_bottlenecks(trace_id),
            "export_timestamp": time.time()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Trace exported to {output_path}")

    def _get_agent_id_for_trace(self, trace_id: str) -> str:
        """Get agent ID for a trace"""
        with self.lock:
            if trace_id in self.active_traces:
                return self.active_traces[trace_id].agent_id
        return "unknown"

    def clear_traces(self):
        """Clear all traces"""
        with self.lock:
            self.active_traces.clear()
            self.completed_traces.clear()

        logger.info("All traces cleared")

    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of all traces"""
        with self.lock:
            active_count = len(self.active_traces)
            completed_count = len(self.completed_traces)

            agents = set()
            for trace in list(self.active_traces.values()) + self.completed_traces:
                agents.add(trace.agent_id)

        return {
            "active_traces": active_count,
            "completed_traces": completed_count,
            "total_agents": len(agents),
            "agents": list(agents)
        }

# Global tracer instance
_global_tracer = AgentTracer()

def get_tracer() -> AgentTracer:
    """Get the global tracer instance"""
    return _global_tracer