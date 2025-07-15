"""Data models for Plan-MCP."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# Project Planning Models
class Task(BaseModel):
    """A single task in a project plan."""
    id: str = Field(description="Unique task identifier")
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed task description")
    priority: Literal["high", "medium", "low"] = Field(description="Task priority")
    estimated_effort: Optional[str] = Field(None, description="Estimated time/effort")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Success criteria")


class Phase(BaseModel):
    """A phase in the project plan."""
    name: str = Field(description="Phase name")
    description: str = Field(description="Phase description")
    tasks: List[Task] = Field(description="Tasks in this phase")
    milestone: Optional[str] = Field(None, description="Key milestone for this phase")


class ProjectPlan(BaseModel):
    """Complete project plan."""
    project_name: str = Field(description="Project name")
    overview: str = Field(description="Project overview")
    phases: List[Phase] = Field(description="Project phases")
    estimated_duration: Optional[str] = Field(None, description="Total estimated duration")
    key_risks: List[str] = Field(default_factory=list, description="Key project risks")
    tech_requirements: List[str] = Field(default_factory=list, description="Technical requirements")


# Code Review Models
class CodeIssue(BaseModel):
    """An issue found during code review."""
    severity: Literal["critical", "major", "minor", "info"] = Field(description="Issue severity")
    type: str = Field(description="Issue type (e.g., bug, security, performance)")
    message: str = Field(description="Issue description")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class CodeSuggestion(BaseModel):
    """A suggestion for code improvement."""
    type: Literal["performance", "readability", "security", "best-practice", "refactoring"] = Field(
        description="Suggestion type"
    )
    message: str = Field(description="Suggestion description")
    example_code: Optional[str] = Field(None, description="Example implementation")
    impact: Literal["high", "medium", "low"] = Field(default="medium", description="Impact level")


class CodeReview(BaseModel):
    """Complete code review result."""
    summary: str = Field(description="Review summary")
    overall_quality: Literal["excellent", "good", "fair", "needs-improvement"] = Field(
        description="Overall code quality"
    )
    issues: List[CodeIssue] = Field(default_factory=list, description="Found issues")
    suggestions: List[CodeSuggestion] = Field(default_factory=list, description="Improvement suggestions")
    strengths: List[str] = Field(default_factory=list, description="Code strengths")
    test_coverage_assessment: Optional[str] = Field(None, description="Test coverage assessment")


# Execution Analysis Models
class ExecutionIssue(BaseModel):
    """An issue found during execution analysis."""
    type: str = Field(description="Issue type")
    description: str = Field(description="Issue description")
    likely_cause: str = Field(description="Likely cause of the issue")


class CodeFix(BaseModel):
    """A suggested code fix."""
    description: str = Field(description="Fix description")
    code_snippet: str = Field(description="Code to fix the issue")
    explanation: str = Field(description="Why this fix works")
    confidence: Literal["high", "medium", "low"] = Field(description="Confidence in this fix")


class ExecutionAnalysis(BaseModel):
    """Analysis of code execution results."""
    success: bool = Field(description="Whether execution was successful")
    summary: str = Field(description="Analysis summary")
    issues: List[ExecutionIssue] = Field(default_factory=list, description="Found issues")
    suggested_fixes: List[CodeFix] = Field(default_factory=list, description="Suggested fixes")
    next_steps: List[str] = Field(description="Recommended next steps")
    performance_notes: Optional[str] = Field(None, description="Performance observations")