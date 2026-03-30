from datetime import date, timedelta

import pytest

from pawpal_system import (
    Frequency, Owner, Pet, Priority, Scheduler, ScheduledTask, Task,
)


# ---------------------------------------------------------------------------
# Helpers — reusable fixtures
# ---------------------------------------------------------------------------

def make_scheduler(available_minutes=120):
    """Return a Scheduler wired to a fresh Owner with one dog and one cat."""
    owner = Owner("Jordan", available_minutes=available_minutes)
    mochi = Pet("Mochi", species="dog")
    luna  = Pet("Luna",  species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return Scheduler(owner), mochi, luna


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should flip task.completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority=Priority.HIGH)

    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Breakfast feeding", duration_minutes=10, priority=Priority.HIGH,
                frequency=Frequency.DAILY)

    before = len(pet.tasks)
    pet.add_task(task)
    assert len(pet.tasks) == before + 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() must order slots by wall-clock time, not insertion order."""
    scheduler, mochi, _ = make_scheduler()

    t1 = Task("Evening play",    duration_minutes=15, priority=Priority.LOW)
    t2 = Task("Morning walk",    duration_minutes=30, priority=Priority.HIGH)
    t3 = Task("Afternoon treat", duration_minutes=5,  priority=Priority.MEDIUM)

    # Inject out-of-order slots directly so we control the times precisely
    scheduler.plan = [
        ScheduledTask(task=t1, pet=mochi, start_time="17:00", end_time="17:15"),
        ScheduledTask(task=t2, pet=mochi, start_time="08:00", end_time="08:30"),
        ScheduledTask(task=t3, pet=mochi, start_time="13:00", end_time="13:05"),
    ]

    sorted_plan = scheduler.sort_by_time()
    start_times = [st.start_time for st in sorted_plan]

    assert start_times == ["08:00", "13:00", "17:00"]


def test_sort_by_time_does_not_mutate_plan():
    """sort_by_time() must return a new list, leaving self.plan unchanged."""
    scheduler, mochi, _ = make_scheduler()
    task = Task("Walk", duration_minutes=20, priority=Priority.HIGH)
    scheduler.plan = [
        ScheduledTask(task=task, pet=mochi, start_time="10:00", end_time="10:20"),
        ScheduledTask(task=task, pet=mochi, start_time="08:00", end_time="08:20"),
    ]

    original_order = [st.start_time for st in scheduler.plan]
    scheduler.sort_by_time()

    assert [st.start_time for st in scheduler.plan] == original_order


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_next_occurrence_is_tomorrow():
    """Completing a DAILY task must queue a new task due the following day."""
    today = date.today()
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH,
                frequency=Frequency.DAILY, due_date=today)

    task.mark_complete()
    next_task = task.next_occurrence()

    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == today + timedelta(days=1)


def test_weekly_task_next_occurrence_is_next_week():
    """Completing a WEEKLY task must queue a new task due seven days later."""
    today = date.today()
    task = Task("Grooming", duration_minutes=20, priority=Priority.LOW,
                frequency=Frequency.WEEKLY, due_date=today)

    task.mark_complete()
    next_task = task.next_occurrence()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_recurrence_shifts_from_due_date_not_today():
    """next_occurrence() must advance from due_date, not date.today(), to prevent drift."""
    past_due = date.today() - timedelta(days=3)   # task is 3 days overdue
    task = Task("Feed fish", duration_minutes=5, priority=Priority.HIGH,
                frequency=Frequency.DAILY, due_date=past_due)

    task.mark_complete()
    next_task = task.next_occurrence()

    # Next occurrence should be past_due + 1 day, not today + 1 day
    assert next_task.due_date == past_due + timedelta(days=1)
    assert next_task.due_date != date.today() + timedelta(days=1)


def test_as_needed_task_has_no_next_occurrence():
    """AS_NEEDED tasks must return None from next_occurrence() — they never auto-recur."""
    task = Task("Vet visit", duration_minutes=60, priority=Priority.HIGH,
                frequency=Frequency.AS_NEEDED)

    assert task.next_occurrence() is None


def test_complete_task_adds_next_occurrence_to_pet():
    """Scheduler.complete_task() must mark done and add the next occurrence to the pet."""
    scheduler, mochi, _ = make_scheduler()
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH,
                frequency=Frequency.DAILY)
    mochi.add_task(task)
    scheduler.plan = [ScheduledTask(task=task, pet=mochi,
                                    start_time="08:00", end_time="08:30")]

    task_count_before = len(mochi.tasks)
    scheduler.complete_task(mochi, task)

    assert task.completed is True
    assert len(mochi.tasks) == task_count_before + 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_same_pet_overlap():
    """Two tasks for the same pet at overlapping times must be flagged as ERROR."""
    scheduler, mochi, _ = make_scheduler()
    t1 = Task("Walk",     duration_minutes=30, priority=Priority.HIGH)
    t2 = Task("Training", duration_minutes=20, priority=Priority.MEDIUM)

    scheduler.plan = [
        ScheduledTask(task=t1, pet=mochi, start_time="08:00", end_time="08:30"),
        ScheduledTask(task=t2, pet=mochi, start_time="08:15", end_time="08:35"),
    ]

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "ERROR" in conflicts[0]
    assert "same pet" in conflicts[0]


def test_detect_conflicts_finds_cross_pet_overlap():
    """Overlapping tasks across different pets must be flagged as WARNING."""
    scheduler, mochi, luna = make_scheduler()
    t1 = Task("Walk",    duration_minutes=30, priority=Priority.HIGH)
    t2 = Task("Feeding", duration_minutes=10, priority=Priority.HIGH)

    scheduler.plan = [
        ScheduledTask(task=t1, pet=mochi, start_time="08:00", end_time="08:30"),
        ScheduledTask(task=t2, pet=luna,  start_time="08:10", end_time="08:20"),
    ]

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "WARNING" in conflicts[0]
    assert "different pets" in conflicts[0]


def test_detect_conflicts_clean_plan_returns_empty():
    """A plan with no overlapping slots must return an empty conflict list."""
    scheduler, mochi, _ = make_scheduler()
    t1 = Task("Walk",     duration_minutes=30, priority=Priority.HIGH)
    t2 = Task("Training", duration_minutes=20, priority=Priority.MEDIUM)

    scheduler.plan = [
        ScheduledTask(task=t1, pet=mochi, start_time="08:00", end_time="08:30"),
        ScheduledTask(task=t2, pet=mochi, start_time="08:30", end_time="08:50"),
    ]

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_catches_nested_overlap():
    """A task fully nested inside another must be flagged even if non-adjacent."""
    scheduler, mochi, _ = make_scheduler()
    outer  = Task("Long walk",   duration_minutes=60, priority=Priority.HIGH)
    nested = Task("Quick treat", duration_minutes=5,  priority=Priority.LOW)
    clean  = Task("Evening play",duration_minutes=15, priority=Priority.LOW)

    scheduler.plan = [
        ScheduledTask(task=outer,  pet=mochi, start_time="08:00", end_time="09:00"),
        ScheduledTask(task=nested, pet=mochi, start_time="08:10", end_time="08:15"),
        ScheduledTask(task=clean,  pet=mochi, start_time="10:00", end_time="10:15"),
    ]

    conflicts = scheduler.detect_conflicts()

    conflict_titles = " ".join(conflicts)
    assert "Long walk" in conflict_titles
    assert "Quick treat" in conflict_titles
    assert "Evening play" not in conflict_titles
