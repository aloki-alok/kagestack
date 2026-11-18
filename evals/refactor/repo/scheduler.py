import json

import handlers


def run_jobs(path="jobs.json"):
    with open(path) as f:
        jobs = json.load(f)
    return [getattr(handlers, job["handler"])(job["to"], job["body"]) for job in jobs]
