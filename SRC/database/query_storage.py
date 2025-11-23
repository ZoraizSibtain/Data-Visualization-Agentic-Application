from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import uuid
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

Base = declarative_base()


class ChatSession(Base):
    __tablename__ = '_chat_sessions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    queries = relationship("SavedQuery", back_populates="session", cascade="all, delete-orphan")


class SavedQuery(Base):
    __tablename__ = '_saved_queries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_question = Column(Text)
    sql_query = Column(Text)
    python_code = Column(Text)
    result_text = Column(Text)
    figure_json = Column(Text)
    execution_time = Column(Float)
    feedback = Column(String(20), default='none')  # 'like', 'dislike', 'none'
    is_saved = Column(Boolean, default=False)
    notes = Column(Text)
    session_id = Column(String(36), ForeignKey('_chat_sessions.id'))

    session = relationship("ChatSession", back_populates="queries")


class QueryStorage:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    # Session management
    def create_session(self, name: str = "New Chat") -> str:
        """Create a new chat session."""
        chat_session = ChatSession(name=name)
        self.session.add(chat_session)
        self.session.commit()
        return chat_session.id

    def get_sessions(self) -> list:
        """Get all chat sessions ordered by creation date."""
        sessions = self.session.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
        return [{'id': s.id, 'name': s.name, 'created_at': s.created_at} for s in sessions]

    def delete_session(self, session_id: str):
        """Delete a chat session and all its queries."""
        chat_session = self.session.query(ChatSession).filter_by(id=session_id).first()
        if chat_session:
            self.session.delete(chat_session)
            self.session.commit()

    def rename_session(self, session_id: str, new_name: str):
        """Rename a chat session."""
        chat_session = self.session.query(ChatSession).filter_by(id=session_id).first()
        if chat_session:
            chat_session.name = new_name
            self.session.commit()

    # Query management
    def save_query(self, session_id: str, user_question: str, sql_query: str = None,
                   python_code: str = None, result_text: str = None,
                   figure_json: str = None, execution_time: float = None) -> int:
        """Save a query to the database."""
        query = SavedQuery(
            session_id=session_id,
            user_question=user_question,
            sql_query=sql_query,
            python_code=python_code,
            result_text=result_text,
            figure_json=figure_json,
            execution_time=execution_time
        )
        self.session.add(query)
        self.session.commit()
        return query.id

    def get_all_queries(self, session_id: str = None, limit: int = 100,
                        search: str = None, time_range: str = None) -> list:
        """Get all queries with optional filters."""
        query = self.session.query(SavedQuery)

        if session_id:
            query = query.filter(SavedQuery.session_id == session_id)

        if search:
            query = query.filter(SavedQuery.user_question.ilike(f'%{search}%'))

        if time_range:
            now = datetime.utcnow()
            if time_range == '24h':
                cutoff = now - timedelta(hours=24)
            elif time_range == '7d':
                cutoff = now - timedelta(days=7)
            elif time_range == '30d':
                cutoff = now - timedelta(days=30)
            else:
                cutoff = None

            if cutoff:
                query = query.filter(SavedQuery.timestamp >= cutoff)

        queries = query.order_by(SavedQuery.timestamp.desc()).limit(limit).all()

        return [self._query_to_dict(q) for q in queries]

    def get_saved_queries(self) -> list:
        """Get only queries marked as saved."""
        queries = (self.session.query(SavedQuery)
                   .filter(SavedQuery.is_saved == True)
                   .order_by(SavedQuery.timestamp.desc())
                   .all())
        return [self._query_to_dict(q) for q in queries]

    def get_session_queries(self, session_id: str) -> list:
        """Get all queries for a specific session."""
        queries = (self.session.query(SavedQuery)
                   .filter(SavedQuery.session_id == session_id)
                   .order_by(SavedQuery.timestamp.asc())
                   .all())
        return [self._query_to_dict(q) for q in queries]

    def update_feedback(self, query_id: int, feedback: str):
        """Update feedback for a query."""
        query = self.session.query(SavedQuery).filter_by(id=query_id).first()
        if query:
            query.feedback = feedback
            self.session.commit()

    def mark_as_saved(self, query_id: int, is_saved: bool = True):
        """Mark or unmark a query as saved."""
        query = self.session.query(SavedQuery).filter_by(id=query_id).first()
        if query:
            query.is_saved = is_saved
            self.session.commit()

    def update_notes(self, query_id: int, notes: str):
        """Update notes for a query."""
        query = self.session.query(SavedQuery).filter_by(id=query_id).first()
        if query:
            query.notes = notes
            self.session.commit()

    def delete_query(self, query_id: int):
        """Delete a query."""
        query = self.session.query(SavedQuery).filter_by(id=query_id).first()
        if query:
            self.session.delete(query)
            self.session.commit()

    def get_performance_metrics(self) -> dict:
        """Get performance metrics for all queries."""
        from sqlalchemy import func

        total = self.session.query(func.count(SavedQuery.id)).scalar() or 0
        avg_time = self.session.query(func.avg(SavedQuery.execution_time)).scalar() or 0
        likes = self.session.query(func.count(SavedQuery.id)).filter(
            SavedQuery.feedback == 'like').scalar() or 0
        dislikes = self.session.query(func.count(SavedQuery.id)).filter(
            SavedQuery.feedback == 'dislike').scalar() or 0
        saved_count = self.session.query(func.count(SavedQuery.id)).filter(
            SavedQuery.is_saved == True).scalar() or 0

        feedback_total = likes + dislikes
        satisfaction_rate = (likes / feedback_total * 100) if feedback_total > 0 else 0

        return {
            'total_queries': total,
            'avg_execution_time': round(avg_time, 2),
            'likes': likes,
            'dislikes': dislikes,
            'satisfaction_rate': round(satisfaction_rate, 1),
            'saved_count': saved_count
        }

    def _query_to_dict(self, query: SavedQuery) -> dict:
        """Convert SavedQuery object to dictionary."""
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

    def close(self):
        """Close the database session."""
        self.session.close()
