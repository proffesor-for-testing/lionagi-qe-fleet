#!/usr/bin/env python3
"""
Q-Learning Inspector Tool

Provides observability into Q-learning across the 18-agent fleet:
- View current Q-values for an agent
- Show learning progress over time
- Display top-performing state-action pairs
- Export learning data for analysis
- Monitor fleet-wide learning metrics

Usage:
    # View agent Q-values
    python qlearning_inspector.py show-qvalues test-generator --limit 20

    # Show learning progress
    python qlearning_inspector.py progress test-generator --hours 24

    # Display top state-action pairs
    python qlearning_inspector.py top-actions test-generator --top 10

    # Export learning data
    python qlearning_inspector.py export test-generator --output learning_data.json

    # Fleet-wide metrics
    python qlearning_inspector.py fleet-status --all-agents

    # Compare agents
    python qlearning_inspector.py compare test-generator coverage-analyzer
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

import asyncpg
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich import box


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lionagi_qe.learning import DatabaseManager


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_DATABASE_URL = os.environ.get(
    "QLEARNING_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/qlearning"
)

console = Console()


# ============================================================================
# Inspector Class
# ============================================================================

class QLearningInspector:
    """Inspector for Q-learning data"""

    def __init__(self, database_url: str = DEFAULT_DATABASE_URL):
        """Initialize inspector

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.db_manager = DatabaseManager(database_url)

    async def connect(self):
        """Connect to database"""
        await self.db_manager.connect()

    async def disconnect(self):
        """Disconnect from database"""
        await self.db_manager.disconnect()

    async def show_q_values(
        self,
        agent_type: str,
        limit: int = 20,
        state_hash: Optional[str] = None
    ):
        """Show Q-values for an agent

        Args:
            agent_type: Agent type to inspect
            limit: Maximum number of Q-values to show
            state_hash: Optional state hash to filter by
        """
        console.print(f"\n[bold cyan]Q-Values for {agent_type}[/bold cyan]\n")

        async with self.db_manager.pool.acquire() as conn:
            if state_hash:
                query = """
                    SELECT
                        state_hash, action_hash, q_value,
                        visit_count, confidence_score,
                        last_updated
                    FROM q_values
                    WHERE agent_type = $1 AND state_hash = $2
                    ORDER BY q_value DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, agent_type, state_hash, limit)
            else:
                query = """
                    SELECT
                        state_hash, action_hash, q_value,
                        visit_count, confidence_score,
                        last_updated
                    FROM q_values
                    WHERE agent_type = $1
                    ORDER BY q_value DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, agent_type, limit)

            if not rows:
                console.print(f"[yellow]No Q-values found for {agent_type}[/yellow]")
                return

            # Create table
            table = Table(
                title=f"Top {len(rows)} Q-Values",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("State Hash", style="cyan", no_wrap=True)
            table.add_column("Action Hash", style="green", no_wrap=True)
            table.add_column("Q-Value", style="yellow", justify="right")
            table.add_column("Visits", style="blue", justify="right")
            table.add_column("Confidence", style="magenta", justify="right")
            table.add_column("Last Updated", style="white")

            for row in rows:
                table.add_row(
                    row['state_hash'][:16] + "...",
                    row['action_hash'][:16] + "...",
                    f"{row['q_value']:.4f}",
                    str(row['visit_count']),
                    f"{row['confidence_score']:.2f}",
                    row['last_updated'].strftime("%Y-%m-%d %H:%M:%S")
                )

            console.print(table)

            # Show summary statistics
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"  Total Q-values shown: {len(rows)}")
            console.print(f"  Highest Q-value: {rows[0]['q_value']:.4f}")
            console.print(f"  Lowest Q-value: {rows[-1]['q_value']:.4f}")
            avg_visits = sum(r['visit_count'] for r in rows) / len(rows)
            console.print(f"  Average visits: {avg_visits:.1f}")

    async def show_progress(
        self,
        agent_type: str,
        hours: int = 24
    ):
        """Show learning progress over time

        Args:
            agent_type: Agent type to inspect
            hours: Number of hours to look back
        """
        console.print(f"\n[bold cyan]Learning Progress for {agent_type}[/bold cyan]")
        console.print(f"[dim]Last {hours} hours[/dim]\n")

        # Get learning statistics
        stats = await self.db_manager.get_learning_statistics(agent_type, hours)

        if not stats:
            console.print(f"[yellow]No learning statistics found for {agent_type} in last {hours} hours[/yellow]")
            return

        # Create table
        table = Table(
            title=f"Learning Statistics (Last {hours}h)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("Time Window", style="cyan")
        table.add_column("Episodes", style="yellow", justify="right")
        table.add_column("Avg Reward", style="green", justify="right")
        table.add_column("Std Reward", style="blue", justify="right")
        table.add_column("Success Rate", style="magenta", justify="right")
        table.add_column("Exploration Rate", style="white", justify="right")

        for stat in stats:
            window_start = datetime.fromisoformat(stat['window_start'])
            window_str = window_start.strftime("%m-%d %H:%M")

            table.add_row(
                window_str,
                str(stat['episodes_completed']),
                f"{stat['avg_episode_reward']:.2f}",
                f"{stat['std_episode_reward']:.2f}",
                f"{stat['success_rate']:.2%}",
                f"{stat['exploration_rate']:.3f}"
            )

        console.print(table)

        # Show trend
        if len(stats) >= 2:
            first_reward = stats[-1]['avg_episode_reward']
            last_reward = stats[0]['avg_episode_reward']
            trend = ((last_reward - first_reward) / abs(first_reward)) * 100 if first_reward != 0 else 0

            console.print(f"\n[bold]Trend:[/bold]")
            if trend > 5:
                console.print(f"  [green]↑ Reward improving by {trend:.1f}%[/green]")
            elif trend < -5:
                console.print(f"  [red]↓ Reward declining by {abs(trend):.1f}%[/red]")
            else:
                console.print(f"  [yellow]→ Reward stable (±{abs(trend):.1f}%)[/yellow]")

    async def show_top_actions(
        self,
        agent_type: str,
        top: int = 10
    ):
        """Show top-performing state-action pairs

        Args:
            agent_type: Agent type to inspect
            top: Number of top pairs to show
        """
        console.print(f"\n[bold cyan]Top {top} State-Action Pairs for {agent_type}[/bold cyan]\n")

        async with self.db_manager.pool.acquire() as conn:
            query = """
                SELECT
                    state_hash,
                    state_data,
                    action_hash,
                    action_data,
                    q_value,
                    visit_count,
                    confidence_score
                FROM q_values
                WHERE agent_type = $1
                ORDER BY q_value DESC, visit_count DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, agent_type, top)

            if not rows:
                console.print(f"[yellow]No Q-values found for {agent_type}[/yellow]")
                return

            # Display as tree structure
            tree = Tree(f"[bold]{agent_type}[/bold] Top Actions")

            for i, row in enumerate(rows, 1):
                state_data = json.loads(row['state_data'])
                action_data = json.loads(row['action_data'])

                # Create branch for this state-action pair
                branch = tree.add(
                    f"[bold yellow]#{i}[/bold yellow] "
                    f"Q-value: [green]{row['q_value']:.4f}[/green] "
                    f"(Visits: {row['visit_count']}, "
                    f"Confidence: {row['confidence_score']:.2f})"
                )

                # Add state details
                state_branch = branch.add("[cyan]State[/cyan]")
                for key, value in state_data.get('features', {}).items():
                    state_branch.add(f"{key}: {value}")

                # Add action details
                action_branch = branch.add("[green]Action[/green]")
                for key, value in action_data.items():
                    action_branch.add(f"{key}: {value}")

            console.print(tree)

    async def export_learning_data(
        self,
        agent_type: str,
        output_file: str
    ):
        """Export learning data to JSON

        Args:
            agent_type: Agent type to export
            output_file: Output file path
        """
        console.print(f"\n[bold cyan]Exporting learning data for {agent_type}[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching data...", total=None)

            async with self.db_manager.pool.acquire() as conn:
                # Get Q-values
                progress.update(task, description="Fetching Q-values...")
                q_values = await conn.fetch(
                    """
                    SELECT
                        state_hash, state_data, action_hash, action_data,
                        q_value, visit_count, confidence_score, last_updated
                    FROM q_values
                    WHERE agent_type = $1
                    ORDER BY q_value DESC
                    """,
                    agent_type
                )

                # Get trajectories
                progress.update(task, description="Fetching trajectories...")
                trajectories = await self.db_manager.get_recent_trajectories(
                    agent_type,
                    limit=1000
                )

                # Get agent states
                progress.update(task, description="Fetching agent states...")
                agent_states = await conn.fetch(
                    """
                    SELECT
                        agent_instance_id, total_tasks, successful_tasks,
                        failed_tasks, total_reward, avg_reward,
                        current_exploration_rate, patterns_learned, status
                    FROM agent_states
                    WHERE agent_type = $1
                    """,
                    agent_type
                )

                progress.update(task, description="Writing to file...")

                # Compile export data
                export_data = {
                    "agent_type": agent_type,
                    "exported_at": datetime.now().isoformat(),
                    "q_values": [
                        {
                            "state_hash": row['state_hash'],
                            "state_data": json.loads(row['state_data']),
                            "action_hash": row['action_hash'],
                            "action_data": json.loads(row['action_data']),
                            "q_value": float(row['q_value']),
                            "visit_count": row['visit_count'],
                            "confidence_score": float(row['confidence_score']),
                            "last_updated": row['last_updated'].isoformat()
                        }
                        for row in q_values
                    ],
                    "trajectories": trajectories,
                    "agent_states": [
                        {
                            "agent_instance_id": row['agent_instance_id'],
                            "total_tasks": row['total_tasks'],
                            "successful_tasks": row['successful_tasks'],
                            "failed_tasks": row['failed_tasks'],
                            "total_reward": float(row['total_reward']),
                            "avg_reward": float(row['avg_reward']),
                            "current_exploration_rate": float(row['current_exploration_rate']),
                            "patterns_learned": row['patterns_learned'],
                            "status": row['status']
                        }
                        for row in agent_states
                    ],
                    "summary": {
                        "total_q_values": len(q_values),
                        "total_trajectories": len(trajectories),
                        "total_agent_instances": len(agent_states),
                        "highest_q_value": max((float(r['q_value']) for r in q_values), default=0.0),
                        "total_visits": sum((r['visit_count'] for r in q_values), 0)
                    }
                }

                # Write to file
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)

        console.print(f"\n[green]✓ Exported {len(q_values)} Q-values and {len(trajectories)} trajectories to {output_file}[/green]")

    async def show_fleet_status(self, all_agents: bool = True):
        """Show fleet-wide learning metrics

        Args:
            all_agents: Show all agents or only active ones
        """
        console.print("\n[bold cyan]Fleet-Wide Learning Status[/bold cyan]\n")

        async with self.db_manager.pool.acquire() as conn:
            # Get fleet metrics from materialized view
            query = """
                SELECT
                    agent_type, display_name,
                    total_sessions, total_trajectories,
                    successful_trajectories, avg_reward,
                    cumulative_reward, avg_execution_time_ms,
                    unique_patterns, active_instances, last_active
                FROM agent_performance_summary
                ORDER BY cumulative_reward DESC
            """
            rows = await conn.fetch(query)

            if not rows:
                console.print("[yellow]No fleet data available[/yellow]")
                return

            # Create summary table
            table = Table(
                title="Fleet Learning Metrics",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("Agent", style="cyan")
            table.add_column("Instances", justify="right", style="blue")
            table.add_column("Trajectories", justify="right", style="yellow")
            table.add_column("Success Rate", justify="right", style="green")
            table.add_column("Avg Reward", justify="right", style="magenta")
            table.add_column("Total Reward", justify="right", style="white")
            table.add_column("Patterns", justify="right", style="cyan")
            table.add_column("Last Active", style="dim")

            total_trajectories = 0
            total_reward = 0.0
            total_patterns = 0

            for row in rows:
                if row['total_trajectories'] == 0 and not all_agents:
                    continue

                success_rate = (
                    row['successful_trajectories'] / row['total_trajectories']
                    if row['total_trajectories'] > 0
                    else 0.0
                )

                last_active = row['last_active'].strftime("%m-%d %H:%M") if row['last_active'] else "Never"

                table.add_row(
                    row['agent_type'],
                    str(row['active_instances'] or 0),
                    str(row['total_trajectories'] or 0),
                    f"{success_rate:.1%}",
                    f"{row['avg_reward'] or 0:.2f}",
                    f"{row['cumulative_reward'] or 0:.1f}",
                    str(row['unique_patterns'] or 0),
                    last_active
                )

                total_trajectories += row['total_trajectories'] or 0
                total_reward += row['cumulative_reward'] or 0
                total_patterns += row['unique_patterns'] or 0

            console.print(table)

            # Fleet summary
            panel = Panel(
                f"[bold]Total Trajectories:[/bold] {total_trajectories:,}\n"
                f"[bold]Total Reward:[/bold] {total_reward:,.1f}\n"
                f"[bold]Total Patterns:[/bold] {total_patterns}\n"
                f"[bold]Active Agents:[/bold] {len(rows)}",
                title="Fleet Summary",
                border_style="green"
            )
            console.print("\n", panel)

    async def compare_agents(self, agent1: str, agent2: str):
        """Compare learning metrics between two agents

        Args:
            agent1: First agent type
            agent2: Second agent type
        """
        console.print(f"\n[bold cyan]Comparing {agent1} vs {agent2}[/bold cyan]\n")

        async with self.db_manager.pool.acquire() as conn:
            query = """
                SELECT
                    agent_type,
                    COUNT(*) as q_value_count,
                    AVG(q_value) as avg_q_value,
                    MAX(q_value) as max_q_value,
                    SUM(visit_count) as total_visits,
                    AVG(visit_count) as avg_visits,
                    AVG(confidence_score) as avg_confidence
                FROM q_values
                WHERE agent_type IN ($1, $2)
                GROUP BY agent_type
            """
            rows = await conn.fetch(query, agent1, agent2)

            if len(rows) < 2:
                console.print(f"[yellow]Insufficient data to compare agents[/yellow]")
                return

            # Create comparison table
            table = Table(
                title="Agent Comparison",
                box=box.DOUBLE,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("Metric", style="cyan")
            table.add_column(agent1, justify="right", style="green")
            table.add_column(agent2, justify="right", style="yellow")
            table.add_column("Winner", style="bold")

            metrics = {
                "Q-Values": ("q_value_count", "higher"),
                "Avg Q-Value": ("avg_q_value", "higher"),
                "Max Q-Value": ("max_q_value", "higher"),
                "Total Visits": ("total_visits", "higher"),
                "Avg Visits": ("avg_visits", "higher"),
                "Avg Confidence": ("avg_confidence", "higher"),
            }

            data1 = {row['agent_type']: row for row in rows}[agent1]
            data2 = {row['agent_type']: row for row in rows}[agent2]

            for metric_name, (field, direction) in metrics.items():
                val1 = data1[field]
                val2 = data2[field]

                # Format values
                if isinstance(val1, float):
                    val1_str = f"{val1:.4f}"
                    val2_str = f"{val2:.4f}"
                else:
                    val1_str = str(val1)
                    val2_str = str(val2)

                # Determine winner
                if val1 > val2:
                    winner = f"[green]{agent1}[/green]"
                elif val2 > val1:
                    winner = f"[yellow]{agent2}[/yellow]"
                else:
                    winner = "[dim]Tie[/dim]"

                table.add_row(metric_name, val1_str, val2_str, winner)

            console.print(table)


# ============================================================================
# CLI
# ============================================================================

async def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Q-Learning Inspector Tool for Agentic QE Fleet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s show-qvalues test-generator --limit 20
  %(prog)s progress test-generator --hours 24
  %(prog)s top-actions test-generator --top 10
  %(prog)s export test-generator --output data.json
  %(prog)s fleet-status --all-agents
  %(prog)s compare test-generator coverage-analyzer
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # show-qvalues command
    qvalues_parser = subparsers.add_parser("show-qvalues", help="Show Q-values for an agent")
    qvalues_parser.add_argument("agent_type", help="Agent type to inspect")
    qvalues_parser.add_argument("--limit", type=int, default=20, help="Number of Q-values to show")
    qvalues_parser.add_argument("--state", help="Filter by state hash")

    # progress command
    progress_parser = subparsers.add_parser("progress", help="Show learning progress")
    progress_parser.add_argument("agent_type", help="Agent type to inspect")
    progress_parser.add_argument("--hours", type=int, default=24, help="Hours to look back")

    # top-actions command
    top_parser = subparsers.add_parser("top-actions", help="Show top-performing actions")
    top_parser.add_argument("agent_type", help="Agent type to inspect")
    top_parser.add_argument("--top", type=int, default=10, help="Number of top pairs to show")

    # export command
    export_parser = subparsers.add_parser("export", help="Export learning data")
    export_parser.add_argument("agent_type", help="Agent type to export")
    export_parser.add_argument("--output", required=True, help="Output JSON file")

    # fleet-status command
    fleet_parser = subparsers.add_parser("fleet-status", help="Show fleet-wide metrics")
    fleet_parser.add_argument("--all-agents", action="store_true", help="Show all agents including inactive")

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two agents")
    compare_parser.add_argument("agent1", help="First agent type")
    compare_parser.add_argument("agent2", help="Second agent type")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create inspector
    inspector = QLearningInspector()

    try:
        await inspector.connect()

        # Execute command
        if args.command == "show-qvalues":
            await inspector.show_q_values(
                args.agent_type,
                limit=args.limit,
                state_hash=args.state
            )
        elif args.command == "progress":
            await inspector.show_progress(args.agent_type, hours=args.hours)
        elif args.command == "top-actions":
            await inspector.show_top_actions(args.agent_type, top=args.top)
        elif args.command == "export":
            await inspector.export_learning_data(args.agent_type, args.output)
        elif args.command == "fleet-status":
            await inspector.show_fleet_status(all_agents=args.all_agents)
        elif args.command == "compare":
            await inspector.compare_agents(args.agent1, args.agent2)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await inspector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
