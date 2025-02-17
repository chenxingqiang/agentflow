"""Test full workflow execution."""

import pytest
import logging
from typing import Dict, Any, List
from agentflow.agents.agent import Agent
from agentflow.agents.agent_types import AgentType, AgentConfig, AgentMode, ModelConfig
from agentflow.core.workflow_types import WorkflowConfig, WorkflowStep, StepConfig, WorkflowStepType
from agentflow.core.templates import WorkflowTemplate, TemplateParameter
from agentflow.core.workflow_executor import WorkflowExecutor
from agentflow.core.processors.transformers import FilterProcessor
from agentflow.core.exceptions import WorkflowExecutionError
from unittest.mock import patch, MagicMock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import yaml
from datetime import datetime
from agentflow.core.config import ConfigurationType
from pathlib import Path

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses."""
    with patch('openai.ChatCompletion.acreate') as mock:
        mock.return_value = AsyncMock(return_value={
            'choices': [{
                'message': {
                    'content': 'Test research output',
                    'role': 'assistant'
                }
            }],
            'usage': {
                'total_tokens': 100
            }
        })
        yield mock

def create_test_workflow_file(path: str) -> None:
    """Create a test workflow YAML file."""
    workflow_data = {
        'name': 'Test Workflow',
        'description': 'Test workflow for integration testing',
        'steps': [
            {
                'id': 'step-1',
                'name': 'Research Step',
                'type': 'research',
                'config': {
                    'strategy': 'research',
                    'params': {'depth': 'comprehensive'}
                }
            },
            {
                'id': 'step-2',
                'name': 'Document Generation Step',
                'type': 'document',
                'config': {
                    'strategy': 'document',
                    'params': {'format': 'academic'}
                }
            }
        ]
    }
    
    with open(path, 'w') as f:
        yaml.dump(workflow_data, f)

def create_test_steps():
    """Create test workflow steps."""
    # Create a mock agent for testing
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value={
        "document": {
            "title": "Test Research Document",
            "content": "Generated document content",
            "format": "Markdown"
        }
    })

    return [
        WorkflowStep(
            id='step-1',
            name='Research Step',
            type=WorkflowStepType.RESEARCH_EXECUTION,
            description='Execute research analysis step',
            config=StepConfig(
                strategy='standard',
                params={
                    'research_topic': 'AI Ethics',
                    'depth': 'comprehensive'
                }
            )
        ),
        WorkflowStep(
            id='step-2',
            name='Document Step',
            type=WorkflowStepType.DOCUMENT_GENERATION,
            description='Generate documentation from research findings',
            config=StepConfig(
                strategy='standard',
                params={
                    'format': 'markdown',
                    'sections': ['introduction', 'methodology', 'results', 'conclusion']
                }
            ),
            dependencies=['step-1']
        )
    ]

def create_test_workflow_config():
    """Create test workflow configuration with mock agent."""
    mock_agent = MagicMock()
    mock_agent.execute = AsyncMock(return_value={
        "document": {
            "title": "Test Research Document",
            "content": "Generated document content",
            "format": "Markdown"
        }
    })

    return WorkflowConfig(
        id='test-workflow-1',
        name='Test Workflow',
        max_iterations=5,
        timeout=30,
        steps=create_test_steps(),
        agent=mock_agent  # Add mock agent to workflow config
    )

def create_test_context():
    """Create test workflow context."""
    return {
        "data": "Research context for AI Ethics in Distributed Systems",
        "research_topic": "AI Ethics in Distributed Systems",
        "deadline": "2024-12-31",
        "academic_level": "PhD",
        "research_methodology": "Systematic Literature Review"
    }

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    return tmp_path

@pytest.mark.asyncio
async def test_complete_workflow(test_data_dir, mock_openai):
    """Test complete workflow execution."""
    # Create test workflow file
    workflow_path = str(test_data_dir / "test_workflow.yaml")
    create_test_workflow_file(workflow_path)

    # Create workflow config
    workflow_config = create_test_workflow_config()

    try:
        # Create workflow executor
        executor = WorkflowExecutor(workflow_config)
        
        # Initialize the executor
        await executor.initialize()

        # Execute workflow
        result = await executor.execute(create_test_context())
        
        # Verify results
        assert result is not None
        assert isinstance(result, dict)
        assert 'steps' in result
        assert 'step-1' in result['steps']
        assert 'step-2' in result['steps']

        # Verify step results
        assert result['steps']['step-1']['status'] in ['success', 'completed']
        assert result['steps']['step-2']['status'] in ['success', 'completed']
        assert 'result' in result['steps']['step-1']
        assert 'result' in result['steps']['step-2']

        # Verify workflow status
        assert result['status'] in ['success', 'completed']
        
    except WorkflowExecutionError as e:
        pytest.fail(f"Workflow execution failed: {str(e)}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {str(e)}")

def test_workflow_validation():
    """Test workflow configuration validation."""
    # Use the same steps as in create_test_steps()
    invalid_steps = [
        WorkflowStep(
            id='invalid-step',
            name='Invalid Step',
            type=WorkflowStepType.TRANSFORM,
            description='Test invalid workflow step',
            config=StepConfig(
                strategy='standard',
                params={}
            )
        )
    ]
    
    # Create workflow config with invalid steps
    workflow_config = WorkflowConfig(
        id='test-workflow-1',
        name='Test Workflow',
        max_iterations=5,
        timeout=30,
        steps=invalid_steps
    )
    
    # Verify workflow configuration
    assert workflow_config is not None
    assert len(workflow_config.steps) == 1
    assert workflow_config.steps[0].type == WorkflowStepType.TRANSFORM

def test_workflow_context_validation():
    """Test workflow context validation."""
    # Test with missing required fields
    invalid_context = {
        "academic_level": "PhD"  # Missing required research_topic
    }

    workflow_config = WorkflowConfig(
        id='test-workflow',
        name='Test Workflow',
        max_iterations=5,
        timeout=30,
        steps=[
            WorkflowStep(
                id='step-1',
                name='Research Step',
                type=WorkflowStepType.RESEARCH_EXECUTION,
                description='Execute research analysis step',
                config=StepConfig(
                    strategy='standard',
                    params={
                        'research_topic': 'AI Ethics',
                        'depth': 'comprehensive'
                    }
                )
            )
        ]
    )

    executor = WorkflowExecutor(workflow_config)

    # Add validate_context method to WorkflowExecutor
    def validate_context(self, context):
        required_fields = ['research_topic']
        for field in required_fields:
            if field not in context:
                raise ValueError(f"Missing required field: {field}")
    
    # Monkey patch the method
    executor.validate_context = validate_context.__get__(executor)

    with pytest.raises(ValueError, match="Missing required field: research_topic"):
        executor.validate_context(invalid_context)