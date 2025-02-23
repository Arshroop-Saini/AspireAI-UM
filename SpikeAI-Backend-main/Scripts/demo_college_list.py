#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
import logging
from typing import Dict, Any, Optional

# Add parent directory to path to import from parent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_crews.list_agent_crews.crew import MatchToProposalCrew
from models.student_model import Student
from controllers.college_list_generator_controller import generate_college_list

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_college_output(output: str) -> str:
    """Format the college list output for better console display"""
    try:
        # Try to parse if output is JSON string
        try:
            data = json.loads(output)
            if isinstance(data, dict) and 'college_list' in data.get('data', {}):
                output = data['data']['college_list']
        except (json.JSONDecodeError, TypeError):
            pass

        # Split the output into individual college sections
        colleges = output.split('\n\n')
        formatted_output = []
        
        for college in colleges:
            if college.strip():
                formatted_output.append('-' * 80)
                formatted_output.append(college.strip())
        
        formatted_output.append('-' * 80)
        return '\n'.join(formatted_output)
    except Exception as e:
        logger.error(f"Error formatting output: {str(e)}")
        return output

def display_student_info(student: Dict[str, Any]) -> None:
    """Display relevant student information"""
    logger.info("\n" + "="*80)
    logger.info("STUDENT PROFILE INFORMATION")
    logger.info("="*80)
    
    if student.get('student_context'):
        context = student['student_context']
        print(f"\nStudent Type: {'International' if context.get('international_student') else 'Domestic'}")
        print(f"Country: {context.get('country', 'N/A')}")
        print(f"Financial Aid Required: {context.get('financial_aid_required', 'N/A')}")
        print(f"First Generation: {context.get('first_generation', 'N/A')}")
    
    if student.get('student_statistics'):
        stats = student['student_statistics']
        print(f"\nAcademic Profile:")
        print(f"GPA (Weighted): {stats.get('weight_gpa', 'N/A')}")
        print(f"GPA (Unweighted): {stats.get('unweight_gpa', 'N/A')}")
        print(f"SAT Score: {stats.get('sat_score', 'N/A')}")
        print(f"Class Rank: {stats.get('class_rank', 'N/A')}")
    
    if student.get('student_preferences'):
        prefs = student['student_preferences']
        print(f"\nPreferences:")
        print(f"Preferred Regions: {', '.join(prefs.get('preferred_regions', ['N/A']))}")
        print(f"Preferred States: {', '.join(prefs.get('preferred_states', ['N/A']))}")
        print(f"Campus Sizes: {', '.join(prefs.get('campus_sizes', ['N/A']))}")
        print(f"College Types: {', '.join(prefs.get('college_types', ['N/A']))}")

def run_college_list_demo(auth0_id: str) -> None:
    """Run the college list generation demo with the given auth0_id"""
    try:
        logger.info("Starting College List Generation Demo")
        logger.info(f"Using auth0_id: {auth0_id}")

        # Get student data first
        student = Student.get_by_auth0_id(auth0_id)
        if not student:
            logger.error("Student profile not found")
            return

        # Display student information
        display_student_info(student)

        # Generate college list using the controller
        logger.info("\nGenerating college list...")
        result = generate_college_list(auth0_id)

        if not result.get('success'):
            logger.error(f"College list generation failed: {result.get('error')}")
            return

        # Format and display results
        logger.info("\n" + "="*80)
        logger.info("COLLEGE LIST GENERATION RESULTS")
        logger.info("="*80)
        
        output = result.get('data', {}).get('college_list', '')
        formatted_output = format_college_output(output)
        print("\n" + formatted_output + "\n")

        logger.info("="*80)
        logger.info("Demo completed successfully")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        raise

if __name__ == "__main__":
    # Check if auth0_id is provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python demo_college_list.py <auth0_id>")
        sys.exit(1)

    auth0_id = sys.argv[1]
    run_college_list_demo(auth0_id) 