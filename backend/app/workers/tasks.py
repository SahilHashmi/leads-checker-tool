import asyncio
from typing import List
from celery import current_task
from motor.motor_asyncio import AsyncIOMotorClient
from .celery_app import celery_app
from ..core.config import settings
from ..models.schemas import TaskStatus
from ..services.email_checker_service import EmailCheckerService
from ..services.leads_service import LeadsService
from ..core.logger import worker_logger


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
    worker_logger.info(f"Starting task {task_id}: Processing {len(emails)} emails from {filename}")
    try:
        result = run_async(_process_leads_async(task_id, emails, filename, self))
        worker_logger.info(f"Task {task_id} completed successfully: {result}")
        return result
    except Exception as e:
        worker_logger.error(f"Task {task_id} failed: {type(e).__name__}: {str(e)}")
        worker_logger.exception("Full traceback:")
        # Update task as failed
        run_async(_update_task_failed(task_id, str(e)))
        raise


async def _process_leads_async(task_id: str, emails: List[str], filename: str, celery_task):
    """Async implementation of leads processing."""
    
    worker_logger.info(f"Task {task_id}: Connecting to main database at {settings.MONGODB_URL}")
    
    # Connect to main database
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        # Test connection
        await asyncio.wait_for(client.admin.command('ping'), timeout=10.0)
        db = client[settings.MONGODB_DATABASE]
        worker_logger.info(f"Task {task_id}: Successfully connected to main database")
    except Exception as e:
        worker_logger.error(f"Task {task_id}: Failed to connect to main database: {type(e).__name__}: {str(e)}")
        raise
    
    # Initialize email checker and connect to external VPS
    worker_logger.info(f"Task {task_id}: Initializing VPS connections for email verification")
    checker = EmailCheckerService()
    await checker.connect_all()
    
    # Check if any VPS databases are connected
    if not checker._databases:
        error_msg = "No VPS databases connected! Cannot verify emails. Please check VPS configuration in .env file."
        worker_logger.error(f"Task {task_id}: {error_msg}")
        await LeadsService.update_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            error_message=error_msg
        )
        client.close()
        raise RuntimeError(error_msg)
    
    try:
        # Update task status to processing
        await LeadsService.update_task_status(db, task_id, TaskStatus.PROCESSING)
        worker_logger.info(f"Task {task_id}: Starting to process {len(emails)} emails")
        
        total_emails = len(emails)
        processed = 0
        leaked_count = 0
        fresh_emails = []
        errors_count = 0
        
        # Process in batches for better performance and progress updates
        batch_size = 50
        
        for i in range(0, total_emails, batch_size):
            batch = emails[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_emails + batch_size - 1) // batch_size
            
            worker_logger.info(f"Task {task_id}: Processing batch {batch_num}/{total_batches} ({len(batch)} emails)")
            
            # Check batch against external databases
            for email in batch:
                try:
                    is_leaked = await checker.check_email_exists(email)
                    
                    if is_leaked:
                        leaked_count += 1
                    else:
                        fresh_emails.append(email)
                    
                    processed += 1
                except Exception as e:
                    worker_logger.error(f"Task {task_id}: Error checking email {email}: {type(e).__name__}: {str(e)}")
                    errors_count += 1
                    processed += 1
                    # Treat errors as fresh to avoid losing data
                    fresh_emails.append(email)
            
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
                    'fresh': len(fresh_emails),
                    'errors': errors_count
                }
            )
            
            worker_logger.info(f"Task {task_id}: Batch {batch_num} complete. Progress: {processed}/{total_emails} ({leaked_count} leaked, {len(fresh_emails)} fresh, {errors_count} errors)")
        
        # Save fresh leads to database
        if fresh_emails:
            worker_logger.info(f"Task {task_id}: Saving {len(fresh_emails)} fresh leads to database")
            await LeadsService.save_fresh_leads_bulk(
                db,
                fresh_emails,
                source=filename,
                task_id=task_id
            )
            worker_logger.info(f"Task {task_id}: Fresh leads saved successfully")
        else:
            worker_logger.info(f"Task {task_id}: No fresh leads to save")
        
        # Generate result file
        worker_logger.info(f"Task {task_id}: Generating result file")
        LeadsService.save_result_file(task_id, fresh_emails)
        worker_logger.info(f"Task {task_id}: Result file generated")
        
        # Update task as completed
        await LeadsService.update_task_status(
            db,
            task_id,
            TaskStatus.COMPLETED,
            processed_emails=total_emails,
            leaked_count=leaked_count,
            fresh_count=len(fresh_emails)
        )
        
        result = {
            'task_id': task_id,
            'total': total_emails,
            'leaked': leaked_count,
            'fresh': len(fresh_emails),
            'errors': errors_count
        }
        
        worker_logger.info(f"Task {task_id}: Processing completed successfully: {result}")
        return result
        
    finally:
        worker_logger.info(f"Task {task_id}: Cleaning up connections")
        checker.close_all()
        client.close()


async def _update_task_failed(task_id: str, error_message: str):
    """Update task status to failed."""
    worker_logger.error(f"Task {task_id}: Marking as FAILED with error: {error_message}")
    
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.MONGODB_DATABASE]
        
        await LeadsService.update_task_status(
            db,
            task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
        
        worker_logger.info(f"Task {task_id}: Status updated to FAILED")
    except Exception as e:
        worker_logger.error(f"Task {task_id}: Failed to update task status: {type(e).__name__}: {str(e)}")
    finally:
        client.close()
