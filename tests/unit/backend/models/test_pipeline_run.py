import uuid

from app.models.pipeline_run import PipelineRun


def test_pipeline_run_repr():
    """PipelineRun repr should include ID, status, and source."""
    run_id = uuid.uuid4()

    pipeline_run = PipelineRun(
        id=run_id,
        status="completed",
        source_site="linkedin",
    )

    assert repr(pipeline_run) == (
        f"<PipelineRun(id={run_id}, status=completed, source=linkedin)>"
    )