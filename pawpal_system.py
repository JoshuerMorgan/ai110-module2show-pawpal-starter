from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes — simple value objects
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str          # "low" | "medium" | "high"
    notes: str = ""
    is_required: bool = False

    def priority_value(self) -> int:
        """Return a numeric score so tasks can be ranked (higher = more urgent)."""
        pass


@dataclass
class Pet:
    name: str
    species: str           # "dog" | "cat" | "other"
    age_years: float = 0.0
    special_needs: str = ""


@dataclass
class ScheduledTask:
    """A Task that has been placed into a time slot inside a daily plan."""
    task: Task
    start_time: str        # e.g. "08:00"
    reason: str = ""       # why this task was chosen / placed here


# ---------------------------------------------------------------------------
# Regular classes — encapsulate state + behavior
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        pet: Pet,
        available_minutes: int = 120,
        preferences: Optional[dict] = None,
    ):
        self.name = name
        self.pet = pet
        self.available_minutes = available_minutes
        self.preferences: dict = preferences or {}
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a care task to the task list."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
        pass

    def get_tasks_by_priority(self) -> list[Task]:
        """Return tasks sorted highest → lowest priority."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, start_time: str = "08:00"):
        self.owner = owner
        self.start_time = start_time
        self.plan: list[ScheduledTask] = []

    def build_plan(self) -> list[ScheduledTask]:
        """Select and order tasks that fit within available time."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the plan."""
        pass

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled tasks."""
        pass

    def _fits_in_time(self, task: Task) -> bool:
        """Check if adding this task would exceed available time."""
        pass

    def _next_start_time(self) -> str:
        """Compute the wall-clock start for the next slot."""
        pass


class PawPalApp:
    """Top-level coordinator — ties Owner, Pet, and Scheduler together."""

    def __init__(self):
        self.owner: Optional[Owner] = None
        self.scheduler: Optional[Scheduler] = None

    def setup(self, owner_name: str, pet_name: str, species: str, available_minutes: int) -> None:
        """Initialise owner and pet from form values."""
        pass

    def add_task(self, title: str, duration_minutes: int, priority: str, notes: str = "") -> None:
        """Create a Task and hand it to the owner."""
        pass

    def generate_schedule(self) -> list[ScheduledTask]:
        """Run the scheduler and return the plan."""
        pass

    def get_explanation(self) -> str:
        """Return a plain-text explanation of the generated plan."""
        pass
