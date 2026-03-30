# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class goes beyond a simple to-do list with several algorithmic improvements:

**Priority-first scheduling** — optional tasks are sorted highest → lowest priority before being slotted in. Required tasks are always included first, even if they exceed the owner's time budget.

**Frequency-aware recurrence** — when a task is marked complete, `complete_task()` automatically queues the next occurrence on the pet. Daily tasks reappear tomorrow; weekly tasks reappear in 7 days. Due dates are calculated from the previous due date (not today) so late completions never cause drift. AS_NEEDED tasks never auto-recur.

**`due_today()` filtering** — the scheduler can filter the full task list to only what is due on a given weekday, respecting `DAILY` / `WEEKLY` / `AS_NEEDED` frequencies. Weekly tasks use a `weekday:N` marker in the task notes to identify their assigned day.

**Time-safe sorting** — `sort_by_time()` converts `HH:MM` strings to integer minutes before comparing, preventing lexicographic sort bugs (e.g. `'09:05'` would sort after `'10:00'` as a raw string).

**All-pairs conflict detection** — `detect_conflicts()` compares every pair of scheduled tasks (not just adjacent ones) using the interval overlap formula `a_start < b_end and b_start < a_end`. Same-pet overlaps are flagged as `ERROR`; cross-pet overlaps as `WARNING`. Malformed time strings produce a `PARSE ERROR` message instead of crashing.

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
