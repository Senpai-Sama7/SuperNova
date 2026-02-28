"""User preferences API routes for controlling power, speed, and risk."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from supernova.api.auth import get_current_user

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    dependencies=[Depends(get_current_user)],
)
