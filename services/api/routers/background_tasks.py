from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import logging

from ..models.extraction_models import ExtractionJob, ExtractionResult
from ..services.extraction_service import ExtractionService
from ..core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize extraction service
extraction_service = ExtractionService()

@router.post("/extraction/start/{conversation_id}/{child_id}")
async def start_extraction_job(
    conversation_id: str,
    child_id: str,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Start a background extraction job for a conversation"""
    try:
        # Get conversation messages from database
        conversation_messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).to_list(length=None)

        if not conversation_messages:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found for conversation {conversation_id}"
            )

        # Create extraction job
        job_id = extraction_service.create_extraction_job(conversation_id, child_id)

        # Add background task
        background_tasks.add_task(
            extraction_service.process_extraction_job,
            job_id,
            conversation_id,
            child_id,
            conversation_messages
        )

        return {
            "job_id": job_id,
            "conversation_id": conversation_id,
            "status": "started",
            "message_count": len(conversation_messages)
        }

    except Exception as e:
        logger.error(f"Error starting extraction job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/extraction/status/{job_id}")
async def get_extraction_status(job_id: str) -> ExtractionJob:
    """Get status of an extraction job"""
    job = extraction_service.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction job {job_id} not found"
        )

    return job

@router.get("/extraction/results/{job_id}")
async def get_extraction_results(job_id: str) -> ExtractionResult:
    """Get results of a completed extraction job"""
    job = extraction_service.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction job {job_id} not found"
        )

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Extraction job {job_id} is not completed. Current status: {job.status}"
        )

    if not job.result:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for completed job {job_id}"
        )

    return job.result

@router.get("/extraction/jobs")
async def list_extraction_jobs() -> List[ExtractionJob]:
    """List all extraction jobs"""
    return list(extraction_service.active_jobs.values())

@router.delete("/extraction/jobs/{job_id}")
async def cleanup_extraction_job(job_id: str):
    """Clean up a completed or failed extraction job"""
    job = extraction_service.get_job_status(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction job {job_id} not found"
        )

    if job.status in ["pending", "processing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cleanup job {job_id} with status {job.status}"
        )

    # Remove from active jobs
    del extraction_service.active_jobs[job_id]

    return {
        "job_id": job_id,
        "status": "cleaned_up",
        "message": f"Job {job_id} has been cleaned up"
    }

@router.get("/extraction/stats")
async def get_extraction_stats() -> Dict[str, Any]:
    """Get statistics about extraction jobs"""
    jobs = list(extraction_service.active_jobs.values())

    stats = {
        "total_jobs": len(jobs),
        "pending_jobs": len([j for j in jobs if j.status == "pending"]),
        "processing_jobs": len([j for j in jobs if j.status == "processing"]),
        "completed_jobs": len([j for j in jobs if j.status == "completed"]),
        "failed_jobs": len([j for j in jobs if j.status == "failed"]),
        "jobs_with_validation_errors": len([
            j for j in jobs
            if j.validation_report and not j.validation_report.valid
        ])
    }

    # Calculate average processing time for completed jobs
    completed_jobs = [j for j in jobs if j.status == "completed" and j.result]
    if completed_jobs:
        avg_processing_time = sum(
            j.result.processing_time_ms for j in completed_jobs
        ) / len(completed_jobs)
        stats["average_processing_time_ms"] = round(avg_processing_time, 2)

        # Entity and relationship counts
        total_entities = sum(len(j.result.entities) for j in completed_jobs)
        total_relationships = sum(len(j.result.relationships) for j in completed_jobs)

        stats.update({
            "total_entities_extracted": total_entities,
            "total_relationships_extracted": total_relationships,
            "average_entities_per_conversation": round(total_entities / len(completed_jobs), 2),
            "average_relationships_per_conversation": round(total_relationships / len(completed_jobs), 2)
        })

    return stats