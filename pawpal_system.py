from dataclasses import dataclass, field, replace
from datetime import date, timedelta
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
    due_date: date = field(default_factory=date.today)
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

    def next_occurrence(self) -> "Task | None":
        """
        Return a fresh copy of this task scheduled for its next occurrence.

        Uses dataclasses.replace to clone every field, then overwrites
        completed=False and due_date with a timedelta shift based on frequency:
          - DAILY  → due_date + 1 day
          - WEEKLY → due_date + 7 days
          - AS_NEEDED → returns None (one-off tasks don't auto-recur)

        Shifting from self.due_date (not date.today()) prevents drift when a
        task is completed late — the next occurrence is always relative to when
        it was supposed to happen, not when it actually got done.
        """
        if self.frequency == Frequency.AS_NEEDED:
            return None
        delta = timedelta(days=1) if self.frequency == Frequency.DAILY else timedelta(weeks=1)
        return replace(self, completed=False, due_date=self.due_date + delta)


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
                continue          # skip this task but keep looking for smaller ones
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

    def complete_task(self, pet: Pet, task: Task) -> "Task | None":
        """
        Mark task complete and, for DAILY/WEEKLY tasks, add the next occurrence to the pet.

        Returns the new Task instance if one was created, or None for AS_NEEDED tasks.
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def sort_by_time(self) -> list[ScheduledTask]:
        """
        Return the current plan sorted chronologically by start_time.

        Converts each 'HH:MM' string to total minutes since midnight before
        comparing, so lexicographic string sorting cannot produce wrong order
        (e.g. '09:05' would sort after '10:00' as a string but before it as
        a time).  Returns a new list — self.plan is not mutated.
        """
        return sorted(self.plan, key=lambda st: self._time_str_to_minutes(st.start_time))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Return (pet, task) pairs from the owner's full task list matching the given filters.

        pet_name  — if provided, only return tasks belonging to that pet.
        completed — if True, return only done tasks; if False, only pending; if None, return all.
        """
        results = self.owner.get_all_tasks()
        if pet_name is not None:
            results = [(pet, task) for pet, task in results if pet.name == pet_name]
        if completed is not None:
            results = [(pet, task) for pet, task in results if task.completed == completed]
        return results

    def due_today(self, today_weekday: int) -> list[tuple[Pet, Task]]:
        """
        Return tasks that are due on today_weekday (0 = Monday … 6 = Sunday).

        DAILY tasks are always due.
        WEEKLY tasks are due only when today_weekday matches their assigned day
        (stored as task.notes starting with 'weekday:N', e.g. 'weekday:0').
        AS_NEEDED tasks are never auto-scheduled — they must be added manually.
        """
        due = []
        for pet, task in self.owner.get_all_tasks():
            if task.frequency.value == "daily":
                due.append((pet, task))
            elif task.frequency.value == "weekly":
                # Expect notes to contain 'weekday:N' for the assigned day
                for part in task.notes.split():
                    if part.startswith("weekday:"):
                        assigned_day = int(part.split(":")[1])
                        if assigned_day == today_weekday:
                            due.append((pet, task))
                        break
        return due

    def detect_conflicts(self) -> list[str]:
        """
        Check every pair of scheduled tasks for time-slot overlaps.

        Compares all pairs (not just adjacent) so nested or non-adjacent
        overlaps are never missed.  Same-pet conflicts are flagged as
        ERROR (the owner physically cannot do both); cross-pet conflicts
        are flagged as WARNING (may be manageable with some juggling).
        Malformed time strings produce a PARSE ERROR entry instead of
        crashing the program.  Returns [] when the plan is conflict-free.
        """
        conflicts = []

        for i in range(len(self.plan)):
            for j in range(i + 1, len(self.plan)):
                a = self.plan[i]
                b = self.plan[j]

                try:
                    a_start = self._time_str_to_minutes(a.start_time)
                    a_end   = self._time_str_to_minutes(a.end_time)
                    b_start = self._time_str_to_minutes(b.start_time)
                    b_end   = self._time_str_to_minutes(b.end_time)
                except (ValueError, AttributeError) as exc:
                    conflicts.append(
                        f"PARSE ERROR: could not read times for "
                        f"'{a.pet.name}: {a.task.title}' or "
                        f"'{b.pet.name}: {b.task.title}' — {exc}"
                    )
                    continue

                # Two intervals overlap when one starts before the other ends
                overlaps = a_start < b_end and b_start < a_end
                if not overlaps:
                    continue

                same_pet = a.pet.name == b.pet.name
                severity = "ERROR" if same_pet else "WARNING"
                scope    = "same pet" if same_pet else "different pets"
                conflicts.append(
                    f"{severity} ({scope}): "
                    f"'{a.pet.name}: {a.task.title}' [{a.start_time}-{a.end_time}] overlaps "
                    f"'{b.pet.name}: {b.task.title}' [{b.start_time}-{b.end_time}]"
                )

        return conflicts

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
