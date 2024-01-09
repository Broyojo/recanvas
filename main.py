import os
import re
from datetime import timezone

from canvasapi import Canvas
from markdownify import markdownify as md
from reclaim_sdk.models.task import ReclaimTask
from tqdm import tqdm

blacklist = {
    1616720, # TA Lab Visit
    1594782, # Timed Lab 3 Makeup
    1594784, # Timed Lab 4
}

def sync():
    canvas = Canvas(
        base_url="https://gatech.instructure.com/",
        access_token=os.environ["CANVAS_API_KEY"]
    )

    canvas_user = canvas.get_user('dandrews47', 'sis_login_id')
    courses = canvas_user.get_courses(enrollment_state='active')        
                
    # Map of canvas id -> reclaim task
    tasks: dict[int, ReclaimTask] = {
        int(re_match.group(1)): task 
        for task in ReclaimTask.search() 
        if (re_match := re.search(r"Canvas Assignment ID: (\d+)", task.description))
    }
    
    # for task in tqdm(tasks.values(), desc="Deleting old assignments"):
    #     task.delete()          
    # return

    # update duration regardless of what is on the calendar already
    FORCE_UPDATE_DURATION = False

    assignments = {}

    # add any tasks which are not present in reclaim or edit any tasks which have been edited in canvas
    for course in courses:
        for assignment in tqdm(canvas_user.get_assignments(course), desc=f"Syncing {course.name}"):
            if "due_at_date" in assignment.__dict__:
                try:
                    # get relevant fields for reclaim task from canvas assignment
                    id = assignment.id
                    if id in blacklist:
                        tqdm.write(f"Skipping {assignment.name} because it is blacklisted")
                        continue
                    name = assignment.name
                    description = f"""**Course: {course.name}**

{md(assignment.description) if assignment.description is not None else ""}

[Link to Canvas Assignment]({assignment.html_url})
Canvas Assignment ID: {id}"""
                    start_date = assignment.unlock_at_date if "unlock_at_date" in assignment.__dict__ is not None else assignment.created_at_date
                    due_date = assignment.due_at_date
                    duration = 1
                    min_work_duration = 0.5
                    max_work_duration = 2
                    
                    # TODO: use AI to figure out how long these should be
                    
                    if "Lecture Attendance" in name:
                        duration = 0.25
                        start_date = start_date.replace(hour=21, minute=45) # fix all the times to be after lecture
                    
                    if "RC" in name:
                        duration = 0.5
                    
                    if "Homework" in name:
                        duration = 4
                    
                    if "Zybooks" in name:
                        duration = 2
                    
                    # check if the assignment is submitted already
                    submission = assignment.get_submission(canvas_user)
                    if "submitted_at" in submission.__dict__:
                        if submission.submitted_at is not None:
                            # if it is submitted on canvas, we don't delete it from here because
                            # we can try it a few more times and then confirm the thing done
                            # once we mark it done on reclaim

                            # if id in tasks:
                            #     print(f"Marking {tasks[id].name} as complete")
                            #     tasks[id].mark_complete()
                            #     assignments[id] = assignment
                            
                            assignments[id] = assignment
                            continue

                    # add or edit task in reclaim
                    with (tasks[id] if id in tasks else ReclaimTask()) as task:
                        if id not in tasks:
                            tqdm.write(f"Adding {name}")
                        if task.name != name:
                            tqdm.write(f"Updating {task.name} to {name}")
                        task.name = name
                        task.description = description
                        if task.start_date != start_date:
                            tqdm.write(f"Updating {task.name} start date from {task.start_date} to {start_date}")
                        task.start_date = start_date
                        if task.due_date != due_date:
                            tqdm.write(f"Updating {task.name} due date from {task.due_date} to {due_date}")
                        task.due_date = due_date
                        # TODO: maybe only add duration if it wasn't already on reclaim
                        task.duration = task.duration if id in tasks and not FORCE_UPDATE_DURATION else duration
                        task.min_work_duration = min_work_duration
                        task.max_work_duration = max_work_duration
                        task.is_work_task = True

                    assignments[id] = assignment
                except Exception as e:
                    print(e)
                    print(assignment.__dict__)
                    return
  
    # delete any tasks from reclaim which were removed from canvas or are in the blacklist
    for id, task in tasks.items():
        if id not in assignments or id in blacklist:
            print(f"Deleting {task.name}")
            task.delete() # maybe just mark it as done instead so it isn't destructive?

sync()