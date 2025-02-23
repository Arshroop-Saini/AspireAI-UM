from openai import AsyncOpenAI
import os
import logging
from datetime import datetime
from models.student_model import Student
from config.db import get_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

class ProfileEvaluationService:
    @staticmethod
    async def evaluate_testing_score(student_data):
        """Evaluate testing score based on student statistics"""
        prompt = f"""
        Analyze the following student statistics and provide a score from 1-6 (can use decimals):
        - SAT Score: {student_data.get('student_statistics', {}).get('sat_score')}
        - Weighted GPA: {student_data.get('student_statistics', {}).get('weight_gpa')}
        - Unweighted GPA: {student_data.get('student_statistics', {}).get('unweight_gpa')}
        - Class Rank: {student_data.get('student_statistics', {}).get('class_rank')}

        Consider:
        1. SAT score percentile
        2. GPA strength
        3. Class rank context
        4. Overall academic performance

        Return only a number between 1-6.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 1.0

    @staticmethod
    async def evaluate_hsr_score(student_data):
        """Evaluate high school rigor score"""
        prompt = f"""
        Analyze the following student data for academic rigor and provide a score from 1-6 (can use decimals):
        - Course Load: Weighted GPA {student_data.get('student_statistics', {}).get('weight_gpa')} vs Unweighted {student_data.get('student_statistics', {}).get('unweight_gpa')}
        - Class Rank: {student_data.get('student_statistics', {}).get('class_rank')}
        - Awards: {student_data.get('awards', [])}

        Consider:
        1. GPA differential (weighted vs unweighted)
        2. Academic awards and recognition
        3. Class rank context
        4. Overall course rigor indicators

        Return only a number between 1-6.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 1.0

    @staticmethod
    async def evaluate_ecs_score(student_data):
        """Evaluate extracurricular activities score"""
        prompt = f"""
        Analyze the following extracurricular activities and provide a score from 1-6 (can use decimals):
        - Activities: {student_data.get('extracurriculars', [])}
        - Awards: {student_data.get('awards', [])}
        - Hooks: {student_data.get('hooks', [])}

        Consider:
        1. Leadership positions
        2. Depth of involvement
        3. Impact and achievements
        4. Diversity of activities
        5. Alignment with interests

        Return only a number between 1-6.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 1.0

    @staticmethod
    async def evaluate_spiv_score(student_data):
        """Evaluate Spike and Intellectual Vitality score"""
        prompt = f"""
        Analyze the following student data for intellectual vitality and spike strength, provide a score from 1-6 (can use decimals):
        - Major: {student_data.get('major')}
        - Personality Type: {student_data.get('personality_type')}
        - Theme: {student_data.get('student_theme')}
        - Activities: {student_data.get('extracurriculars', [])}
        - Awards: {student_data.get('awards', [])}

        Consider:
        1. Clarity of academic/career direction
        2. Depth of intellectual engagement
        3. Uniqueness of profile
        4. Alignment of activities with interests
        5. Evidence of initiative and creativity

        Return only a number between 1-6.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 1.0

    @staticmethod
    async def evaluate_overall_score(scores):
        """Calculate overall evaluation score"""
        weights = {
            'testing_score': 0.25,
            'hsr_score': 0.25,
            'ecs_score': 0.25,
            'spiv_score': 0.25
        }
        
        eval_score = sum(scores[key] * weights[key] for key in weights)
        return round(eval_score, 2)

    @classmethod
    async def evaluate_profile(cls, auth0_id: str) -> dict:
        """Evaluate entire student profile and update scores"""
        try:
            # Get student data
            db = get_db()
            student_data = db.students.find_one({'auth0_id': auth0_id})
            
            if not student_data:
                logger.error(f"No student found with auth0_id: {auth0_id}")
                return {'success': False, 'error': 'Student not found'}

            # Calculate individual scores
            scores = {
                'testing_score': await cls.evaluate_testing_score(student_data),
                'hsr_score': await cls.evaluate_hsr_score(student_data),
                'ecs_score': await cls.evaluate_ecs_score(student_data),
                'spiv_score': await cls.evaluate_spiv_score(student_data)
            }
            
            # Calculate overall score
            scores['eval_score'] = await cls.evaluate_overall_score(scores)
            
            # Add timestamp
            scores['last_evaluated'] = datetime.utcnow()
            
            # Update student record
            result = db.students.update_one(
                {'auth0_id': auth0_id},
                {'$set': {'evaluation_scores': scores}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully updated evaluation scores for student {auth0_id}")
                return {'success': True, 'data': scores}
            else:
                logger.error(f"Failed to update evaluation scores for student {auth0_id}")
                return {'success': False, 'error': 'Failed to update scores'}

        except Exception as e:
            logger.error(f"Error in evaluate_profile: {str(e)}")
            return {'success': False, 'error': str(e)} 