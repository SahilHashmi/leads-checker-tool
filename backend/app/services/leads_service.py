import os
import uuid
import re
from datetime import datetime
from typing import List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models.schemas import TaskStatus, TaskResponse, FreshLeadResponse
from ..core.config import settings


class LeadsService:
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email: lowercase and trim whitespace."""
        return email.lower().strip()
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Basic email validation - allows special characters that exist in leaked databases."""
        # More permissive pattern to match emails in VPS databases
        # Allows: letters, numbers, and special chars like !._%+- in local part
        pattern = r'^[^\s@]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def parse_emails_from_file(content: str) -> List[str]:
        """Parse emails from file content, one per line."""
        emails = []
        for line in content.splitlines():
            email = LeadsService.normalize_email(line)
            if email and LeadsService.is_valid_email(email):
                emails.append(email)
        return list(set(emails))  # Remove duplicates
    
    @staticmethod
    async def create_task(
        db: AsyncIOMotorDatabase,
        filename: str,
        total_emails: int
    ) -> str:
        """Create a new processing task."""
        task_id = str(uuid.uuid4())
        
        document = {
            "task_id": task_id,
            "status": TaskStatus.PENDING.value,
            "filename": filename,
            "total_emails": total_emails,
            "processed_emails": 0,
            "leaked_count": 0,
            "fresh_count": 0,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        await db.tasks.insert_one(document)
        return task_id
    
    @staticmethod
    async def get_task(db: AsyncIOMotorDatabase, task_id: str) -> Optional[TaskResponse]:
        """Get task by ID."""
        doc = await db.tasks.find_one({"task_id": task_id})
        
        if doc:
            return TaskResponse(
                task_id=doc["task_id"],
                status=TaskStatus(doc["status"]),
                filename=doc["filename"],
                total_emails=doc["total_emails"],
                processed_emails=doc["processed_emails"],
                leaked_count=doc["leaked_count"],
                fresh_count=doc["fresh_count"],
                created_at=doc["created_at"],
                completed_at=doc.get("completed_at"),
                error_message=doc.get("error_message")
            )
        return None
    
    @staticmethod
    async def update_task_status(
        db: AsyncIOMotorDatabase,
        task_id: str,
        status: TaskStatus,
        processed_emails: int = None,
        leaked_count: int = None,
        fresh_count: int = None,
        error_message: str = None
    ):
        """Update task status and progress."""
        update_data = {"status": status.value}
        
        if processed_emails is not None:
            update_data["processed_emails"] = processed_emails
        if leaked_count is not None:
            update_data["leaked_count"] = leaked_count
        if fresh_count is not None:
            update_data["fresh_count"] = fresh_count
        if error_message is not None:
            update_data["error_message"] = error_message
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            update_data["completed_at"] = datetime.utcnow()
        
        await db.tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
    
    @staticmethod
    async def save_fresh_lead(
        db: AsyncIOMotorDatabase,
        email: str,
        source: str,
        task_id: str
    ):
        """Save a fresh (non-leaked) lead."""
        document = {
            "email": email,
            "source": source,
            "task_id": task_id,
            "created_at": datetime.utcnow()
        }
        
        await db.fresh_leads.insert_one(document)
    
    @staticmethod
    async def save_fresh_leads_bulk(
        db: AsyncIOMotorDatabase,
        emails: List[str],
        source: str,
        task_id: str
    ):
        """Save multiple fresh leads in bulk."""
        if not emails:
            return
        
        documents = [
            {
                "email": email,
                "source": source,
                "task_id": task_id,
                "created_at": datetime.utcnow()
            }
            for email in emails
        ]
        
        await db.fresh_leads.insert_many(documents)
    
    @staticmethod
    async def get_fresh_leads_by_task(
        db: AsyncIOMotorDatabase,
        task_id: str
    ) -> List[str]:
        """Get all fresh leads for a specific task."""
        cursor = db.fresh_leads.find({"task_id": task_id})
        emails = []
        
        async for doc in cursor:
            emails.append(doc["email"])
        
        return emails
    
    @staticmethod
    async def get_fresh_leads_by_date_range(
        db: AsyncIOMotorDatabase,
        from_date: datetime,
        to_date: datetime
    ) -> List[str]:
        """Get fresh leads within a date range."""
        cursor = db.fresh_leads.find({
            "created_at": {
                "$gte": from_date,
                "$lte": to_date
            }
        }).sort("created_at", 1)
        
        emails = []
        async for doc in cursor:
            emails.append(doc["email"])
        
        return emails
    
    @staticmethod
    def save_result_file(task_id: str, emails: List[str]) -> str:
        """Save result emails to a file."""
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        
        filename = f"result_{task_id}.txt"
        filepath = os.path.join(settings.RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for email in emails:
                f.write(f"{email}\n")
        
        return filepath
    
    @staticmethod
    def get_result_file_path(task_id: str) -> Optional[str]:
        """Get the path to a result file."""
        filename = f"result_{task_id}.txt"
        filepath = os.path.join(settings.RESULTS_DIR, filename)
        
        if os.path.exists(filepath):
            return filepath
        return None
