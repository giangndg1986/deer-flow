# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.prompts.planner_model import StepType
import logging
from .types import State
from .nodes import (
    coordinator_node,
    planner_node,
    reporter_node,
    research_team_node,
    researcher_node,
    coder_node,
    human_feedback_node,
    background_investigation_node,
)

logger = logging.getLogger(__name__)

def continue_to_running_research_team(state: State):
    logger.info("=== ROUTING DEBUG START ===")
    current_plan = state.get("current_plan")

    if not current_plan or not current_plan.steps:
        logger.info("No current plan or steps found, routing to planner")
        return "planner"

    # Check if all steps are completed
    if all(step.execution_res for step in current_plan.steps):
        logger.info("All steps completed, routing to planner")
        return "planner"

    # Find the first unexecuted step
    current_step = None
    for i, step in enumerate(current_plan.steps):
        if not step.execution_res:
            current_step = step
            logger.info(f"Found unexecuted step {i+1}: {step.title}")
            logger.info(f"Step type: {step.step_type}")
            logger.info(f"Step description: {step.description}")
            break

    if not current_step:
        logger.info("No unexecuted step found, routing to planner")
        return "planner"

    # Route based on step type - FIX: use current_step instead of step
    if current_step.step_type and current_step.step_type == StepType.RESEARCH:
        logger.info("Routing to researcher")
        return "researcher"
    elif current_step.step_type and current_step.step_type == StepType.PROCESSING:
        logger.info("Routing to coder (processing)")
        return "coder"
    elif current_step.step_type and current_step.step_type == StepType.CODE_GENERATION:
        logger.info("Routing to coder (code generation)")
        return "coder"
    else:
        logger.warning(f"Unknown step type: {current_step.step_type}, routing to planner")
        return "planner"


def _build_base_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("research_team", research_team_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("coder", coder_node)
    builder.add_node("human_feedback", human_feedback_node)
    builder.add_edge("background_investigator", "planner")
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "coder"],
    )
    # builder.add_edge("reporter", END)
    return builder


def build_graph_with_memory():
    """Build and return the agent workflow graph with memory."""
    # use persistent memory to save conversation history
    # TODO: be compatible with SQLite / PostgreSQL
    memory = MemorySaver()

    # build state graph
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile()


graph = build_graph()
