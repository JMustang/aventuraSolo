import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session

from db.database import get_db
from models.job import StoryJob
from schemas.job import StoryJobResponse

router = APIRouter(prefix='/jobs', tags=['Jobs'])

@router.get('/{job_id}', response_model=StoryJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    