from datetime import datetime
from config.db import get_db

class BlacklistModel:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db.blacklisted_tokens

    def add_to_blacklist(self, email, token, student_data):
        """Add a token to the blacklist with student data"""
        deletion_time = datetime.utcnow()
        blacklist_entry = {
            'email': email,
            'token': token,  # Required field
            'exp_time': int(deletion_time.timestamp()),  # Convert to Unix timestamp (int)
            'auth0_id': student_data.get('auth0_id'),
            'name': student_data.get('name'),
            'deleted_at': deletion_time,
            'reason': 'User requested deletion',
            'account_created_at': student_data.get('created_at'),
            'account_lifetime_days': (deletion_time - student_data.get('created_at')).days if student_data.get('created_at') else 0,
            'had_subscription': student_data.get('subscription', {}).get('is_subscribed', False),
            'subscription_status': student_data.get('subscription', {}).get('status'),
            'last_plan': student_data.get('subscription', {}).get('plan'),
            'profile_completion': {
                'had_major': bool(student_data.get('major')),
                'had_extracurriculars': len(student_data.get('extracurriculars', [])) > 0,
                'had_awards': len(student_data.get('awards', [])) > 0,
                'had_personality_type': bool(student_data.get('personality_type')),
                'had_student_theme': bool(student_data.get('student_theme'))
            },
            'deletion_metadata': {
                'user_agent': student_data.get('user_agent'),
                'ip_address': student_data.get('ip_address'),
                'timestamp': deletion_time
            }
        }
        return self.collection.insert_one(blacklist_entry)

    def is_blacklisted(self, email):
        """Check if an email is blacklisted"""
        return bool(self.collection.find_one({'email': email}))

    def get_blacklist_info(self, email):
        """Get blacklist information for an email"""
        return self.collection.find_one({'email': email})

    def remove_from_blacklist(self, email):
        """Remove an email from blacklist (admin function)"""
        return self.collection.delete_one({'email': email})

    def get_all_blacklisted(self, skip=0, limit=20):
        """Get all blacklisted accounts with pagination"""
        return list(self.collection.find().skip(skip).limit(limit)) 