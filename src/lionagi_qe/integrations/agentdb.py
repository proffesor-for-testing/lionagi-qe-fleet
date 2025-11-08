"""
AgentDB Integration for LionAGI QE Fleet

Stores test execution episodes in AgentDB for continuous learning and pattern discovery.
Enables retrieval of similar past test scenarios to improve future test generation.

Usage:
    from lionagi_qe.integrations.agentdb import AgentDBIntegration
    
    agentdb = AgentDBIntegration(namespace="qe/")
    await agentdb.store_test_run(agent_id, task, result)
    similar = await agentdb.retrieve_similar_tests(task, k=5)
"""

import asyncio
import subprocess
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestEpisode:
    """Represents a test execution episode"""
    session_id: str
    agent_id: str
    task_type: str
    success: bool
    reward: float
    critique: Optional[str]
    context: Dict[str, Any]
    output: Any
    latency_ms: int
    tokens: int
    timestamp: float


class AgentDBIntegration:
    """
    Integrates LionAGI QE Fleet with AgentDB for reflexion-based learning.
    
    This enables:
    - Storing test execution results as episodes
    - Retrieving similar past test scenarios
    - Learning from successful and failed test patterns
    - Building skill library from repeated successful patterns
    """
    
    def __init__(
        self,
        namespace: str = "qe/",
        db_path: Optional[str] = None,
        enable_learning: bool = True
    ):
        """
        Initialize AgentDB integration.
        
        Args:
            namespace: Memory namespace for QE episodes (default: "qe/")
            db_path: Path to AgentDB database (default: .data/agentdb-test.db)
            enable_learning: Enable automatic skill consolidation
        """
        self.namespace = namespace
        self.db_path = db_path or str(Path.cwd() / ".data" / "agentdb-test.db")
        self.enable_learning = enable_learning
        
    async def store_test_run(
        self,
        agent_id: str,
        task: Any,  # QETask from lionagi_qe
        result: Any,  # Result object
        critique: Optional[str] = None
    ) -> bool:
        """
        Store a test execution as an AgentDB episode.
        
        Args:
            agent_id: ID of the agent that executed the test
            task: QETask object with test context
            result: Test execution result
            critique: Optional self-critique or lessons learned
            
        Returns:
            bool: True if stored successfully
            
        Example:
            success = await agentdb.store_test_run(
                agent_id="test-generator",
                task=test_task,
                result=test_result,
                critique="Tests covered edge cases but missed error handling"
            )
        """
        session_id = f"{self.namespace}{agent_id}-{int(time.time())}"
        reward = 1.0 if result.success else 0.0
        
        # Extract metadata
        task_desc = f"{agent_id}: {task.task_type}"
        if hasattr(task, "context"):
            task_desc += f" ({task.context.get('framework', 'unknown')})"
        
        # Build command
        cmd = [
            "npx", "agentdb", "reflexion", "store",
            session_id,
            task_desc,
            str(reward),
            str(result.success).lower(),
            critique or result.get("critique", "No critique provided"),
            json.dumps(task.context if hasattr(task, "context") else {}),
            json.dumps(str(result.output) if hasattr(result, "output") else ""),
            str(getattr(result, "latency_ms", 0)),
            str(getattr(result, "tokens", 0))
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"✅ Stored episode: {session_id}")
                return True
            else:
                print(f"❌ Failed to store episode: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error storing episode: {e}")
            return False
    
    async def retrieve_similar_tests(
        self,
        task: Any,
        k: int = 5,
        min_reward: float = 0.7,
        only_successes: bool = False
    ) -> List[Dict]:
        """
        Retrieve similar past test executions from AgentDB.
        
        Args:
            task: Current QETask to find similar tests for
            k: Number of similar episodes to retrieve
            min_reward: Minimum reward threshold (0.0-1.0)
            only_successes: Only return successful test episodes
            
        Returns:
            List of similar test episodes with context and results
            
        Example:
            similar = await agentdb.retrieve_similar_tests(
                task=current_task,
                k=10,
                min_reward=0.8,
                only_successes=True
            )
        """
        task_type = task.task_type if hasattr(task, "task_type") else "unknown"
        query = f"{task_type} test execution"
        
        cmd = [
            "npx", "agentdb", "reflexion", "retrieve",
            query,
            "--k", str(k),
            "--min-reward", str(min_reward)
        ]
        
        if only_successes:
            cmd.append("--only-successes")
        
        cmd.append("--synthesize-context")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parse JSON output
                output = stdout.decode()
                # Extract JSON from output (may have other text)
                import re
                json_match = re.search(r'\[.*\]', output, re.DOTALL)
                if json_match:
                    episodes = json.loads(json_match.group())
                    print(f"✅ Retrieved {len(episodes)} similar episodes")
                    return episodes
                else:
                    print(f"⚠️  No episodes found for: {query}")
                    return []
            else:
                print(f"❌ Failed to retrieve episodes: {stderr.decode()}")
                return []
                
        except Exception as e:
            print(f"❌ Error retrieving episodes: {e}")
            return []
    
    async def consolidate_skills(
        self,
        min_attempts: int = 3,
        min_reward: float = 0.7,
        time_window_days: int = 7
    ) -> bool:
        """
        Consolidate successful test patterns into reusable skills.
        
        This analyzes recent test episodes and creates skills for patterns
        that have been successfully applied multiple times.
        
        Args:
            min_attempts: Minimum number of successful applications
            min_reward: Minimum average reward threshold
            time_window_days: Look back window in days
            
        Returns:
            bool: True if consolidation completed successfully
            
        Example:
            # Run skill consolidation weekly
            await agentdb.consolidate_skills(
                min_attempts=5,
                min_reward=0.8,
                time_window_days=7
            )
        """
        if not self.enable_learning:
            print("⚠️  Learning disabled, skipping skill consolidation")
            return False
        
        cmd = [
            "npx", "agentdb", "skill", "consolidate",
            str(min_attempts),
            str(min_reward),
            str(time_window_days),
            "true"  # extract-patterns
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"✅ Skill consolidation complete")
                print(stdout.decode())
                return True
            else:
                print(f"❌ Skill consolidation failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Error consolidating skills: {e}")
            return False
    
    async def search_skills(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Search for applicable skills in the skill library.
        
        Args:
            query: Search query describing the test scenario
            k: Number of skills to retrieve
            
        Returns:
            List of applicable skills with descriptions and code
            
        Example:
            skills = await agentdb.search_skills(
                query="pytest test generation for REST APIs",
                k=3
            )
        """
        cmd = [
            "npx", "agentdb", "skill", "search",
            query,
            str(k)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode()
                # Parse JSON output
                import re
                json_match = re.search(r'\[.*\]', output, re.DOTALL)
                if json_match:
                    skills = json.loads(json_match.group())
                    print(f"✅ Found {len(skills)} applicable skills")
                    return skills
                else:
                    print(f"⚠️  No skills found for: {query}")
                    return []
            else:
                print(f"❌ Failed to search skills: {stderr.decode()}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching skills: {e}")
            return []
    
    async def get_critique_summary(
        self,
        task_type: str,
        only_failures: bool = True
    ) -> str:
        """
        Get aggregated critique lessons for a specific task type.
        
        Useful for understanding common failure modes and how to avoid them.
        
        Args:
            task_type: Type of task (e.g., "generate_tests", "execute_tests")
            only_failures: Only include failed episodes
            
        Returns:
            str: Aggregated critique summary
            
        Example:
            critique = await agentdb.get_critique_summary(
                task_type="generate_tests",
                only_failures=True
            )
            print(f"Common failures:\\n{critique}")
        """
        cmd = [
            "npx", "agentdb", "reflexion", "critique-summary",
            task_type
        ]
        
        if only_failures:
            cmd.append("true")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode()
            else:
                print(f"❌ Failed to get critique summary: {stderr.decode()}")
                return ""
                
        except Exception as e:
            print(f"❌ Error getting critique summary: {e}")
            return ""


# Convenience function for quick integration
async def store_qe_episode(
    agent_id: str,
    task: Any,
    result: Any,
    critique: Optional[str] = None,
    db_path: Optional[str] = None
) -> bool:
    """
    Convenience function to store a QE episode without initializing class.
    
    Example:
        from lionagi_qe.integrations.agentdb import store_qe_episode
        
        await store_qe_episode(
            agent_id="test-generator",
            task=task,
            result=result,
            critique="Good coverage but slow execution"
        )
    """
    integration = AgentDBIntegration(db_path=db_path)
    return await integration.store_test_run(agent_id, task, result, critique)
