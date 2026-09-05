# tasks.py
from celery import shared_task
from . import retrain_herbert, retrain_xgboost, rag_add_note, rebuild_rag_index
from ..models import TrainingJob
from django.utils import timezone

def _finish(job: TrainingJob, status: str, log: str):
    job.status = status
    job.log = (job.log or "") + f"\n{log}"
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "log", "finished_at"])

@shared_task
def task_rag_add_note(job_id: int, title: str, text: str, file_path: str | None):
    job = TrainingJob.objects.get(id=job_id)
    job.status = "running"; job.started_at = timezone.now(); job.save(update_fields=["status","started_at"])
    try:
        log = rag_add_note(title, text, file_path)
        _finish(job, "succeeded", log)
    except Exception as e:
        _finish(job, "failed", str(e))

@shared_task
def task_retrain(job_id: int):
    job = TrainingJob.objects.get(id=job_id)
    job.status = "running"; job.started_at = timezone.now(); job.save(update_fields=["status","started_at"])
    try:
        if job.model_name == "herbert":
            log = retrain_herbert(job.params or {})
        elif job.model_name == "xgboost":
            log = retrain_xgboost(job.params or {})
        elif job.model_name == "rag_index":
            log = rebuild_rag_index()
        else:
            raise ValueError("Nieznany model")
        _finish(job, "succeeded", log)
    except Exception as e:
        _finish(job, "failed", str(e))
