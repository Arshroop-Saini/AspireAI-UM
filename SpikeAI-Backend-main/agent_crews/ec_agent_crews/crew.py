# src/latest_ai_development/crew.py
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import json

from .tools.student_profile_memory_tool import StudentProfileMemoryTool
from .tools.past_suggestions_history_tool import PastSuggestionsHistoryTool
from .tools.search_tool import SearchTool
from langchain_openai import ChatOpenAI
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

os.environ["OPENAI_API_KEY"] = "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"
llm = ChatOpenAI(model="gpt-4o-mini")

@CrewBase
class ECRecommendationCrew():
	"""Extracurricular Activities Research and Recommendation Crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, inputs: Optional[Dict[str, Any]] = None):
		"""Initialize the EC Recommendation crew with required tools and inputs."""
		super().__init__()
		self.inputs = inputs or {}
		self.task_results = {}
		
		# Validate required inputs
		required_fields = ['auth0_id', 'activity_type', 'hrs_per_wk']
		missing_fields = [field for field in required_fields if field not in self.inputs]
		if missing_fields:
			raise ValueError(f"Missing required inputs: {', '.join(missing_fields)}")
			
		# Initialize tools
		try:
			self.student_profile_tool = StudentProfileMemoryTool()
			self.past_suggestions_tool = PastSuggestionsHistoryTool()
			self.search_tool = SearchTool()
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
	def cv_reader(self) -> Agent:
		try:
			return Agent(
				config=self.agents_config['cv_reader'],
				tools=[self.student_profile_tool],
				llm=llm,
				verbose=True,
				allow_delegation=False,
				max_execution_time=10,
				context=[{
					"auth0_id": self.inputs.get('auth0_id'),
					"activity_type": self.inputs.get('activity_type'),
					"hrs_per_wk": self.inputs.get('hrs_per_wk')
				}]
			)
		except Exception as e:
			logger.error(f"Error initializing cv_reader: {str(e)}")
			raise

	@agent
	def past_ec_suggestion_checker(self) -> Agent:
		try:
			return Agent(
				config=self.agents_config['past_ec_suggestion_checker'],
				tools=[self.past_suggestions_tool],
				llm=llm,
				verbose=True,
				allow_delegation=False,
				max_execution_time=10,
				context=[{
					"auth0_id": self.inputs.get('auth0_id'),
					"activity_type": self.inputs.get('activity_type')
				}]
			)
		except Exception as e:
			logger.error(f"Error initializing past_ec_suggestion_checker: {str(e)}")
			raise

	@agent
	def ec_scout(self) -> Agent:
		try:
			return Agent(
				config=self.agents_config['ec_scout'],
				tools=[self.search_tool],
				llm=llm,
				verbose=True,
				allow_delegation=False,
				max_execution_time=30,
				context=[{
					"auth0_id": self.inputs.get('auth0_id'),
					"activity_type": self.inputs.get('activity_type'),
					"hrs_per_wk": self.inputs.get('hrs_per_wk')
				}]
			)
		except Exception as e:
			logger.error(f"Error initializing ec_scout: {str(e)}")
			raise

	@agent
	def ec_suggestor(self) -> Agent:
		try:
			return Agent(
				config=self.agents_config['ec_suggestor'],
				llm=llm,
				verbose=True,
				allow_delegation=False,
				max_execution_time=20,
				context=[{
					"auth0_id": self.inputs.get('auth0_id'),
					"activity_type": self.inputs.get('activity_type'),
					"hrs_per_wk": self.inputs.get('hrs_per_wk')
				}]
			)
		except Exception as e:
			logger.error(f"Error initializing ec_suggestor: {str(e)}")
			raise

	@task
	def analyze_student_profile_task(self) -> Task:
		"""Task for analyzing student profile"""
		try:
			auth0_id = str(self.inputs.get('auth0_id')).strip('"')  # Remove any quotes
			activity_type = self.inputs.get('activity_type')
			hrs_per_wk = self.inputs.get('hrs_per_wk')
			
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for profile analysis")

			task_config = dict(self.tasks_config['analyze_student_profile_task'])
			description = task_config['description'].replace(
				'{auth0_id}', auth0_id
			).replace(
				'{activity_type}', str(activity_type)
			).replace(
				'{hrs_per_wk}', str(hrs_per_wk)
			)

			task = Task(
				description=description,
				expected_output=task_config['expected_output'],
				agent=self.cv_reader()
			)
			self.log_task_result("analyze_student_profile_task", True)
			return task
		except Exception as e:
			logger.error(f"Error in analyze_student_profile_task: {str(e)}")
			self.log_task_result("analyze_student_profile_task", False, str(e))
			raise

	@task
	def check_past_suggestions_task(self) -> Task:
		"""Task for checking past EC suggestions"""
		try:
			auth0_id = str(self.inputs.get('auth0_id')).strip('"')
			activity_type = self.inputs.get('activity_type')
			
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for checking past suggestions")

			task_config = dict(self.tasks_config['check_past_suggestions_task'])
			description = task_config['description'].replace(
				'{auth0_id}', auth0_id
			).replace(
				'{activity_type}', str(activity_type)
			)

			task = Task(
				description=description,
				expected_output=task_config['expected_output'],
				agent=self.past_ec_suggestion_checker()
			)
			self.log_task_result("check_past_suggestions_task", True)
			return task
		except Exception as e:
			logger.error(f"Error in check_past_suggestions_task: {str(e)}")
			self.log_task_result("check_past_suggestions_task", False, str(e))
			raise

	@task
	def scout_activities_task(self) -> Task:
		"""Task for scouting EC activities"""
		try:
			auth0_id = str(self.inputs.get('auth0_id')).strip('"')
			activity_type = self.inputs.get('activity_type')
			hrs_per_wk = self.inputs.get('hrs_per_wk')
			
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for scouting activities")

			task_config = dict(self.tasks_config['scout_activities_task'])
			description = task_config['description'].replace(
				'{auth0_id}', auth0_id
			).replace(
				'{activity_type}', str(activity_type)
			).replace(
				'{hrs_per_wk}', str(hrs_per_wk)
			)

			task = Task(
				description=description,
				expected_output=task_config['expected_output'],
				agent=self.ec_scout()
			)
			self.log_task_result("scout_activities_task", True)
			return task
		except Exception as e:
			logger.error(f"Error in scout_activities_task: {str(e)}")
			self.log_task_result("scout_activities_task", False, str(e))
			raise

	@task
	def generate_recommendations_task(self) -> Task:
		"""Task for generating EC recommendations"""
		try:
			auth0_id = str(self.inputs.get('auth0_id')).strip('"')
			activity_type = self.inputs.get('activity_type')
			hrs_per_wk = self.inputs.get('hrs_per_wk')
			
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for generating recommendations")

			task_config = dict(self.tasks_config['generate_recommendations_task'])
			description = task_config['description'].replace(
				'{auth0_id}', auth0_id
			).replace(
				'{activity_type}', str(activity_type)
			).replace(
				'{hrs_per_wk}', str(hrs_per_wk)
			)

			task = Task(
				description=description,
				expected_output=task_config['expected_output'],
				agent=self.ec_suggestor()
			)
			self.log_task_result("generate_recommendations_task", True)
			return task
		except Exception as e:
			logger.error(f"Error in generate_recommendations_task: {str(e)}")
			self.log_task_result("generate_recommendations_task", False, str(e))
			raise

	@crew
	def crew(self) -> Crew:
		"""Creates the EC Recommendation crew with proper task sequencing"""
		try:
			logger.info("=== Starting EC Recommendation Crew Creation ===")
			
			auth0_id = self.inputs.get('auth0_id')
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				return {"success": False, "data": None, "error": "auth0_id is required"}

			agents = [
				self.cv_reader(),
				self.past_ec_suggestion_checker(),
				self.ec_scout(),
				self.ec_suggestor()
			]

			tasks = [
				self.analyze_student_profile_task(),
				self.check_past_suggestions_task(),
				self.scout_activities_task(),
				self.generate_recommendations_task()
			]

			logger.info(f"Created crew with {len(tasks)} tasks and {len(agents)} agents")
			
			crew = Crew(
				agents=agents,
				tasks=tasks,
				llm=llm,
				process=Process.sequential,
				verbose=True,
				memory=True
			)
			
			logger.info(f"Crew created successfully for auth0_id: {auth0_id}")
			return crew

		except Exception as e:
			logger.error(f"Error in crew creation: {str(e)}")
			logger.error(f"Error type: {type(e)}")
			logger.error(f"Error traceback: {traceback.format_exc()}")
			self.log_task_result("crew", False, str(e))
			return {"success": False, "data": None, "error": str(e)}