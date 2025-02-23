import json
import os
from typing import List, Dict
import logging
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pinecone
PINECONE_API_KEY = "pcsk_7Wrfxz_NZ1egjkTBejyiDfXJdqsMixzSVMogWnMgikCNnoC3D6W87XESuz8wxfgNzayjwJ"
PINECONE_ENV = "us-east-1"

# Initialize encoder model
model = SentenceTransformer('all-MiniLM-L6-v2')

def load_json_files() -> Dict:
    """Load both JSON files."""
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        knowledge_path = os.path.join(base_path, "agent_crews", "ec_agent_crews", "knowledge")
        
        # Load college EC info
        with open(os.path.join(knowledge_path, "college_ec_info.json"), 'r') as f:
            college_data = json.load(f)
            
        # Load external programs
        with open(os.path.join(knowledge_path, "external_programs.json"), 'r') as f:
            programs_data = json.load(f)
            
        return {
            "college_data": college_data,
            "programs_data": programs_data
        }
    except Exception as e:
        logger.error(f"Error loading JSON files: {str(e)}")
        raise

def format_college_text(college: Dict) -> str:
    """Format college data into a single text string."""
    return f"""
    College: {college['name']}
    Mission: {college['mission']}
    Values: {college['values']}
    EC Score Weight: {college['extracurricular_score_weight']}
    EC Expectations: {college['extracurricular_expectations']}
    Special Programs: {', '.join(college['special_programs'])}
    Student Organizations: {', '.join(college['student_activities_orgs'])}
    Notable EC Examples: {', '.join(college.get('excellent_ecs', []))}
    """

def format_program_text(program: Dict) -> str:
    """Format program data into a single text string."""
    return f"""
    Program: {program['program_name']} ({program['program_type']})
    Description: {program['description']}
    Eligibility: {program['eligibility']}
    Duration: {program['duration']}
    Location: {program['location']}
    Cost: {program['cost']}
    Deadline: {program['deadline']}
    Recognition Level: {program['recognition_level']}
    Acceptance Rate: {program['acceptance_rate']}
    """

def upsert_vectors(index, vectors, namespace: str):
    """Upsert vectors to specified namespace in batches."""
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        logger.info(f"Uploaded batch {i//batch_size + 1} to namespace: {namespace}")

def create_vector_store():
    """Create and populate the Pinecone vector store."""
    try:
        # Initialize Pinecone with new method
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        index_name = "college-ec-info"
        dimension = model.get_sentence_embedding_dimension()
        
        # Delete index if it exists
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)
            logger.info(f"Deleted existing index: {index_name}")
        
        # Create new index
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        logger.info(f"Created new index: {index_name}")
        
        # Wait a moment for the index to be ready
        time.sleep(10)
        
        # Connect to index
        index = pc.Index(index_name)
        
        # Load data
        data = load_json_files()
        college_vectors = []
        program_vectors = []
        
        # Process college data
        for i, college in enumerate(data["college_data"]["colleges_ec_info"]):
            text = format_college_text(college)
            vector = model.encode(text).tolist()
            college_vectors.append((
                f"college_{i}",
                vector,
                {
                    "type": "college",
                    "name": college["name"],
                    "text": text
                }
            ))
        
        # Process program data
        for i, program in enumerate(data["programs_data"]["external_programs"]):
            text = format_program_text(program)
            vector = model.encode(text).tolist()
            program_vectors.append((
                f"program_{i}",
                vector,
                {
                    "type": "program",
                    "name": program["program_name"],
                    "text": text
                }
            ))
        
        # Upsert vectors to respective namespaces
        upsert_vectors(index, college_vectors, "colleges")
        upsert_vectors(index, program_vectors, "programs")
        
        logger.info("Successfully uploaded all data to Pinecone with separate namespaces")
        
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise

if __name__ == "__main__":
    create_vector_store() 