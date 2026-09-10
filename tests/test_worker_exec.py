import shlex

from worker.main import ClusterWorker


def test_parse_command_argv():
    worker = ClusterWorker.__new__(ClusterWorker)
    cmd = "echo hello world"
    argv = shlex.split(cmd)
    assert argv == ["echo", "hello", "world"]
