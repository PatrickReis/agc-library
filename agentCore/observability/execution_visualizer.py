"""
Execution visualization for agent traces
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .agent_tracer import ExecutionTrace, TraceEvent
from ..logger.logger import get_logger

logger = get_logger("execution_visualizer")

class ExecutionVisualizer:
    """
    Create visualizations of agent execution traces
    """

    def __init__(self):
        self.trace_data = {}

    def generate_mermaid_diagram(self, trace: ExecutionTrace) -> str:
        """
        Generate Mermaid diagram for execution trace

        Args:
            trace: Execution trace to visualize

        Returns:
            Mermaid diagram as string
        """
        lines = ["graph TD"]

        # Create nodes for events
        for i, event in enumerate(trace.events):
            node_id = f"E{i}"
            label = f"{event.event_type}"

            if event.duration_ms:
                label += f"<br/>{event.duration_ms:.0f}ms"

            # Add tool name if it's a tool call
            if event.event_type == "tool_call" and "tool_name" in event.data:
                label += f"<br/>{event.data['tool_name']}"

            lines.append(f'    {node_id}["{label}"]')

        # Create connections based on parent-child relationships
        event_map = {event.event_id: i for i, event in enumerate(trace.events)}

        for i, event in enumerate(trace.events):
            node_id = f"E{i}"

            if event.parent_id and event.parent_id in event_map:
                parent_idx = event_map[event.parent_id]
                parent_id = f"E{parent_idx}"
                lines.append(f"    {parent_id} --> {node_id}")

        # Add styling
        lines.extend([
            "",
            "    classDef toolCall fill:#e1f5fe",
            "    classDef llmCall fill:#f3e5f5",
            "    classDef error fill:#ffebee",
            ""
        ])

        # Apply styles
        for i, event in enumerate(trace.events):
            node_id = f"E{i}"
            if event.event_type == "tool_call":
                lines.append(f"    class {node_id} toolCall")
            elif event.event_type == "llm_call":
                lines.append(f"    class {node_id} llmCall")
            elif event.event_type == "error":
                lines.append(f"    class {node_id} error")

        return "\n".join(lines)

    def generate_timeline_html(self, trace: ExecutionTrace) -> str:
        """
        Generate HTML timeline visualization

        Args:
            trace: Execution trace to visualize

        Returns:
            HTML content as string
        """
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Agent Execution Trace - {trace_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .timeline {{ position: relative; padding: 20px 0; }}
                .event {{
                    margin: 10px 0;
                    padding: 10px;
                    border-left: 4px solid #2196F3;
                    background: #f5f5f5;
                    border-radius: 4px;
                }}
                .event.tool-call {{ border-left-color: #4CAF50; }}
                .event.llm-call {{ border-left-color: #FF9800; }}
                .event.error {{ border-left-color: #f44336; }}
                .duration {{ float: right; color: #666; font-size: 0.9em; }}
                .event-data {{ margin-top: 5px; font-size: 0.9em; color: #444; }}
                .header {{ background: #1976D2; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat {{ padding: 15px; background: #e3f2fd; border-radius: 8px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Agent Execution Trace</h1>
                <p>Agent: {agent_id} | Trace ID: {trace_id}</p>
                <p>Duration: {total_duration:.0f}ms | Events: {event_count}</p>
            </div>

            <div class="stats">
                <div class="stat">
                    <h3>{tool_calls}</h3>
                    <p>Tool Calls</p>
                </div>
                <div class="stat">
                    <h3>{llm_calls}</h3>
                    <p>LLM Calls</p>
                </div>
                <div class="stat">
                    <h3>{errors}</h3>
                    <p>Errors</p>
                </div>
            </div>

            <div class="timeline">
                {events_html}
            </div>
        </body>
        </html>
        """

        # Generate events HTML
        events_html = []
        tool_calls = 0
        llm_calls = 0
        errors = 0

        for event in trace.events:
            css_class = "event"
            if event.event_type == "tool_call":
                css_class += " tool-call"
                tool_calls += 1
            elif event.event_type == "llm_call":
                css_class += " llm-call"
                llm_calls += 1
            elif event.event_type == "error":
                css_class += " error"
                errors += 1

            duration_text = f"{event.duration_ms:.0f}ms" if event.duration_ms else ""

            # Format event data
            data_items = []
            for key, value in event.data.items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                data_items.append(f"<strong>{key}:</strong> {value}")

            data_html = "<br/>".join(data_items) if data_items else ""

            event_html = f"""
            <div class="{css_class}">
                <strong>{event.event_type}</strong>
                <span class="duration">{duration_text}</span>
                <div class="event-data">{data_html}</div>
            </div>
            """
            events_html.append(event_html)

        return html_template.format(
            trace_id=trace.trace_id[:8],
            agent_id=trace.agent_id,
            total_duration=trace.total_duration_ms or 0,
            event_count=len(trace.events),
            tool_calls=tool_calls,
            llm_calls=llm_calls,
            errors=errors,
            events_html="".join(events_html)
        )

    def generate_json_report(self, trace: ExecutionTrace) -> str:
        """
        Generate JSON report for trace

        Args:
            trace: Execution trace

        Returns:
            JSON report as string
        """
        # Analyze trace
        analysis = self._analyze_trace(trace)

        report = {
            "trace_id": trace.trace_id,
            "agent_id": trace.agent_id,
            "execution_summary": {
                "start_time": datetime.fromtimestamp(trace.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(trace.end_time).isoformat() if trace.end_time else None,
                "total_duration_ms": trace.total_duration_ms,
                "total_events": len(trace.events)
            },
            "analysis": analysis,
            "events": [
                {
                    "event_id": event.event_id,
                    "parent_id": event.parent_id,
                    "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                    "event_type": event.event_type,
                    "duration_ms": event.duration_ms,
                    "data": event.data
                }
                for event in trace.events
            ]
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def _analyze_trace(self, trace: ExecutionTrace) -> Dict[str, Any]:
        """Analyze trace for insights"""
        if not trace.events:
            return {}

        # Event type distribution
        event_types = {}
        total_tool_time = 0
        total_llm_time = 0
        errors = []

        for event in trace.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

            if event.duration_ms:
                if event.event_type == "tool_call":
                    total_tool_time += event.duration_ms
                elif event.event_type == "llm_call":
                    total_llm_time += event.duration_ms

            if event.event_type == "error":
                errors.append({
                    "timestamp": event.timestamp,
                    "error": event.data.get("error", "Unknown error")
                })

        # Performance metrics
        durations = [e.duration_ms for e in trace.events if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        # Tool usage analysis
        tool_usage = {}
        for event in trace.events:
            if event.event_type == "tool_call" and "tool_name" in event.data:
                tool_name = event.data["tool_name"]
                if tool_name not in tool_usage:
                    tool_usage[tool_name] = {"count": 0, "total_time": 0}
                tool_usage[tool_name]["count"] += 1
                if event.duration_ms:
                    tool_usage[tool_name]["total_time"] += event.duration_ms

        return {
            "event_distribution": event_types,
            "performance": {
                "avg_event_duration_ms": avg_duration,
                "max_event_duration_ms": max_duration,
                "total_tool_time_ms": total_tool_time,
                "total_llm_time_ms": total_llm_time
            },
            "tool_usage": tool_usage,
            "errors": errors,
            "insights": self._generate_insights(trace, event_types, tool_usage)
        }

    def _generate_insights(self, trace: ExecutionTrace, event_types: Dict, tool_usage: Dict) -> List[str]:
        """Generate insights from trace analysis"""
        insights = []

        # Performance insights
        if trace.total_duration_ms and trace.total_duration_ms > 10000:
            insights.append(f"Long execution time: {trace.total_duration_ms:.0f}ms")

        # Tool usage insights
        if tool_usage:
            most_used_tool = max(tool_usage.items(), key=lambda x: x[1]["count"])
            insights.append(f"Most used tool: {most_used_tool[0]} ({most_used_tool[1]['count']} times)")

            # Check for repeated tool calls
            for tool, stats in tool_usage.items():
                if stats["count"] > 5:
                    insights.append(f"Frequent {tool} usage: {stats['count']} calls")

        # Error insights
        error_count = event_types.get("error", 0)
        if error_count > 0:
            insights.append(f"Execution had {error_count} error(s)")

        # Efficiency insights
        total_events = len(trace.events)
        if total_events > 20:
            insights.append(f"Complex execution with {total_events} events")

        return insights

    def save_visualization(self, trace: ExecutionTrace, output_dir: str = "./visualizations"):
        """
        Save all visualization formats for a trace

        Args:
            trace: Trace to visualize
            output_dir: Directory to save visualizations
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        trace_name = f"{trace.agent_id}_{trace.trace_id[:8]}"

        # Save Mermaid diagram
        mermaid_content = self.generate_mermaid_diagram(trace)
        with open(output_path / f"{trace_name}.mermaid", 'w') as f:
            f.write(mermaid_content)

        # Save HTML timeline
        html_content = self.generate_timeline_html(trace)
        with open(output_path / f"{trace_name}.html", 'w') as f:
            f.write(html_content)

        # Save JSON report
        json_content = self.generate_json_report(trace)
        with open(output_path / f"{trace_name}.json", 'w') as f:
            f.write(json_content)

        logger.info(f"Visualizations saved to {output_path}")

    def compare_traces(self, traces: List[ExecutionTrace]) -> str:
        """
        Generate comparison report for multiple traces

        Args:
            traces: List of traces to compare

        Returns:
            Comparison report as HTML
        """
        if not traces:
            return "<p>No traces to compare</p>"

        comparison_data = []
        for trace in traces:
            analysis = self._analyze_trace(trace)
            comparison_data.append({
                "trace": trace,
                "analysis": analysis
            })

        # Generate comparison HTML
        html = ["<h2>Trace Comparison</h2>", "<table border='1' style='border-collapse: collapse;'>"]
        html.append("<tr><th>Agent</th><th>Duration (ms)</th><th>Events</th><th>Tool Calls</th><th>Errors</th></tr>")

        for data in comparison_data:
            trace = data["trace"]
            analysis = data["analysis"]

            html.append(f"""
            <tr>
                <td>{trace.agent_id}</td>
                <td>{trace.total_duration_ms or 0:.0f}</td>
                <td>{len(trace.events)}</td>
                <td>{analysis['event_distribution'].get('tool_call', 0)}</td>
                <td>{analysis['event_distribution'].get('error', 0)}</td>
            </tr>
            """)

        html.append("</table>")

        return "".join(html)