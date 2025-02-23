import json
import os
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient
import logging

logger = logging.getLogger(__name__)

def upload_college_data():
    try:
        # Initialize Pinecone with hardcoded values
        pc = PineconeClient(
            api_key="pcsk_7Wrfxz_NZ1egjkTBejyiDfXJdqsMixzSVMogWnMgikCNnoC3D6W87XESuz8wxfgNzayjwJ"
        )
        
        # Set OpenAI API key
        os.environ["OPENAI_API_KEY"] = "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"
        
        # Load college data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'agent_crews', 'data', 'sample_college.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        colleges = data.get('colleges', [])
        texts = []
        metadatas = []
        
        # Process colleges (text and metadata generation stays the same)
        for college in colleges:
            text = f"""
            {college['name']}
            Mission: {college['mission']}
            Values: {college['values']}
            Location: {college['location']}
            Type: {college['type']}
            Size: {college['size']}
            GPA Range: {college['gpa']}
            SAT Range: {college['sat_range']}
            ACT Range: {college['act_range']}
            Cost: ${college['cost_of_attendance']}
            Special Programs: {', '.join(college['special_programs'])}
            Student Activities: {', '.join(college['student_activities_orgs'])}
            Excellent ECs: {', '.join(college['excellent_ecs'])}
            Extracurricular Expectations: {college['extracurricular_expectations']}
            Essays: {', '.join(essay['prompt'] for essay in college['essays_that_got_accepted'])}
            """
            
            metadata = {
                "id": college['id'],
                "name": college['name'],
                "cost": college['cost_of_attendance'],
                "meets_need_national": college['meets_demonstrated_need']['national'],
                "meets_need_international": college['meets_demonstrated_need']['international'],
                "need_blind_national": college['need_blind_status']['national'],
                "need_blind_international": college['need_blind_status']['international'],
                "stingy_with_aid_national": college['stingy_with_aid']['national'],
                "stingy_with_aid_international": college['stingy_with_aid']['international'],
                "max_aid_national": college['max_financial_aid']['national'],
                "max_aid_international": college['max_financial_aid']['international'],
                "co_educational": college['co_educational'],
                "location": college['location'],
                "size": college['size'],
                "type": college['type'],
                "gpa_range": college['gpa'],
                "sat_range": college['sat_range'],
                "act_range": college['act_range'],
                "extracurricular_score": college['extracurricular_score_weight']
            }
            
            texts.append(text)
            metadatas.append(metadata)
        
        # Create embeddings
        embeddings = OpenAIEmbeddings()
        index_name = "college-matcher"
        
        # Delete existing index if it exists
        if index_name in pc.list_indexes().names():
            pc.delete_index(index_name)
        
        # Create new index
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embedding dimension
            metric='cosine'
        )
        
        # Upload to Pinecone
        Pinecone.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            index_name=index_name
        )
        
        logger.info(f"Successfully uploaded {len(colleges)} colleges to Pinecone")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading college data: {str(e)}")
        return False

if __name__ == "__main__":
    upload_college_data()