import json
import os

def update_college_data():
    # Get the absolute path to the JSON file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'agent_crews', 'list_agent_crews', 'data', 'sample_college.json')
    
    # Fields to remove
    fields_to_remove = [
        'mission',
        'values',
        'extracurricular_expectations',
        'special_programs',
        'student_activities_orgs',
        'excellent_ecs',
        'essays_that_got_accepted'
    ]
    
    # Read the JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Remove fields from each college
    for college in data['colleges']:
        for field in fields_to_remove:
            if field in college:
                del college[field]
    
    # Write back to file
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    update_college_data() 