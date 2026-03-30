from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums & value types
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"


@dataclass
class Preferences:
    preferred_walk_time: str = "morning"   # "morning" | "afternoon" | "evening"
    max_tasks_per_day: int = 10
    skip_grooming: bool = False


# ---------------------------------------------------------------------------
# Task — a single care activity
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    frequency: Frequency = Frequency.DAILY
    completed: bool = False
    notes: str = ""
    is_required: bool = False

    def __post_init__(self):
        """Validate that priority and frequency are the correct enum types."""
        if not isinstance(self.priority, Priority):
            raise ValueError(f"priority must be a Priority enum, got: {self.priority!r}")
        if not isinstance(self.frequency, Frequency):
            raise ValueError(f"frequency must be a Frequency enum, got: {self.frequency!r}")

    def priority_value(self) -> int:
        """Return numeric priority score (higher = more urgent)."""
        return self.priority.value

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion status (e.g. start of a new day)."""
        self.completed = False


# ---------------------------------------------------------------------------
# Pet — stores pet details and owns its task list
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str                          # "dog" | "cat" | "other"
    age_years: float = 0.0
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title. Does nothing if not found."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def get_tasks_by_priority(self) -> list[Task]:
        """Return all tasks sorted highest → lowest priority."""
        return sorted(self.tasks, key=lambda t: t.priority_value(), reverse=True)

    def requires_outdoor_tasks(self) -> bool:
        """Dogs need outdoor activity; cats and others typically do not."""
        return self.species.lower() == "dog"


# ---------------------------------------------------------------------------
# ScheduledTask — a Task placed into a time slot
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    """A Task that has been assigned a specific time slot in the daily plan."""
    task: Task
    pet: Pet
    start_time: str        # e.g. "08:00"
    end_time: str = ""     # computed: start_time + task.duration_minutes
    reason: str = ""       # plain-English explanation of why this was scheduled


# ---------------------------------------------------------------------------
# Owner — manages multiple pets
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int = 120,
        preferences: Optional[Preferences] = None,
    ):
        """Create an owner with a daily time budget and optional care preferences."""
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: Preferences = preferences or Preferences()
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name. Does nothing if not found."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return only incomplete (pet, task) pairs across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]


# ---------------------------------------------------------------------------
# Scheduler — the "brain" that builds and explains a daily plan
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, start_time: str = "08:00"):
        """Bind the scheduler to an owner and set the day's wall-clock start time."""
        self.owner = owner
        self.start_time = start_time
        self.plan: list[ScheduledTask] = []

    # -- public methods ------------------------------------------------------

    def build_plan(self) -> list[ScheduledTask]:
        """
        Build a daily schedule across all of the owner's pets.

        Rules applied in order:
        1. Reset the plan so repeated calls don't accumulate duplicates.
        2. Always include required tasks even if they exceed available_minutes.
        3. Skip tasks already marked completed.
        4. Skip outdoor/walk tasks for pets that don't require them.
        5. Respect owner's skip_grooming preference.
        6. Fill remaining time with optional tasks sorted by priority (highest first).
        7. Stop once available_minutes is consumed.
        """
        self.plan = []
        pending = self.owner.get_all_pending_tasks()

        # Separate required from optional
        required = [(pet, task) for pet, task in pending if task.is_required]
        optional = [(pet, task) for pet, task in pending if not task.is_required]

        # Always schedule required tasks first
        for pet, task in required:
            self._schedule(pet, task, required=True)

        # Fill remaining time with optional tasks, highest priority first
        optional_sorted = sorted(optional, key=lambda pt: pt[1].priority_value(), reverse=True)
        for pet, task in optional_sorted:
            if self._should_skip(pet, task):
                continue
            if not self._fits_in_time(task):
                break
            self._schedule(pet, task, required=False)

        return self.plan

    def explain_plan(self) -> str:
        """Return a human-readable summary of the scheduled plan."""
        if not self.plan:
            return "No tasks have been scheduled yet. Run build_plan() first."

        lines = [f"Daily plan for {self.owner.name} ({self.total_scheduled_minutes()} min total)\n"]
        for i, st in enumerate(self.plan, start=1):
            lines.append(
                f"{i}. [{st.start_time}–{st.end_time}] {st.pet.name}: {st.task.title} "
                f"({st.task.duration_minutes} min, {st.task.priority.name}) — {st.reason}"
            )

        remaining = self.owner.available_minutes - self.total_scheduled_minutes()
        lines.append(f"\n{remaining} min of available time unused.")
        return "\n".join(lines)

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all tasks currently in the plan."""
        return sum(st.task.duration_minutes for st in self.plan)

    # -- private helpers -----------------------------------------------------

    def _schedule(self, pet: Pet, task: Task, required: bool) -> None:
        """Create a ScheduledTask entry and append it to the plan."""
        start = self._next_start_time()
        end = self._minutes_to_time_str(
            self._time_str_to_minutes(start) + task.duration_minutes
        )
        reason = "required task — always included" if required else (
            f"priority {task.priority.name.lower()}, fits within available time"
        )
        self.plan.append(ScheduledTask(task=task, pet=pet, start_time=start, end_time=end, reason=reason))

    def _should_skip(self, pet: Pet, task: Task) -> bool:
        """Return True if this task should be excluded based on pet or owner preferences."""
        prefs = self.owner.preferences

        # Skip grooming tasks if the owner opts out
        if prefs.skip_grooming and "groom" in task.title.lower():
            return True

        # Skip outdoor/walk tasks for pets that don't need them
        if not pet.requires_outdoor_tasks() and any(
            kw in task.title.lower() for kw in ("walk", "outdoor", "run")
        ):
            return True

        return False

    def _fits_in_time(self, task: Task) -> bool:
        """Return True if adding this task stays within available_minutes."""
        return self.total_scheduled_minutes() + task.duration_minutes <= self.owner.available_minutes

    def _next_start_time(self) -> str:
        """Compute the wall-clock start for the next task slot."""
        base = self._time_str_to_minutes(self.start_time)
        offset = self.total_scheduled_minutes()
        return self._minutes_to_time_str(base + offset)

    def _time_str_to_minutes(self, time_str: str) -> int:
        """Convert 'HH:MM' to total minutes since midnight."""
        hours, minutes = time_str.split(":")
        return int(hours) * 60 + int(minutes)

    def _minutes_to_time_str(self, total_minutes: int) -> str:
        """Convert total minutes since midnight to 'HH:MM'."""
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"


# ---------------------------------------------------------------------------
# PawPalApp — single public API for the Streamlit UI
# ---------------------------------------------------------------------------

class PawPalApp:
    """Top-level coordinator. app.py should only call methods on this class."""

    def __init__(self):
        """Initialise the app with no owner or scheduler — call setup() next."""
        self.owner: Optional[Owner] = None
        self.scheduler: Optional[Scheduler] = None

    def setup(self, owner_name: str, available_minutes: int = 120,
              preferences: Optional[Preferences] = None) -> None:
        """Initialise the owner. Call add_pet() next to register pets."""
        self.owner = Owner(
            name=owner_name,
            available_minutes=available_minutes,
            preferences=preferences,
        )
        self.scheduler = Scheduler(self.owner)

    def add_pet(self, pet_name: str, species: str,
                age_years: float = 0.0, special_needs: str = "") -> Pet:
        """Create a Pet, register it with the owner, and return it."""
        if self.owner is None:
            raise RuntimeError("Call setup() before adding pets.")
        pet = Pet(name=pet_name, species=species, age_years=age_years, special_needs=special_needs)
        self.owner.add_pet(pet)
        return pet

    def add_task(self, pet: Pet, title: str, duration_minutes: int,
                 priority: Priority, frequency: Frequency = Frequency.DAILY,
                 notes: str = "", is_required: bool = False) -> None:
        """Create a Task and attach it directly to the given pet."""
        task = Task(
            title=title,
            duration_minutes=duration_minutes,
            priority=priority,
            frequency=frequency,
            notes=notes,
            is_required=is_required,
        )
        pet.add_task(task)

    def remove_task(self, pet: Pet, title: str) -> None:
        """Remove a task by title from the given pet."""
        pet.remove_task(title)

    def generate_schedule(self) -> list[ScheduledTask]:
        """Run the scheduler and return the resulting plan."""
        if self.scheduler is None:
            raise RuntimeError("Call setup() before generating a schedule.")
        return self.scheduler.build_plan()

    def get_explanation(self) -> str:
        """Return a plain-text explanation of the most recently generated plan."""
        if self.scheduler is None:
            raise RuntimeError("Call setup() before requesting an explanation.")
        return self.scheduler.explain_plan()
