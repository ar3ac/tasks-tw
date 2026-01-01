from .auth_gtasks import gtasks


def run() -> int:
    print("tasks-tw: avvio app")

    tasks = gtasks()
    for task in tasks:
        print(f"Task: {task.get('title')} ({task.get('id')})")
    return 0
