from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Optional, Dict, Any
from datetime import datetime
import os
import json
import logging
from .tools.student_profile_tool import StudentProfileTool
from .tools.college_search_tool import CollegeSearchTool
from .tools.essay_feedback_memory_tool import EssayFeedbackMemoryTool
from langchain_openai import ChatOpenAI
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.environ["OPENAI_API_KEY"] = "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"
llm = ChatOpenAI(model="gpt-4o")

@CrewBase
class EssayFeedbackCrew():
    """Essay Feedback and Analysis Crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, inputs: Optional[Dict[str, Any]] = None):
        """Initialize the Essay Feedback crew with required tools and inputs."""
        super().__init__()
        self.inputs = inputs or {}
        self.task_results = {}
        
        # Validate required inputs
        required_fields = ['college_name', 'prompt', 'essay_text', 'word_count', 'auth0_id']
        missing_fields = [field for field in required_fields if field not in self.inputs]
        if missing_fields:
            raise ValueError(f"Missing required inputs: {', '.join(missing_fields)}")
            
        # Set default feedback questions if not provided
        if 'feedback_questions' not in self.inputs or not self.inputs['feedback_questions']:
            self.inputs['feedback_questions'] = ["Provide general feedback on the essay"]

        # Ensure thread_id is present for memory analysis
        if 'thread_id' not in self.inputs:
            logger.warning("No thread_id provided, memory analysis will be skipped")
            self.inputs['thread_id'] = None
            
        # Initialize tools
        try:
            self.student_profile_tool = StudentProfileTool()
            self.college_search_tool = CollegeSearchTool()
            self._memory_tool = EssayFeedbackMemoryTool()
            self.essay_feedback_memory_tool = self._memory_tool  # Keep for backward compatibility
            logger.info("Successfully initialized tools")
        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            raise

    def log_task_result(self, task_id: str, success: bool, error: str = None):
        """Log task execution results"""
        try:
            self.task_results[task_id] = {
                "success": success,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }

            log_path = os.path.join(os.path.dirname(__file__), "crew_execution.log")
            with open(log_path, "a") as f:
                json.dump({
                    "task_id": task_id,
                    "result": self.task_results[task_id]
                }, f)
                f.write("\n")
            logger.debug(f"Logged task result for {task_id}")
        except Exception as e:
            logger.error(f"Error logging task result: {str(e)}")

    @agent
    def essay_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['essay_analyzer'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=10
        )

    @agent
    def college_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['college_researcher'],
            tools=[self.college_search_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=40
        )

    @agent
    def feedback_synthesizer(self) -> Agent:
        return Agent(
            config=self.agents_config['feedback_synthesizer'],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=20
        )

    @agent
    def college_data_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['college_data_analyzer'],
            tools=[self.college_search_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=30
        )

    @agent
    def student_profile_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['student_profile_analyzer'],
            tools=[self.student_profile_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=10
        )

    @agent
    def memory_analyzer(self) -> Agent:
        try:
            # Ensure tool is properly instantiated
            if not hasattr(self, '_memory_tool'):
                self._memory_tool = self.essay_feedback_memory_tool
                logger.info("Memory tool initialized")

            return Agent(
                config=self.agents_config['memory_analyzer'],
                tools=[self._memory_tool],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                max_execution_time=10
            )
        except Exception as e:
            logger.error(f"Error initializing memory analyzer: {str(e)}")
            raise

    @task
    def analyze_essay_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['analyze_essay_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['analyze_essay_task']['expected_output'],
                agent=self.essay_analyzer()
            )
            self.log_task_result("analyze_essay_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in analyze_essay_task: {str(e)}")
            self.log_task_result("analyze_essay_task", False, str(e))
            raise

    @task
    def analyze_student_profile_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['analyze_student_profile_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['analyze_student_profile_task']['expected_output'],
                agent=self.student_profile_analyzer()
            )
            self.log_task_result("analyze_student_profile_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in analyze_student_profile_task: {str(e)}")
            self.log_task_result("analyze_student_profile_task", False, str(e))
            raise

    @task
    def analyze_college_data_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['analyze_college_data_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['analyze_college_data_task']['expected_output'],
                agent=self.college_data_analyzer()
            )
            self.log_task_result("analyze_college_data_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in analyze_college_data_task: {str(e)}")
            self.log_task_result("analyze_college_data_task", False, str(e))
            raise

    @task
    def analyze_thread_memory_task(self) -> Task:
        try:
            # Skip memory analysis if no thread_id
            if not self.inputs.get('thread_id'):
                logger.info("Skipping memory analysis - no thread_id provided")
                return None

            # Format the input data as a JSON string for the tool
            tool_input = json.dumps({
                "auth0_id": self.inputs.get('auth0_id'),
                "thread_id": self.inputs.get('thread_id')
            })
            
            task_config = dict(self.tasks_config['analyze_thread_memory_task'])
            task_config['description'] = task_config['description'].format(
                auth0_id=self.inputs.get('auth0_id'),
                thread_id=self.inputs.get('thread_id'),
                tool_input=tool_input
            )

            task = Task(
                description=task_config['description'],
                expected_output=task_config['expected_output'],
                agent=self.memory_analyzer()
            )
            
            logger.info(f"Created memory analysis task with input: {tool_input}")
            self.log_task_result("analyze_thread_memory_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in analyze_thread_memory_task: {str(e)}")
            self.log_task_result("analyze_thread_memory_task", False, str(e))
            raise

    @task
    def research_college_preferences_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['research_college_preferences_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['research_college_preferences_task']['expected_output'],
                agent=self.college_researcher()
            )
            self.log_task_result("research_college_preferences_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in research_college_preferences_task: {str(e)}")
            self.log_task_result("research_college_preferences_task", False, str(e))
            raise

    @task
    def generate_feedback_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['generate_feedback_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['generate_feedback_task']['expected_output'],
                agent=self.feedback_synthesizer()
            )
            self.log_task_result("generate_feedback_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in generate_feedback_task: {str(e)}")
            self.log_task_result("generate_feedback_task", False, str(e))
            raise

    @crew
    def crew(self) -> Crew:
        """Creates the Essay Feedback crew with proper task sequencing"""
        try:
            logger.info("=== Starting Essay Feedback Crew Creation ===")
            
            # Get auth0_id from inputs
            auth0_id = self.inputs.get('auth0_id')
            thread_id = self.inputs.get('thread_id')
            
            if not auth0_id:
                logger.error("No auth0_id provided in inputs")
                return {"success": False, "data": None, "error": "auth0_id is required"}

            # Create all possible tasks
            all_tasks = [
                self.analyze_thread_memory_task(),  # This might return None
                self.analyze_essay_task(),
                self.analyze_student_profile_task(),
                self.analyze_college_data_task(),
                self.research_college_preferences_task(),
                self.generate_feedback_task()
            ]
            
            # Filter out None tasks
            tasks = [task for task in all_tasks if task is not None]
            
            agents = [
                self.memory_analyzer(),
                self.essay_analyzer(),
                self.student_profile_analyzer(),
                self.college_data_analyzer(),
                self.college_researcher(),
                self.feedback_synthesizer()
            ]

            logger.info(f"Created crew with {len(tasks)} tasks and {len(agents)} agents")
            
            # Create crew with proper memory configuration
            crew = Crew(
                agents=agents,
                tasks=tasks,
                llm=llm,
                process=Process.sequential,
                verbose=True,
                memory=True,
            )
            
            logger.info(f"Crew created successfully with memory configuration for auth0_id: {auth0_id}")
            return crew

        except Exception as e:
            logger.error(f"Error in crew creation: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            self.log_task_result("crew", False, str(e))
            return {"success": False, "data": None, "error": str(e)}