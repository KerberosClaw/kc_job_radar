"""Data models for kc_job_radar."""

from dataclasses import dataclass


@dataclass
class Job:
    job_id: str
    title: str
    company: str
    location: str
    salary: str
    url: str

    def summary(self) -> str:
        return f"{self.company} | {self.title} | {self.location} | {self.salary}"
