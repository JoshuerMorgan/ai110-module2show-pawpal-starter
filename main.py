from datetime import date
from pawpal_system import Frequency, PawPalApp, Preferences, Priority, ScheduledTask, Task

app = PawPalApp()
app.setup(
    owner_name="Jordan",
    available_minutes=180,
    preferences=Preferences(preferred_walk_time="morning", skip_grooming=False),
)

mochi = app.add_pet("Mochi", species="dog", age_years=3.0)
luna  = app.add_pet("Luna",  species="cat", age_years=5.0)

# ---------------------------------------------------------------------------
# Tasks added OUT OF ORDER intentionally — evening task first, morning last
# ---------------------------------------------------------------------------
app.add_task(luna,  "Evening wind-down play", duration_minutes=10, priority=Priority.LOW,
             frequency=Frequency.DAILY)

app.add_task(mochi, "Grooming brush",         duration_minutes=15, priority=Priority.LOW,
             frequency=Frequency.WEEKLY,       notes="weekday:0")   # Mondays only

app.add_task(luna,  "Litter box clean",        duration_minutes=5,  priority=Priority.HIGH,
             frequency=Frequency.DAILY,        is_required=True)

app.add_task(mochi, "Training session",        duration_minutes=20, priority=Priority.MEDIUM,
             frequency=Frequency.DAILY,        notes="Practice sit, stay, and recall")

app.add_task(luna,  "Breakfast feeding",       duration_minutes=10, priority=Priority.HIGH,
             frequency=Frequency.DAILY,        is_required=True)

app.add_task(mochi, "Breakfast feeding",       duration_minutes=10, priority=Priority.HIGH,
             frequency=Frequency.DAILY,        is_required=True)

app.add_task(mochi, "Morning walk",            duration_minutes=30, priority=Priority.HIGH,
             frequency=Frequency.DAILY,        is_required=True)

# ---------------------------------------------------------------------------
# Generate the schedule
# ---------------------------------------------------------------------------
app.generate_schedule()
scheduler = app.scheduler

SEP = "=" * 55

# ---------------------------------------------------------------------------
# 1. Raw plan (insertion order — intentionally unordered)
# ---------------------------------------------------------------------------
print(SEP)
print("  RAW PLAN  (insertion order — unordered)")
print(SEP)
for i, st in enumerate(scheduler.plan, 1):
    print(f"  {i}. [{st.start_time}] {st.pet.name}: {st.task.title}")

# ---------------------------------------------------------------------------
# 2. Sorted by time
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  SORTED BY TIME")
print(SEP)
for i, st in enumerate(scheduler.sort_by_time(), 1):
    print(f"  {i}. [{st.start_time}–{st.end_time}] {st.pet.name}: {st.task.title}")

# ---------------------------------------------------------------------------
# 3. Filter — Mochi's tasks only
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  FILTER: Mochi's tasks")
print(SEP)
for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
    status = "done" if task.completed else "pending"
    print(f"  {pet.name}: {task.task if hasattr(task, 'task') else task.title}  [{status}]")

# ---------------------------------------------------------------------------
# 4. Filter — pending tasks only (nothing completed yet)
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  FILTER: pending tasks (not yet completed)")
print(SEP)
for pet, task in scheduler.filter_tasks(completed=False):
    print(f"  {pet.name}: {task.title}  ({task.priority.name})")

# ---------------------------------------------------------------------------
# 5. Due today (checks Frequency — today's weekday used)
# ---------------------------------------------------------------------------
today_weekday = date.today().weekday()   # 0=Mon … 6=Sun
day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
print(f"\n{SEP}")
print(f"  DUE TODAY  ({day_names[today_weekday]})")
print(SEP)
for pet, task in scheduler.due_today(today_weekday):
    print(f"  {pet.name}: {task.title}  ({task.frequency.value})")

# ---------------------------------------------------------------------------
# 6. Conflict detection
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  CONFLICT DETECTION")
print(SEP)

# build_plan always assigns sequential slots, so inject two deliberate
# conflicts to prove detect_conflicts() surfaces them correctly:
#   - same-pet:    a second Mochi task overlapping the Morning walk slot
#   - cross-pet:   a Luna task that starts before Mochi's walk ends
clash_same  = Task("Emergency vet call", duration_minutes=20, priority=Priority.HIGH,
                   frequency=Frequency.AS_NEEDED)
clash_cross = Task("Luna meds",          duration_minutes=10, priority=Priority.HIGH,
                   frequency=Frequency.DAILY)

scheduler.plan.append(ScheduledTask(task=clash_same,  pet=mochi,
                                    start_time="08:05", end_time="08:25",
                                    reason="injected same-pet conflict"))
scheduler.plan.append(ScheduledTask(task=clash_cross, pet=luna,
                                    start_time="08:10", end_time="08:20",
                                    reason="injected cross-pet conflict"))

conflicts = scheduler.detect_conflicts()
if conflicts:
    for c in conflicts:
        print(f"  {c}")
else:
    print("  No conflicts detected — plan is clean.")

# ---------------------------------------------------------------------------
# 7. Recurring task demo — complete a task, verify next occurrence is queued
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  RECURRING TASKS — complete then check next occurrence")
print(SEP)

# Pick Mochi's morning walk from the plan and complete it
walk_entry = next(st for st in scheduler.plan if st.task.title == "Morning walk")
walk_task  = walk_entry.task

print(f"  Before: Mochi has {len(mochi.tasks)} task(s), walk completed = {walk_task.completed}")

next_walk = scheduler.complete_task(walk_entry.pet, walk_task)

print(f"  After:  Mochi has {len(mochi.tasks)} task(s), walk completed = {walk_task.completed}")
if next_walk:
    print(f"  Next occurrence queued: '{next_walk.title}'  completed = {next_walk.completed}")

# Luna's litter box (daily)
litter_entry = next(st for st in scheduler.plan if st.task.title == "Litter box clean")
next_litter  = scheduler.complete_task(litter_entry.pet, litter_entry.task)
print(f"\n  Luna's litter box marked done. Next occurrence queued = {next_litter is not None}")

# AS_NEEDED task — should produce no next occurrence
from pawpal_system import Task as PawTask
one_off = PawTask("Vet visit", duration_minutes=60, priority=Priority.HIGH, frequency=Frequency.AS_NEEDED)
result  = one_off.next_occurrence()
print(f"\n  AS_NEEDED 'Vet visit' next_occurrence() = {result}  (expected None)")

print(f"\n{SEP}")
