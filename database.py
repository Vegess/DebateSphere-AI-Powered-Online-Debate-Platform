import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_path="debatesphere.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create analysis table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            confidence_score REAL
        )
        ''')
        
        # Create claims table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            claim_text TEXT NOT NULL,
            verification_status TEXT,
            verification_source TEXT,
            confidence_score REAL,
            FOREIGN KEY (analysis_id) REFERENCES analyses (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, text, analysis_type, results, source=None, confidence_score=None):
        """Save a text analysis result to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO analyses (text, analysis_type, results, source, confidence_score)
        VALUES (?, ?, ?, ?, ?)
        ''', (text, analysis_type, json.dumps(results), source, confidence_score))
        
        analysis_id = cursor.lastrowid
        
        # If results contain claims, save them separately
        if 'claims' in results:
            for claim in results['claims']:
                cursor.execute('''
                INSERT INTO claims (analysis_id, claim_text, verification_status, 
                                  verification_source, confidence_score)
                VALUES (?, ?, ?, ?, ?)
                ''', (analysis_id, claim['text'], claim.get('status'),
                     claim.get('source'), claim.get('confidence')))
        
        conn.commit()
        conn.close()
        return analysis_id
    
    def get_analysis(self, analysis_id):
        """Retrieve a specific analysis by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM analyses WHERE id = ?
        ''', (analysis_id,))
        
        analysis = cursor.fetchone()
        
        if analysis:
            # Get associated claims
            cursor.execute('''
            SELECT * FROM claims WHERE analysis_id = ?
            ''', (analysis_id,))
            
            claims = cursor.fetchall()
            
            result = {
                'id': analysis[0],
                'text': analysis[1],
                'analysis_type': analysis[2],
                'results': json.loads(analysis[3]),
                'created_at': analysis[4],
                'source': analysis[5],
                'confidence_score': analysis[6],
                'claims': [{
                    'id': claim[0],
                    'text': claim[2],
                    'status': claim[3],
                    'source': claim[4],
                    'confidence': claim[5]
                } for claim in claims]
            }
        else:
            result = None
        
        conn.close()
        return result
    
    def get_recent_analyses(self, limit=10):
        """Get the most recent analyses."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        
        analyses = cursor.fetchall()
        
        result = [{
            'id': analysis[0],
            'text': analysis[1],
            'analysis_type': analysis[2],
            'results': json.loads(analysis[3]),
            'created_at': analysis[4],
            'source': analysis[5],
            'confidence_score': analysis[6]
        } for analysis in analyses]
        
        conn.close()
        return result 