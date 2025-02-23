from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Dict, Any, Optional
from datetime import datetime
import os
import logging
import json
import traceback
from .tools import StudentProfileTool, IdeasHistoryTool, CollegeSearchTool
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.environ["OPENAI_API_KEY"] = "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"
llm = ChatOpenAI(model="gpt-4o")

@CrewBase
class EssayBrainstormCrew():
    """Essay Brainstorming Crew"""

    # Get the absolute path to the config files
    base_path = os.path.dirname(os.path.abspath(__file__))
    agents_config = os.path.join(base_path, 'config', 'agents.yaml')
    tasks_config = os.path.join(base_path, 'config', 'tasks.yaml')

    def __init__(self, inputs: Optional[Dict[str, Any]] = None):
        """Initialize the Essay Brainstorming crew with required tools and inputs."""
        super().__init__()
        self.inputs = inputs or {}
        self.task_results = {}
        
        # Log config file paths
        logger.info(f"Loading config files from:")
        logger.info(f"Agents config: {self.agents_config}")
        logger.info(f"Tasks config: {self.tasks_config}")
        
        # Verify config files exist
        if not os.path.exists(self.agents_config):
            raise FileNotFoundError(f"Agents config file not found at: {self.agents_config}")
        if not os.path.exists(self.tasks_config):
            raise FileNotFoundError(f"Tasks config file not found at: {self.tasks_config}")
            
        # Validate required inputs
        required_fields = ['auth0_id', 'college_name', 'essay_prompt']
        missing_fields = [field for field in required_fields if field not in self.inputs]
        if missing_fields:
            raise ValueError(f"Missing required inputs: {', '.join(missing_fields)}")
            
        # Ensure thread_id is present for ideas history
        if 'thread_id' not in self.inputs:
            logger.warning("No thread_id provided, ideas history will be skipped")
            self.inputs['thread_id'] = None
            
        # Initialize tools
        try:
            self.profile_tool = StudentProfileTool()
            self.ideas_tool = IdeasHistoryTool()
            self.search_tool = CollegeSearchTool()
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
    def profile_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['profile_analyzer'],
            tools=[self.profile_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=10,
            llm=llm
        )


    @agent
    def ideas_history_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['ideas_history_checker'],
            tools=[self.ideas_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=10,
            llm=llm
        )


    @agent
    def college_values_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['college_values_researcher'],
            tools=[self.search_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=30,
            llm=llm
        )


    @agent
    def essay_examples_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['essay_examples_researcher'],
            tools=[self.search_tool],
            verbose=True,
            allow_delegation=False,
            max_execution_time=30,
            llm=llm
        )


    @agent
    def ideas_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['ideas_generator'],
            verbose=True,
            allow_delegation=False,
            max_execution_time=20,
            llm=llm
        )


    @task
    def analyze_student_profile_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['analyze_student_profile_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['analyze_student_profile_task']['expected_output'],
                agent=self.profile_analyzer()
            )
            self.log_task_result("analyze_student_profile_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in analyze_student_profile_task: {str(e)}")
            self.log_task_result("analyze_student_profile_task", False, str(e))
            raise

    @task
    def check_ideas_history_task(self) -> Task:
        """Only create this task if thread_id is provided"""
        try:
            if not self.inputs.get('thread_id'):
                logger.info("Skipping ideas history task - no thread_id provided")
                return None
                
            task = Task(
                description=self.tasks_config['check_ideas_history_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['check_ideas_history_task']['expected_output'],
                agent=self.ideas_history_checker()
            )
            self.log_task_result("check_ideas_history_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in check_ideas_history_task: {str(e)}")
            self.log_task_result("check_ideas_history_task", False, str(e))
            raise

    @task
    def research_college_values_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['research_college_values_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['research_college_values_task']['expected_output'],
                agent=self.college_values_researcher()
            )
            self.log_task_result("research_college_values_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in research_college_values_task: {str(e)}")
            self.log_task_result("research_college_values_task", False, str(e))
            raise

    @task
    def research_essay_examples_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['research_essay_examples_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['research_essay_examples_task']['expected_output'],
                agent=self.essay_examples_researcher()
            )
            self.log_task_result("research_essay_examples_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in research_essay_examples_task: {str(e)}")
            self.log_task_result("research_essay_examples_task", False, str(e))
            raise

    @task
    def generate_essay_ideas_task(self) -> Task:
        try:
            task = Task(
                description=self.tasks_config['generate_essay_ideas_task']['description'].format(**self.inputs),
                expected_output=self.tasks_config['generate_essay_ideas_task']['expected_output'],
                agent=self.ideas_generator()
            )
            self.log_task_result("generate_essay_ideas_task", True)
            return task
        except Exception as e:
            logger.error(f"Error in generate_essay_ideas_task: {str(e)}")
            self.log_task_result("generate_essay_ideas_task", False, str(e))
            raise

    @crew
    def crew(self) -> Crew:
        """Creates the Essay Brainstorming crew with proper task sequencing"""
        try:
            logger.info("=== Starting Essay Brainstorming Crew Creation ===")
            
            # Get required inputs
            auth0_id = self.inputs.get('auth0_id')
            thread_id = self.inputs.get('thread_id')
            
            if not auth0_id:
                logger.error("No auth0_id provided in inputs")
                return {"success": False, "data": None, "error": "auth0_id is required"}

            # Create all possible tasks
            all_tasks = [
                self.analyze_student_profile_task(),
                self.check_ideas_history_task(),  # This might return None
                self.research_college_values_task(),
                self.research_essay_examples_task(),
                self.generate_essay_ideas_task()
            ]
            
            # Filter out None tasks
            tasks = [task for task in all_tasks if task is not None]
            
            # Create and configure the crew
            crew = Crew(
                agents=[
                    self.profile_analyzer(),
                    self.ideas_history_checker(),
                    self.college_values_researcher(),
                    self.essay_examples_researcher(),
                    self.ideas_generator()
                ],
                tasks=tasks,
                llm=llm,
                process=Process.sequential,
                verbose=True,
                memory=True
            )

            logger.info("=== Essay Brainstorming Crew Created Successfully ===")
            return crew

        except Exception as e:
            logger.error(f"Error creating crew: {str(e)}\n{traceback.format_exc()}")
            raise