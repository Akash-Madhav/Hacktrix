from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.system import SystemClock

DEFAULT_CLOCK_ID = "niriksha-system-clock"

class ClockService:
    @staticmethod
    def get_clock(db: Session) -> SystemClock:
        clock = db.query(SystemClock).filter(SystemClock.id == DEFAULT_CLOCK_ID).first()
        if not clock:
            clock = SystemClock(
                id=DEFAULT_CLOCK_ID,
                simulated_now=datetime.utcnow(),
                speed_multiplier=1.0,
                is_paused=False
            )
            db.add(clock)
            db.commit()
            db.refresh(clock)
        return clock

    @staticmethod
    def now(db: Session) -> datetime:
        """Returns the current simulated application time."""
        clock = ClockService.get_clock(db)
        return clock.simulated_now

    @staticmethod
    def advance_time(db: Session, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
        """Advances the simulated clock by specified offset and triggers dependent recalculations."""
        clock = ClockService.get_clock(db)
        delta = timedelta(days=days, hours=hours, minutes=minutes)
        clock.simulated_now = clock.simulated_now + delta
        clock.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(clock)
        return clock.simulated_now

    @staticmethod
    def set_time(db: Session, target_time: datetime) -> datetime:
        clock = ClockService.get_clock(db)
        clock.simulated_now = target_time
        clock.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(clock)
        return clock.simulated_now

    @staticmethod
    def reset_to_real_time(db: Session) -> datetime:
        clock = ClockService.get_clock(db)
        clock.simulated_now = datetime.utcnow()
        clock.speed_multiplier = 1.0
        clock.is_paused = False
        clock.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(clock)
        return clock.simulated_now

clock_service = ClockService()
