# app/api/routes/jobs.py
from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["Jobs"])