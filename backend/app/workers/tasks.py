import asyncio
from typing import List
from celery import current_task
from motor.motor_asyncio import AsyncIOMotorClient
from .celery_app import celery_app
from ..core.config import settings
from ..models.schemas import TaskStatus
from ..services.email_checker_service import EmailCheckerService
from ..services.leads_service import LeadsService


def get_sync_db():
    """Get synchronous database connection for Celery workers."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DATABASE]


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_leads_task(self, task_id: str, emails: List[str], filename: str):
    """
    Process uploaded leads:
    1. Check each email against external VPS databases
    2. Filter out leaked emails
    3. Save fresh emails to database
    4. Generate result file
    """
    try:
        run_async(_process_leads_async(task_id, emails, filename, self))
    except Exception as e:
        # Update task as failed
        run_async(_update_task_failed(task_id, str(e)))
        raise


async def _process_leads_async(task_id: str, emails: List[str], filename: str, celery_task):
    """Async implementation of leads processing."""
    
    # Connect to main database
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Initialize email checker and connect to external VPS
    checker = EmailCheckerService()
    await checker.connect_all()
    
    try:
        # Update task status to processing
        await LeadsService.update_task_status(db, task_id, TaskStatus.PROCESSING)
        
        total_emails = len(emails)
        processed = 0
        leaked_count = 0
        fresh_emails = []
        
        # Process in batches for better performance and progress updates
        batch_size = 50
        
        for i in range(0, total_emails, batch_size):
            batch = emails[i:i + batch_size]
            
            # Check batch against external databases
            for email in batch:
                is_leaked = await checker.check_email_exists(email)
                
                if is_leaked:
                    leaked_count += 1
                else:
                    fresh_emails.append(email)
                
                processed += 1
            
            # Update progress
            await LeadsService.update_task_status(
                db,
                task_id,
                TaskStatus.PROCESSING,
                processed_emails=processed,
                leaked_count=leaked_count,
                fresh_count=len(fresh_emails)
            )
            
            # Update Celery task state for monitoring
            celery_task.update_state(
                state='PROGRESS',
                meta={
                    'current': processed,
                    'total': total_emails,
                    'leaked': leaked_count,
                    'fresh': len(fresh_emails)
                }
            )
        
        # Save fresh leads to database
        if fresh_emails:
            await LeadsService.save_fresh_leads_bulk(
                db,
                fresh_emails,
                source=filename,
                task_id=task_id
            )
        
        # Generate result file
        LeadsService.save_result_file(task_id, fresh_emails)
        
        # Update task as completed
        await LeadsService.update_task_status(
            db,
            task_id,
            TaskStatus.COMPLETED,
            processed_emails=total_emails,
            leaked_count=leaked_count,
            fresh_count=len(fresh_emails)
        )
        
        return {
            'task_id': task_id,
            'total': total_emails,
            'leaked': leaked_count,
            'fresh': len(fresh_emails)
        }
        
    finally:
        checker.close_all()
        client.close()


async def _update_task_failed(task_id: str, error_message: str):
    """Update task status to failed."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    try:
        await LeadsService.update_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
    finally:
        client.close()
