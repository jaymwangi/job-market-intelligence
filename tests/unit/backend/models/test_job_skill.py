import uuid

from app.models.job_skill import JobSkill


def test_job_skill_repr():
    """JobSkill repr should include both linked IDs."""
    job_id = uuid.uuid4()
    skill_id = uuid.uuid4()

    job_skill = JobSkill(
        job_id=job_id,
        skill_id=skill_id,
    )

    assert repr(job_skill) == (
        f"<JobSkill(job_id={job_id}, skill_id={skill_id})>"
    )

import uuid

from app.models.skill import Skill


def test_skill_repr():
    """Skill repr should include ID and name."""
    skill_id = uuid.uuid4()
    skill = Skill(id=skill_id, name="Python")

    assert repr(skill) == f"<Skill(id={skill_id}, name=Python)>"