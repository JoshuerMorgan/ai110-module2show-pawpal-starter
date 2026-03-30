import streamlit as st
from pawpal_system import PawPalApp, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — initialise the app and pet list once per session
# ---------------------------------------------------------------------------
if "app" not in st.session_state:
    st.session_state.app = PawPalApp()

if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

app: PawPalApp = st.session_state.app

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=120)

if st.button("Save owner"):
    app.setup(owner_name=owner_name, available_minutes=int(available_minutes))
    st.success(f"Owner '{owner_name}' saved with {available_minutes} min available.")

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
    age_years = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

if st.button("Add pet"):
    if app.owner is None:
        st.warning("Save an owner first before adding pets.")
    else:
        pet = app.add_pet(pet_name=pet_name, species=species, age_years=age_years)
        st.session_state.current_pet = pet
        st.success(f"Pet '{pet_name}' ({species}) added.")

# Show registered pets and let user pick which one to add tasks to
if app.owner and app.owner.pets:
    pet_names = [p.name for p in app.owner.pets]
    selected_pet_name = st.selectbox("Select pet to add tasks to", pet_names)
    st.session_state.current_pet = next(p for p in app.owner.pets if p.name == selected_pet_name)

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task to the selected pet
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
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
        st.success(f"Task '{task_title}' added to {st.session_state.current_pet.name}.")

# Show all tasks across all pets
if app.owner:
    all_tasks = app.owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        rows = [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority.name,
                "Required": task.is_required,
                "Done": task.completed,
            }
            for pet, task in all_tasks
        ]
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate and display the schedule
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
        plan = app.generate_schedule()
        st.success(f"Schedule built — {len(plan)} tasks, {app.scheduler.total_scheduled_minutes()} min total.")

        for st_task in plan:
            st.markdown(
                f"**{st_task.start_time}–{st_task.end_time}** &nbsp;|&nbsp; "
                f"{st_task.pet.name}: {st_task.task.title} "
                f"({st_task.task.duration_minutes} min, {st_task.task.priority.name})"
            )
            st.caption(f"Why: {st_task.reason}")

        with st.expander("Full explanation"):
            st.text(app.get_explanation())
