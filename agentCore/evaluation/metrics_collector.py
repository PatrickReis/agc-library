"""
Metrics collection and observability for AgentCore evaluations
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from pathlib import Path

from ..logger.logger import get_logger

logger = get_logger("metrics_collector")

@dataclass
class MetricEvent:
    """Single metric event"""
    timestamp: float
    event_type: str
    agent_id: str
    tool_name: Optional[str]
    duration_ms: float
    success: bool
    metadata: Dict[str, Any]

class MetricsCollector:
    """
    Collect and analyze metrics from agent executions
    """

    def __init__(self, buffer_size: int = 1000):
        """
        Initialize metrics collector

        Args:
            buffer_size: Maximum number of events to keep in memory
        """
        self.buffer_size = buffer_size
        self.events = deque(maxlen=buffer_size)
        self.session_metrics = defaultdict(list)
        self.lock = threading.Lock()

        # Performance tracking
        self.active_executions = {}

    def start_execution(self, agent_id: str, operation: str) -> str:
        """
        Start tracking an execution

        Args:
            agent_id: Unique identifier for the agent
            operation: Operation being performed

        Returns:
            Execution ID for later reference
        """
        execution_id = f"{agent_id}_{operation}_{int(time.time() * 1000)}"

        with self.lock:
            self.active_executions[execution_id] = {
                "agent_id": agent_id,
                "operation": operation,
                "start_time": time.time(),
                "tools_used": []
            }

        return execution_id

    def end_execution(self,
                     execution_id: str,
                     success: bool = True,
                     metadata: Optional[Dict] = None):
        """
        End tracking an execution

        Args:
            execution_id: ID from start_execution
            success: Whether execution was successful
            metadata: Additional metadata
        """
        with self.lock:
            if execution_id not in self.active_executions:
                logger.warning(f"Unknown execution ID: {execution_id}")
                return

            execution = self.active_executions.pop(execution_id)
            duration_ms = (time.time() - execution["start_time"]) * 1000

            event = MetricEvent(
                timestamp=time.time(),
                event_type="execution",
                agent_id=execution["agent_id"],
                tool_name=None,
                duration_ms=duration_ms,
                success=success,
                metadata={
                    "operation": execution["operation"],
                    "tools_used": execution["tools_used"],
                    **(metadata or {})
                }
            )

            self.events.append(event)

    def record_tool_usage(self,
                         agent_id: str,
                         tool_name: str,
                         duration_ms: float,
                         success: bool = True,
                         metadata: Optional[Dict] = None):
        """
        Record tool usage

        Args:
            agent_id: Agent using the tool
            tool_name: Name of the tool
            duration_ms: How long the tool took
            success: Whether tool call was successful
            metadata: Additional metadata
        """
        event = MetricEvent(
            timestamp=time.time(),
            event_type="tool_usage",
            agent_id=agent_id,
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
            metadata=metadata or {}
        )

        with self.lock:
            self.events.append(event)

            # Add to active executions if any
            for execution in self.active_executions.values():
                if execution["agent_id"] == agent_id:
                    execution["tools_used"].append({
                        "tool_name": tool_name,
                        "duration_ms": duration_ms,
                        "success": success
                    })

    def record_llm_call(self,
                       agent_id: str,
                       model: str,
                       input_tokens: int,
                       output_tokens: int,
                       duration_ms: float,
                       success: bool = True):
        """
        Record LLM API call

        Args:
            agent_id: Agent making the call
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Call duration
            success: Whether call was successful
        """
        self.record_tool_usage(
            agent_id=agent_id,
            tool_name="llm_call",
            duration_ms=duration_ms,
            success=success,
            metadata={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        )

    def get_metrics_summary(self,
                           time_window_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Get summary of collected metrics

        Args:
            time_window_minutes: Only consider events from last N minutes

        Returns:
            Dictionary with metric summaries
        """
        with self.lock:
            events = list(self.events)

        # Filter by time window if specified
        if time_window_minutes:
            cutoff_time = time.time() - (time_window_minutes * 60)
            events = [e for e in events if e.timestamp >= cutoff_time]

        if not events:
            return {"total_events": 0}

        # Calculate metrics
        total_events = len(events)
        successful_events = len([e for e in events if e.success])
        success_rate = successful_events / total_events

        # Tool usage metrics
        tool_events = [e for e in events if e.event_type == "tool_usage"]
        tool_usage = defaultdict(int)
        tool_latencies = defaultdict(list)

        for event in tool_events:
            if event.tool_name:
                tool_usage[event.tool_name] += 1
                tool_latencies[event.tool_name].append(event.duration_ms)

        # Agent metrics
        agent_events = defaultdict(list)
        for event in events:
            agent_events[event.agent_id].append(event)

        # Execution metrics
        execution_events = [e for e in events if e.event_type == "execution"]
        avg_execution_time = sum(e.duration_ms for e in execution_events) / len(execution_events) if execution_events else 0

        # LLM metrics
        llm_events = [e for e in tool_events if e.tool_name == "llm_call"]
        total_tokens = sum(e.metadata.get("total_tokens", 0) for e in llm_events)
        avg_llm_latency = sum(e.duration_ms for e in llm_events) / len(llm_events) if llm_events else 0

        return {
            "summary": {
                "total_events": total_events,
                "success_rate": success_rate,
                "time_window_minutes": time_window_minutes,
                "avg_execution_time_ms": avg_execution_time
            },
            "tool_usage": {
                "most_used_tools": dict(sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]),
                "avg_tool_latencies": {
                    tool: sum(latencies) / len(latencies)
                    for tool, latencies in tool_latencies.items()
                }
            },
            "agent_activity": {
                "active_agents": len(agent_events),
                "events_per_agent": {
                    agent_id: len(events)
                    for agent_id, events in agent_events.items()
                }
            },
            "llm_metrics": {
                "total_llm_calls": len(llm_events),
                "total_tokens": total_tokens,
                "avg_llm_latency_ms": avg_llm_latency
            }
        }

    def export_metrics(self, output_path: str, format: str = "json"):
        """
        Export metrics to file

        Args:
            output_path: Path to save metrics
            format: Export format (json, csv)
        """
        with self.lock:
            events = list(self.events)

        if format.lower() == "json":
            output_data = {
                "metrics_summary": self.get_metrics_summary(),
                "events": [asdict(event) for event in events],
                "export_timestamp": time.time()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

        elif format.lower() == "csv":
            import pandas as pd

            # Convert events to DataFrame
            events_data = []
            for event in events:
                row = asdict(event)
                # Flatten metadata
                if row["metadata"]:
                    for key, value in row["metadata"].items():
                        row[f"metadata_{key}"] = value
                del row["metadata"]
                events_data.append(row)

            df = pd.DataFrame(events_data)
            df.to_csv(output_path, index=False)

        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Metrics exported to {output_path}")

    def get_agent_trace(self, agent_id: str) -> List[MetricEvent]:
        """
        Get execution trace for a specific agent

        Args:
            agent_id: Agent to trace

        Returns:
            List of events for this agent
        """
        with self.lock:
            return [event for event in self.events if event.agent_id == agent_id]

    def detect_performance_issues(self) -> Dict[str, List[str]]:
        """
        Detect potential performance issues

        Returns:
            Dictionary with issue categories and descriptions
        """
        issues = defaultdict(list)
        summary = self.get_metrics_summary()

        # Check success rate
        if summary.get("summary", {}).get("success_rate", 1.0) < 0.9:
            issues["reliability"].append(f"Low success rate: {summary['summary']['success_rate']:.2%}")

        # Check tool latencies
        tool_latencies = summary.get("tool_usage", {}).get("avg_tool_latencies", {})
        for tool, latency in tool_latencies.items():
            if latency > 5000:  # > 5 seconds
                issues["performance"].append(f"Slow tool: {tool} ({latency:.0f}ms)")

        # Check LLM performance
        llm_latency = summary.get("llm_metrics", {}).get("avg_llm_latency_ms", 0)
        if llm_latency > 3000:  # > 3 seconds
            issues["performance"].append(f"Slow LLM calls: {llm_latency:.0f}ms average")

        # Check for error patterns
        with self.lock:
            failed_events = [e for e in self.events if not e.success]

        if failed_events:
            # Group by error type
            error_types = defaultdict(int)
            for event in failed_events:
                error_type = event.metadata.get("error_type", "unknown")
                error_types[error_type] += 1

            for error_type, count in error_types.items():
                if count > 5:  # More than 5 of same error
                    issues["errors"].append(f"Frequent {error_type} errors: {count} occurrences")

        return dict(issues)

    def clear_metrics(self):
        """Clear all collected metrics"""
        with self.lock:
            self.events.clear()
            self.active_executions.clear()
            self.session_metrics.clear()

        logger.info("Metrics cleared")

# Global metrics collector instance
_global_metrics = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return _global_metrics