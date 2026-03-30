import streamlit as st
from pawpal_system import PawPalApp, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — initialise once per session
# ---------------------------------------------------------------------------
if "app" not in st.session_state:
    st.session_state.app = PawPalApp()
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None
if "plan_built" not in st.session_state:
    st.session_state.plan_built = False

app: PawPalApp = st.session_state.app

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=120
    )

if st.button("Save owner"):
    app.setup(owner_name=owner_name, available_minutes=int(available_minutes))
    st.session_state.plan_built = False
    st.success(f"Owner '{owner_name}' saved — {available_minutes} min available today.")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age_years = st.number_input(
        "Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5
    )

if st.button("Add pet"):
    if app.owner is None:
        st.warning("Save an owner first before adding pets.")
    else:
        pet = app.add_pet(pet_name=pet_name, species=species, age_years=age_years)
        st.session_state.current_pet = pet
        st.success(f"{pet_name} ({species}) added.")

if app.owner and app.owner.pets:
    pet_names = [p.name for p in app.owner.pets]
    selected_pet_name = st.selectbox("Select pet to add tasks to", pet_names)
    st.session_state.current_pet = next(
        p for p in app.owner.pets if p.name == selected_pet_name
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"], index=2)
with col4:
    required = st.checkbox("Required?")

if st.button("Add task"):
    if st.session_state.current_pet is None:
        st.warning("Add a pet first before adding tasks.")
    else:
        app.add_task(
            pet=st.session_state.current_pet,
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority_str],
            is_required=required,
        )
        st.success(
            f"'{task_title}' added to {st.session_state.current_pet.name}."
        )

# Task table — all pets
if app.owner:
    all_tasks = app.owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        st.table(
            [
                {
                    "Pet": pet.name,
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority.name,
                    "Required": "Yes" if task.is_required else "No",
                    "Done": "✓" if task.completed else "—",
                }
                for pet, task in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if app.owner is None:
        st.warning("Save an owner before generating a schedule.")
    elif not app.owner.pets:
        st.warning("Add at least one pet before generating a schedule.")
    elif not app.owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        app.generate_schedule()
        st.session_state.plan_built = True

# ---------------------------------------------------------------------------
# Section 5 — Display results (only after a plan exists)
# ---------------------------------------------------------------------------
if st.session_state.plan_built and app.scheduler and app.scheduler.plan:
    scheduler = app.scheduler
    total_min = scheduler.total_scheduled_minutes()
    remaining = app.owner.available_minutes - total_min

    st.success(
        f"Schedule ready — {len(scheduler.plan)} tasks, "
        f"{total_min} min scheduled, {remaining} min free."
    )

    # -- Conflict warnings (shown before the plan so they aren't missed) ----
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(
            f"**{len(conflicts)} scheduling conflict(s) detected.** "
            "Review and adjust task times before following this plan."
        )
        for conflict in conflicts:
            severity = "🔴" if conflict.startswith("ERROR") else "🟡"
            # ERROR = same pet cannot do two things at once (hard block)
            # WARNING = different pets overlap (may need a second person)
            st.warning(f"{severity} {conflict}")
    else:
        st.success("No conflicts — your plan is clear.")

    st.divider()

    # -- Sorted schedule table ----------------------------------------------
    st.subheader("Today's Schedule (sorted by time)")
    sorted_plan = scheduler.sort_by_time()

    schedule_rows = [
        {
            "Time": f"{st_task.start_time} – {st_task.end_time}",
            "Pet": st_task.pet.name,
            "Task": st_task.task.title,
            "Duration (min)": st_task.task.duration_minutes,
            "Priority": st_task.task.priority.name,
            "Required": "Yes" if st_task.task.is_required else "No",
            "Why": st_task.reason,
        }
        for st_task in sorted_plan
    ]
    st.table(schedule_rows)

    # -- Filter by pet ------------------------------------------------------
    if app.owner and len(app.owner.pets) > 1:
        st.subheader("Filter by Pet")
        pet_filter = st.selectbox(
            "Show tasks for", ["All pets"] + [p.name for p in app.owner.pets]
        )
        if pet_filter != "All pets":
            filtered = scheduler.filter_tasks(pet_name=pet_filter, completed=False)
            if filtered:
                st.table(
                    [
                        {
                            "Task": t.title,
                            "Duration (min)": t.duration_minutes,
                            "Priority": t.priority.name,
                            "Required": "Yes" if t.is_required else "No",
                        }
                        for _, t in filtered
                    ]
                )
            else:
                st.info(f"No pending tasks for {pet_filter}.")

    # -- Full explanation expander ------------------------------------------
    with st.expander("Show full plan explanation"):
        st.text(app.get_explanation())
