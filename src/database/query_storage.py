"""
Query Storage - Manage saved queries and history
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config
import json

Base = declarative_base()


class ChatSession(Base):
    """Model for chat sessions"""
    __tablename__ = 'chat_sessions'
    
    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class SavedQuery(Base):
    """Model for saved queries"""
    __tablename__ = 'saved_queries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_question = Column(Text, nullable=False)
    sql_query = Column(Text)
    python_code = Column(Text)
    result_text = Column(Text)
    figure_json = Column(Text)
    execution_time = Column(Float)
    feedback = Column(String(10), default='none')  # 'like', 'dislike', 'none'
    is_saved = Column(Boolean, default=False)
    notes = Column(Text)
    session_id = Column(String(36), nullable=True)  # Link to ChatSession


class QueryStorage:
    """Manages query storage and retrieval"""
    
    def __init__(self, database_url=None):
        """Initialize query storage"""
        db_url = database_url or str(config.DATABASE_URL)
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Migrate existing queries if needed
        self._migrate_legacy_queries()
    
    def _migrate_legacy_queries(self):
        """Assign existing queries to a default session"""
        session = self.Session()
        try:
            # Check if session_id column exists
            inspector = inspect(self.engine)
            columns = [c['name'] for c in inspector.get_columns('saved_queries')]
            
            if 'session_id' not in columns:
                with self.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE saved_queries ADD COLUMN session_id VARCHAR(36)"))
                    conn.commit()
            
            import uuid
            
            # Create default session if none exists
            default_session = session.query(ChatSession).filter_by(name="Legacy Session").first()
            if not default_session:
                default_session = ChatSession(
                    id=str(uuid.uuid4()),
                    name="Legacy Session",
                    created_at=datetime.now()
                )
                session.add(default_session)
                session.commit()
                
            # Assign null session_ids to default session
            with self.engine.connect() as conn:
                conn.execute(
                    text("UPDATE saved_queries SET session_id = :sid WHERE session_id IS NULL"),
                    {"sid": default_session.id}
                )
                conn.commit()
                
        except Exception as e:
            print(f"Migration warning: {e}")
        finally:
            session.close()

    def create_session(self, name="New Chat"):
        """Create a new chat session"""
        import uuid
        session = self.Session()
        try:
            new_session = ChatSession(
                id=str(uuid.uuid4()),
                name=name,
                created_at=datetime.now()
            )
            session.add(new_session)
            session.commit()
            return new_session.id
        finally:
            session.close()

    def get_sessions(self):
        """Get all chat sessions"""
        session = self.Session()
        try:
            sessions = session.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
            return [{'id': s.id, 'name': s.name, 'created_at': s.created_at} for s in sessions]
        finally:
            session.close()
            
    def delete_session(self, session_id):
        """Delete a chat session and its queries"""
        session = self.Session()
        try:
            # Delete queries first
            session.query(SavedQuery).filter(SavedQuery.session_id == session_id).delete()
            # Delete session
            session.query(ChatSession).filter(ChatSession.id == session_id).delete()
            session.commit()
            return True
        finally:
            session.close()

    def rename_session(self, session_id, new_name):
        """Rename a chat session"""
        session = self.Session()
        try:
            chat_session = session.query(ChatSession).filter(ChatSession.id == session_id).first()
            if chat_session:
                chat_session.name = new_name
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def save_query(self, user_question, sql_query=None, python_code=None, 
                   result_text=None, figure_json=None, execution_time=None,
                   is_saved=False, notes=None, session_id=None):
        """Save a query to the database"""
        session = self.Session()
        try:
            query = SavedQuery(
                user_question=user_question,
                sql_query=sql_query,
                python_code=python_code,
                result_text=result_text,
                figure_json=figure_json,
                execution_time=execution_time,
                is_saved=is_saved,
                notes=notes,
                session_id=session_id
            )
            session.add(query)
            session.commit()
            query_id = query.id
            return query_id
        finally:
            session.close()
    
    def get_all_queries(self, limit=100, session_id=None):
        """Get all queries (history), optionally filtered by session"""
        session = self.Session()
        try:
            query = session.query(SavedQuery)
            
            if session_id:
                query = query.filter(SavedQuery.session_id == session_id)
                
            queries = query.order_by(SavedQuery.timestamp.desc())\
                .limit(limit)\
                .all()
            return [self._query_to_dict(q) for q in queries]
        finally:
            session.close()
    
    def get_saved_queries(self):
        """Get only saved queries"""
        session = self.Session()
        try:
            queries = session.query(SavedQuery)\
                .filter(SavedQuery.is_saved == True)\
                .order_by(SavedQuery.timestamp.desc())\
                .all()
            return [self._query_to_dict(q) for q in queries]
        finally:
            session.close()
    
    def update_feedback(self, query_id, feedback):
        """Update feedback for a query"""
        session = self.Session()
        try:
            query = session.query(SavedQuery).filter(SavedQuery.id == query_id).first()
            if query:
                query.feedback = feedback
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def mark_as_saved(self, query_id, notes=None):
        """Mark a query as saved"""
        session = self.Session()
        try:
            query = session.query(SavedQuery).filter(SavedQuery.id == query_id).first()
            if query:
                query.is_saved = True
                if notes:
                    query.notes = notes
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def delete_query(self, query_id):
        """Delete a saved query"""
        session = self.Session()
        try:
            query = session.query(SavedQuery).filter(SavedQuery.id == query_id).first()
            if query:
                session.delete(query)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        session = self.Session()
        try:
            total_queries = session.query(SavedQuery).count()
            
            # Average execution time
            avg_time_result = session.query(SavedQuery.execution_time).all()
            avg_time = sum([r[0] for r in avg_time_result if r[0]]) / len(avg_time_result) if avg_time_result else 0
            
            # Feedback counts
            likes = session.query(SavedQuery).filter(SavedQuery.feedback == 'like').count()
            dislikes = session.query(SavedQuery).filter(SavedQuery.feedback == 'dislike').count()
            
            # Saved queries count
            saved_count = session.query(SavedQuery).filter(SavedQuery.is_saved == True).count()
            
            return {
                'total_queries': total_queries,
                'avg_execution_time': avg_time,
                'likes': likes,
                'dislikes': dislikes,
                'saved_count': saved_count,
                'satisfaction_rate': (likes / (likes + dislikes) * 100) if (likes + dislikes) > 0 else 0
            }
        finally:
            session.close()
    
    def get_queries_by_ids(self, query_ids):
        """Get multiple queries by their IDs"""
        session = self.Session()
        try:
            queries = session.query(SavedQuery)\
                .filter(SavedQuery.id.in_(query_ids))\
                .all()
            return [self._query_to_dict(q) for q in queries]
        finally:
            session.close()
    
    def _query_to_dict(self, query):
        """Convert query object to dictionary"""
        return {
            'id': query.id,
            'timestamp': query.timestamp,
            'user_question': query.user_question,
            'sql_query': query.sql_query,
            'python_code': query.python_code,
            'result_text': query.result_text,
            'figure_json': query.figure_json,
            'execution_time': query.execution_time,
            'feedback': query.feedback,
            'is_saved': query.is_saved,
            'notes': query.notes,
            'session_id': query.session_id
        }
