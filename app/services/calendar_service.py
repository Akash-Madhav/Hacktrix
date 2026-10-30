from datetime import datetime, date, timedelta
from typing import List, Set, Optional
from sqlalchemy.orm import Session
from app.models.sla import Holiday

# Pre-defined gazetted national and regional holidays for 2026
DEFAULT_HOLIDAYS_2026 = [
    ("2026-01-26", "Republic Day", "ALL"),
    ("2026-03-04", "Holi", "ALL"),
    ("2026-03-21", "Eid-ul-Fitr", "ALL"),
    ("2026-04-03", "Good Friday", "ALL"),
    ("2026-04-14", "Dr. Ambedkar Jayanti", "ALL"),
    ("2026-05-01", "Maharashtra Day / Labour Day", "MH"),
    ("2026-05-27", "Eid-ul-Adha (Bakrid)", "ALL"),
    ("2026-08-15", "Independence Day", "ALL"),
    ("2026-09-04", "Janmashtami", "ALL"),
    ("2026-10-02", "Mahatma Gandhi Jayanti", "ALL"),
    ("2026-10-20", "Dussehra (Maha Navami)", "ALL"),
    ("2026-10-21", "Dussehra (Vijaya Dashami)", "ALL"),
    ("2026-11-01", "Kannada Rajyotsava", "KA"),
    ("2026-11-09", "Diwali (Lakshmi Puja)", "ALL"),
    ("2026-11-10", "Diwali (Govardhan Puja)", "ALL"),
    ("2026-11-24", "Guru Nanak Jayanti", "ALL"),
    ("2026-12-25", "Christmas Day", "ALL"),
]

class CalendarService:
    @staticmethod
    def ensure_default_holidays(db: Session, year: int = 2026):
        count = db.query(Holiday).filter(Holiday.year == year).count()
        if count == 0:
            for h_date, h_name, state in DEFAULT_HOLIDAYS_2026:
                adjusted_date = f"{year}{h_date[4:]}"
                h = Holiday(
                    id=f"hol-{year}-{h_date[5:]}-{state.lower()}",
                    holiday_date=adjusted_date,
                    name=h_name,
                    state_code=state,
                    year=year
                )
                db.add(h)
            db.commit()

    @staticmethod
    def get_holiday_dates(db: Session, year: int, state_code: str = "ALL") -> Set[str]:
        CalendarService.ensure_default_holidays(db, year)
        query = db.query(Holiday.holiday_date).filter(
            Holiday.year == year,
            (Holiday.state_code == "ALL") | (Holiday.state_code == state_code)
        )
        return {r[0] for r in query.all()}

    @staticmethod
    def is_working_day(check_date: date, holidays: Set[str]) -> bool:
        # Weekend check: Saturday (5) or Sunday (6)
        if check_date.weekday() >= 5:
            return False
        # Holiday check
        if check_date.strftime("%Y-%m-%d") in holidays:
            return False
        return True

    @staticmethod
    def add_working_days(db: Session, start_datetime: datetime, working_days: int, state_code: str = "ALL") -> datetime:
        """Computes the target datetime by adding N working days, accounting for weekends and state holidays."""
        current_date = start_datetime.date()
        year = current_date.year
        holidays = CalendarService.get_holiday_dates(db, year, state_code)
        
        days_added = 0
        while days_added < working_days:
            current_date += timedelta(days=1)
            # Fetch holidays for next year if we cross the calendar boundary
            if current_date.year != year:
                year = current_date.year
                holidays = CalendarService.get_holiday_dates(db, year, state_code)
            
            if CalendarService.is_working_day(current_date, holidays):
                days_added += 1

        # Preserve the original hour/minute
        return datetime.combine(current_date, start_datetime.time())

    @staticmethod
    def count_working_days(db: Session, start_datetime: datetime, end_datetime: datetime, state_code: str = "ALL") -> int:
        """Counts elapsed working days between two datetimes."""
        if start_datetime >= end_datetime:
            return 0
        
        start_date = start_datetime.date()
        end_date = end_datetime.date()
        year = start_date.year
        holidays = CalendarService.get_holiday_dates(db, year, state_code)
        
        working_days = 0
        cur = start_date + timedelta(days=1)
        while cur <= end_date:
            if cur.year != year:
                year = cur.year
                holidays = CalendarService.get_holiday_dates(db, year, state_code)
            if CalendarService.is_working_day(cur, holidays):
                working_days += 1
            cur += timedelta(days=1)
            
        return working_days

calendar_service = CalendarService()
