import os

from canvasapi import Canvas

canvas = Canvas(
    base_url="https://gatech.instructure.com/",
    access_token=os.environ["CANVAS_API_KEY"]
)

canvas_user = canvas.get_user('dandrews47', 'sis_login_id')

for announcement in canvas.get_announcements([368762]):
    print(announcement)

# courses = canvas_user.get_courses(enrollment_state='active')   

# for course in courses:
#     if course.id == 368762:
#         print()     

# for course in courses:
#     print()

# assignments = []

# for course in courses:
#     for assignment in canvas_user.get_assignments(course):
#         if "CS-2340-B" in course.name:
#             assignments.append(assignment)

# submission = assignments[0].get_submission(canvas_user)
# print(submission.__dict__)

# from datetime import datetime, timedelta, timezone

# from reclaim_sdk.models.task import ReclaimTask

# time = datetime.now().astimezone(timezone.utc)

# print(time)

# with ReclaimTask() as task:
#     task.name = "test"
#     task.duration = 0.5
#     task.due_date = time