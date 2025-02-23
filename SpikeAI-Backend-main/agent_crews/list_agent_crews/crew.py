# src/latest_ai_development/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from models.student_model import Student
from typing import List, Dict, Any
import os
import logging
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from agent_crews.list_agent_crews.tools.search_tool import SearchTool
from agent_crews.list_agent_crews.tools.student_profile_memory_tool import StudentProfileMemoryTool
from agent_crews.list_agent_crews.tools.past_suggestions_history_tool import PastSuggestionsHistoryTool
from middleware.college_list_validation import CollegeListValidator
import traceback
from mem0 import MemoryClient

os.environ["OPENAI_API_KEY"] = "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"
os.environ["MEM0_API_KEY"] = "m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh"
llm = ChatOpenAI(model="gpt-4o-mini")

logger = logging.getLogger(__name__)

client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])

# Initialize tools
search_tool = SearchTool()

def json_serial(obj):
	"""JSON serializer for objects not serializable by default json code"""
	if isinstance(obj, datetime):
		return obj.isoformat()
	raise TypeError(f"Type {type(obj)} not serializable")

@CrewBase
class MatchToProposalCrew:
	"""US College Matching Crew for sequential college recommendation process"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, inputs: Dict[str, Any]):
		self.inputs = inputs
		self.task_results = {}
		self.profile_validator = CollegeListValidator()
		# Initialize tools as instance variables
		self.search_tool = SearchTool()
		
		# Get auth0_id from inputs and validate it
		auth0_id = inputs.get('auth0_id')
		if not auth0_id:
			logger.error("No auth0_id provided in inputs")
			raise ValueError("auth0_id is required")
			
		logger.info(f"Initializing crew with auth0_id: {auth0_id}")


		
		logger.info("Memory configurations initialized successfully")

	def log_task_result(self, task_id: str, success: bool, error: str = None):
		"""Log task execution results"""
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
			}, f, default=json_serial)
			f.write("\n")

	@agent
	def student_profile_analyzer(self) -> Agent:
		"""Profile analyzer that determines if student is domestic or international"""
			
		return Agent(
			config=self.agents_config['cv_reader'],
			llm=llm,
			memory=True,
			verbose=True,
			max_execution_time=10,
			tools=[StudentProfileMemoryTool()],
		)


	@agent
	def college_expert(self) -> Agent:
		"""College expert that researches and suggests colleges"""
		return Agent(
			config=self.agents_config['college_expert'],
			llm=llm,
			memory=True,
			verbose=True,
			max_execution_time=30,
			tools=[PastSuggestionsHistoryTool(),search_tool],
		)

	@task
	def analyze_profile_task(self) -> Task:
		"""Task for analyzing student profile"""
		try:
			# Get auth0_id from inputs
			auth0_id = self.inputs.get('auth0_id')
			college_type = self.inputs.get('college_type')
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for profile analysis")

			# Format task config with auth0_id
			task_config = dict(self.tasks_config['analyze_profile_task'])
			task_config['description'] = task_config['description'].replace('{auth0_id}', str(auth0_id)).replace('{college_type}', str(college_type))

			return Task(
				config=task_config,
				agent=self.student_profile_analyzer(),
			)
		except Exception as e:
			logger.error(f"Error in analyze_profile_task: {str(e)}")
			logger.error(f"Error details: {traceback.format_exc()}")
			raise

	@task
	def research_colleges(self) -> Task:
		"""Task for researching and suggesting colleges"""
		try:
			# Get auth0_id and college_type from inputs
			auth0_id = self.inputs.get('auth0_id')
			college_type = self.inputs.get('college_type', 'all')
			
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				raise ValueError("auth0_id is required for college research")

			# Format task config with auth0_id and college_type
			task_config = dict(self.tasks_config['research_colleges'])
			task_config['description'] = task_config['description'].replace('{auth0_id}', str(auth0_id)).replace('{college_type}', str(college_type))

			return Task(
				config=task_config,
				agent=self.college_expert(),
			)
		except Exception as e:
			logger.error(f"Error in research_colleges: {str(e)}")
			raise


	@crew
	def crew(self) -> Crew:
		"""Create and run the crew for generating US college matches."""
		try:
			logger.info("=== Starting Crew Creation ===")
			
			# Get auth0_id from inputs
			auth0_id = self.inputs.get('auth0_id')
			if not auth0_id:
				logger.error("No auth0_id provided in inputs")
				return {"success": False, "data": None, "error": "auth0_id is required"}
				
			logger.info(f"Creating crew for student with auth0_id: {auth0_id}")
			
			# Validate and store student profile
			student = Student.get_by_auth0_id(auth0_id)
			if not student:
				logger.error(f"Student profile not found for auth0_id: {auth0_id}")
				return {"success": False, "data": None, "error": "Student profile not found"}

			# Log student profile for debugging
			logger.info(f"Found student profile: {student.get('email')} with auth0_id: {auth0_id}")

			# Validate student profile
			validation_errors = self.profile_validator.validate_student_profile(student)
			if validation_errors:
				logger.error(f"Validation failed for student {auth0_id}: {validation_errors}")
				return {"success": False, "data": None, "error": validation_errors[0]}

			# Store validated profile
			store_result = self.profile_validator.store_student_profile(student)
			if store_result:
				logger.error(f"Error storing profile for student {auth0_id}: {store_result}")
				return {"success": False, "data": None, "error": store_result[0]}

			# Update inputs with validated profile data
			self.inputs.update(self.profile_validator.inputs)

			# Create crew with sequential process
			crew = Crew(
				agents=[
					self.student_profile_analyzer(),
					self.college_expert(),
				],
				tasks=[
					self.analyze_profile_task(),
					self.research_colleges(),
				],
				llm=llm,
				process=Process.sequential,
				memory=True,
				verbose=True,
			)
			
			logger.info(f"Crew created successfully for student {auth0_id}")
			return crew

		except Exception as e:
			logger.error(f"Error in crew creation: {str(e)}")
			logger.error(f"Error type: {type(e)}")
			logger.error(f"Error traceback: {traceback.format_exc()}")
			self.log_task_result("crew", False, str(e))
			return {"success": False, "data": None, "error": str(e)}

class CollegeListCrew:
	def __init__(self):
		self.profile_analysis = None
		self.college_suggestions = None
		self.college_statistics = None

	def process_step(self, step_output, step_number):
		if step_number == 1:
			self.profile_analysis = step_output
			return True
		elif step_number == 2:
			self.college_suggestions = step_output
			return True
		return False

	def get_final_output(self):
		return {
			"profile_analysis": self.profile_analysis,
			"college_list": self.college_suggestions,
		}