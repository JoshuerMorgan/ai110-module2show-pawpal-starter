from pawpal_system import Frequency, Pet, Priority, Task


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
