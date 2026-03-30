# PawPal+

**PawPal+** is a pet care planning assistant built with Python and Streamlit. It helps busy pet owners stay consistent with daily care routines by generating a prioritized, conflict-checked schedule across multiple pets.

---

## Features

### Multi-Pet Management
Register any number of pets under a single owner. Each pet tracks its own task list independently. The scheduler works across all pets simultaneously, so one owner can manage a dog and a cat in the same daily plan.

### Priority-First Scheduling
Tasks are ranked `HIGH`, `MEDIUM`, or `LOW` using a validated `Priority` enum. When building the daily plan, required tasks are always placed first regardless of the time budget. Optional tasks are then slotted in from highest to lowest priority until the owner's available time is consumed. If a large task doesn't fit, the scheduler keeps scanning for smaller tasks that do — no time is wasted unnecessarily.

### Daily Recurrence
Marking a task complete automatically queues its next occurrence on the pet. Daily tasks reappear the following day; weekly tasks reappear in 7 days. Due dates advance from the previous due date — not from today — so completing a task late never shifts all future occurrences forward (no drift).

### Frequency Filtering
Tasks carry a `Frequency` value (`DAILY`, `WEEKLY`, or `AS_NEEDED`). The `due_today()` method filters the full task list to only what is relevant for a given weekday, so the scheduler never proposes a weekly grooming session on the wrong day. `AS_NEEDED` tasks are never auto-scheduled.

### Chronological Sorting
`sort_by_time()` converts `HH:MM` strings to integer minutes before comparing, preventing the silent lexicographic sort bug where `"09:05"` would rank after `"10:00"` as a raw string. The sorted plan is what the UI always displays — insertion order is never shown to the user.

### Conflict Detection
`detect_conflicts()` compares every pair of scheduled tasks using the interval overlap formula `a_start < b_end and b_start < a_end`. This catches nested and non-adjacent overlaps that adjacent-only checks miss. Conflicts are classified by severity:
- **ERROR** — same pet, same time slot. The owner cannot physically do both.
- **WARNING** — different pets overlap. May be manageable but worth flagging.
- **PARSE ERROR** — malformed time string. Reported as a message rather than a crash.

### Pet-Aware Task Filtering
Species matters. Walk and outdoor tasks are automatically skipped for cats and non-dog pets. Grooming tasks can be suppressed app-wide via a `skip_grooming` preference. Both rules are applied inside `build_plan()` before any task is scheduled.

### Plan Explanation
Every scheduled task includes a plain-English `reason` field explaining why it was chosen. The full explanation is available as a formatted text output, suitable for display in the UI or printing to the terminal.

### Conflict Warnings in the UI
When the Streamlit UI detects conflicts after generating a schedule, it surfaces them above the plan table — before the owner can act on a broken schedule. Errors are shown with a red banner; warnings with a yellow banner. Each conflict message names the specific tasks and their time slots so the owner knows exactly what to fix.

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Smarter Scheduling

The `Scheduler` class goes beyond a simple to-do list with several algorithmic improvements:

**Priority-first scheduling** — optional tasks are sorted highest → lowest priority before being slotted in. Required tasks are always included first, even if they exceed the owner's time budget.

**Frequency-aware recurrence** — when a task is marked complete, `complete_task()` automatically queues the next occurrence on the pet. Daily tasks reappear tomorrow; weekly tasks reappear in 7 days. Due dates are calculated from the previous due date (not today) so late completions never cause drift. AS_NEEDED tasks never auto-recur.

**`due_today()` filtering** — the scheduler can filter the full task list to only what is due on a given weekday, respecting `DAILY` / `WEEKLY` / `AS_NEEDED` frequencies. Weekly tasks use a `weekday:N` marker in the task notes to identify their assigned day.

**Time-safe sorting** — `sort_by_time()` converts `HH:MM` strings to integer minutes before comparing, preventing lexicographic sort bugs (e.g. `'09:05'` would sort after `'10:00'` as a raw string).

**All-pairs conflict detection** — `detect_conflicts()` compares every pair of scheduled tasks (not just adjacent ones) using the interval overlap formula `a_start < b_end and b_start < a_end`. Same-pet overlaps are flagged as `ERROR`; cross-pet overlaps as `WARNING`. Malformed time strings produce a `PARSE ERROR` message instead of crashing.

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | Tests | What is verified |
|---|---|---|
| Task state | 2 | `mark_complete()` flips `completed` to `True`; adding a task grows the pet's list by 1 |
| Sorting | 2 | `sort_by_time()` returns slots in chronological order; original `self.plan` is not mutated |
| Recurrence | 5 | Daily tasks recur tomorrow; weekly tasks recur in 7 days; late completions don't cause date drift; `AS_NEEDED` tasks return `None`; `complete_task()` marks done and queues the next occurrence on the pet |
| Conflict detection | 4 | Same-pet overlap flagged as `ERROR`; cross-pet overlap flagged as `WARNING`; clean sequential plan returns `[]`; nested task (non-adjacent overlap) is caught |

**13 tests — 13 passing.**

### Confidence level

★★★★☆ (4 / 5)

The core scheduling contract (required tasks, priority ordering, recurrence, conflict detection) is fully covered and all 13 tests pass. The rating stops short of 5 stars for two reasons:

1. **Integration paths are untested** — the tests verify individual methods in isolation but do not run a full `build_plan()` end-to-end with multiple pets, mixed priorities, and a tight time budget to confirm all rules interact correctly.
2. **Edge cases at system boundaries are missing** — no tests for an owner with zero pets, `available_minutes=0`, or the `skip_grooming` / species-filter preferences inside `build_plan`.

These gaps would be the next tests to write before considering the system production-ready.

## Demo

<a href="/ai110-module2show-pawpal-starter/Screenshot.png" target="_blank"><img src='/ai110-module2show-pawpal-starter/Screenshot.png'title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

### Run the app locally

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser. From there:

1. Enter an owner name and daily time budget, then click **Save owner**
2. Add one or more pets with name, species, and age
3. Select a pet and add tasks — set duration, priority, and whether the task is required
4. Click **Generate schedule** to build the daily plan
5. Review the sorted schedule table and check for any conflict warnings above it

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
