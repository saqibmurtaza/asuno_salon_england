import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models.session_models import SessionHistory

class PostgresSessionStore:
    """
    A session store that uses a PostgreSQL database to persist agent session history.
    """
    def __init__(self, session_id: str, db: AsyncSession):
        self.session_id = session_id
        self.db = db
        self.history: List[Dict[str, Any]] = []

    async def load_or_create(self):
        """
        Loads the session history from the database. If no session exists,
        it creates a new one and saves it.
        """
        stmt = select(SessionHistory).where(SessionHistory.session_id == self.session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            self.history = session.history
        else:
            self.history = []
            new_session = SessionHistory(session_id=self.session_id, history=self.history)
            self.db.add(new_session)
            await self.db.commit()

    async def save(self):
        """
        Saves the current session history back to the database.
        """
        stmt = select(SessionHistory).where(SessionHistory.session_id == self.session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            session.history = self.history
            await self.db.commit()
        else:
            new_session = SessionHistory(session_id=self.session_id, history=self.history)
            self.db.add(new_session)
            await self.db.commit()

    def add_message(self, message: Dict[str, Any]):
        """
        Adds a single message to the in-memory history.
        """
        self.history.append(message)

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """
        Returns the list of messages.
        """
        return self.history

    async def get_items(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieves the list of messages.
        """
        return self.history

    async def add_items(self, items: List[Dict[str, Any]]):
        """
        Adds multiple items/messages to the in-memory history.
        This method is required by the 'agents' Runner.
        """
        self.history.extend(items)
