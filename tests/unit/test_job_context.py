import pytest

from procrastinate import job_context


@pytest.mark.parametrize(
    "job_result, expected",
    [
        (job_context.JobResult(), None),
        (job_context.JobResult(start_timestamp=10), 20),
        (job_context.JobResult(start_timestamp=10, end_timestamp=15), 5),
    ],
)
def test_job_result_duration(job_result, expected):
    assert job_result.duration(current_timestamp=30) == expected


@pytest.mark.parametrize(
    "job_result, expected",
    [
        (job_context.JobResult(), {}),
        (
            job_context.JobResult(start_timestamp=10),
            {
                "start_timestamp": 10,
                "duration": 15,
            },
        ),
        (
            job_context.JobResult(start_timestamp=10, end_timestamp=15, result="foo"),
            {
                "start_timestamp": 10,
                "end_timestamp": 15,
                "duration": 5,
                "result": "foo",
            },
        ),
    ],
)
def test_job_result_as_dict(job_result, expected, mocker):
    mocker.patch("time.time", return_value=25)
    assert job_result.as_dict() == expected


@pytest.mark.parametrize(
    "queues, result", [(None, "all queues"), (["foo", "bar"], "queues foo, bar")]
)
def test_queues_display(queues, result):
    context = job_context.JobContext(worker_queues=queues)
    assert context.queues_display == result


def test_evolve():
    context = job_context.JobContext(worker_name="a")
    assert context.evolve(worker_name="b").worker_name == "b"


def test_log_extra():
    context = job_context.JobContext(
        worker_name="a", worker_id=2, additional_context={"ha": "ho"}
    )

    assert context.log_extra(action="foo", bar="baz") == {
        "action": "foo",
        "bar": "baz",
        "worker": {"name": "a", "id": 2, "queues": None},
    }


def test_log_extra_job(job_factory):
    job = job_factory()
    context = job_context.JobContext(worker_name="a", worker_id=2, job=job)

    assert context.log_extra(action="foo") == {
        "action": "foo",
        "job": job.log_context(),
        "worker": {"name": "a", "id": 2, "queues": None},
    }


def test_job_description_no_job(job_factory):
    descr = job_context.JobContext(worker_name="a", worker_id=2).job_description(
        current_timestamp=0
    )
    assert descr == "worker 2: no current job"


def test_job_description_job_no_time(job_factory):
    job = job_factory(task_name="some_task", id=12, task_kwargs={"a": "b"})
    descr = job_context.JobContext(
        worker_name="a", worker_id=2, job=job
    ).job_description(current_timestamp=0)
    assert descr == "worker 2: some_task[12](a='b')"


def test_job_description_job_time(job_factory):
    job = job_factory(task_name="some_task", id=12, task_kwargs={"a": "b"})
    descr = job_context.JobContext(
        worker_name="a",
        worker_id=2,
        job=job,
        job_result=job_context.JobResult(start_timestamp=20.0),
    ).job_description(current_timestamp=30.0)
    assert descr == "worker 2: some_task[12](a='b') (started 10.000 s ago)"
