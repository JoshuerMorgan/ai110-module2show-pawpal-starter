from pawpal_system import Frequency, PawPalApp, Preferences, Priority

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
app = PawPalApp()

app.setup(
    owner_name="Jordan",
    available_minutes=180,
    preferences=Preferences(preferred_walk_time="morning", skip_grooming=False),
)

# ---------------------------------------------------------------------------
# Add pets
# ---------------------------------------------------------------------------
mochi = app.add_pet("Mochi", species="dog", age_years=3.0)
luna  = app.add_pet("Luna",  species="cat", age_years=5.0)

# ---------------------------------------------------------------------------
# Add tasks — Mochi (dog)
# ---------------------------------------------------------------------------
app.add_task(mochi, "Morning walk",      duration_minutes=30, priority=Priority.HIGH,
             frequency=Frequency.DAILY,   is_required=True)

app.add_task(mochi, "Breakfast feeding", duration_minutes=10, priority=Priority.HIGH,
             frequency=Frequency.DAILY,   is_required=True)

app.add_task(mochi, "Training session",  duration_minutes=20, priority=Priority.MEDIUM,
             frequency=Frequency.DAILY,   notes="Practice sit, stay, and recall")

app.add_task(mochi, "Grooming brush",    duration_minutes=15, priority=Priority.LOW,
             frequency=Frequency.WEEKLY)

# ---------------------------------------------------------------------------
# Add tasks — Luna (cat)
# ---------------------------------------------------------------------------
app.add_task(luna, "Breakfast feeding",  duration_minutes=10, priority=Priority.HIGH,
             frequency=Frequency.DAILY,   is_required=True)

app.add_task(luna, "Litter box clean",   duration_minutes=5,  priority=Priority.HIGH,
             frequency=Frequency.DAILY,   is_required=True)

app.add_task(luna, "Enrichment play",    duration_minutes=15, priority=Priority.MEDIUM,
             frequency=Frequency.DAILY,   notes="Wand toy or puzzle feeder")

# ---------------------------------------------------------------------------
# Generate and display the schedule
# ---------------------------------------------------------------------------
app.generate_schedule()

print("=" * 55)
print("        TODAY'S PAWPAL+ SCHEDULE")
print("=" * 55)
print(app.get_explanation())
print("=" * 55)
