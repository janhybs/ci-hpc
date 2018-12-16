# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = profiler_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Optional, List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


@dataclass
class Child:
    tag: str
    file_path: str
    file_line: int
    function: str
    cumul_time_min: str
    cumul_time_max: str
    cumul_time_sum: str
    call_count_min: int
    call_count_max: int
    call_count_sum: int
    memory_alloc_min: int
    memory_alloc_max: int
    memory_alloc_sum: int
    memory_dealloc_min: int
    memory_dealloc_max: int
    memory_dealloc_sum: int
    memory_peak_min: int
    memory_peak_max: int
    memory_peak_sum: int
    memory_alloc_called_min: int
    memory_alloc_called_max: int
    memory_alloc_called_sum: int
    memory_dealloc_called_min: int
    memory_dealloc_called_max: int
    memory_dealloc_called_sum: int
    memory_petsc_diff_min: int
    memory_petsc_diff_max: int
    memory_petsc_diff_sum: int
    memory_petsc_peak_min: int
    memory_petsc_peak_max: int
    memory_petsc_peak_sum: int
    percent: str
    children: Optional[List['Child']]

    @staticmethod
    def from_dict(obj: Any) -> 'Child':
        assert isinstance(obj, dict)
        tag = from_str(obj.get("tag"))
        file_path = from_str(obj.get("file-path"))
        file_line = int(from_str(obj.get("file-line")))
        function = from_str(obj.get("function"))
        cumul_time_min = from_str(obj.get("cumul-time-min"))
        cumul_time_max = from_str(obj.get("cumul-time-max"))
        cumul_time_sum = from_str(obj.get("cumul-time-sum"))
        call_count_min = int(from_str(obj.get("call-count-min")))
        call_count_max = int(from_str(obj.get("call-count-max")))
        call_count_sum = int(from_str(obj.get("call-count-sum")))
        memory_alloc_min = int(from_str(obj.get("memory-alloc-min")))
        memory_alloc_max = int(from_str(obj.get("memory-alloc-max")))
        memory_alloc_sum = int(from_str(obj.get("memory-alloc-sum")))
        memory_dealloc_min = int(from_str(obj.get("memory-dealloc-min")))
        memory_dealloc_max = int(from_str(obj.get("memory-dealloc-max")))
        memory_dealloc_sum = int(from_str(obj.get("memory-dealloc-sum")))
        memory_peak_min = int(from_str(obj.get("memory-peak-min")))
        memory_peak_max = int(from_str(obj.get("memory-peak-max")))
        memory_peak_sum = int(from_str(obj.get("memory-peak-sum")))
        memory_alloc_called_min = int(from_str(obj.get("memory-alloc-called-min")))
        memory_alloc_called_max = int(from_str(obj.get("memory-alloc-called-max")))
        memory_alloc_called_sum = int(from_str(obj.get("memory-alloc-called-sum")))
        memory_dealloc_called_min = int(from_str(obj.get("memory-dealloc-called-min")))
        memory_dealloc_called_max = int(from_str(obj.get("memory-dealloc-called-max")))
        memory_dealloc_called_sum = int(from_str(obj.get("memory-dealloc-called-sum")))
        memory_petsc_diff_min = int(from_str(obj.get("memory-petsc-diff-min")))
        memory_petsc_diff_max = int(from_str(obj.get("memory-petsc-diff-max")))
        memory_petsc_diff_sum = int(from_str(obj.get("memory-petsc-diff-sum")))
        memory_petsc_peak_min = int(from_str(obj.get("memory-petsc-peak-min")))
        memory_petsc_peak_max = int(from_str(obj.get("memory-petsc-peak-max")))
        memory_petsc_peak_sum = int(from_str(obj.get("memory-petsc-peak-sum")))
        percent = from_str(obj.get("percent"))
        children = from_union([lambda x: from_list(Child.from_dict, x), from_none], obj.get("children"))
        return Child(tag, file_path, file_line, function, cumul_time_min, cumul_time_max, cumul_time_sum, call_count_min, call_count_max, call_count_sum, memory_alloc_min, memory_alloc_max, memory_alloc_sum, memory_dealloc_min, memory_dealloc_max, memory_dealloc_sum, memory_peak_min, memory_peak_max, memory_peak_sum, memory_alloc_called_min, memory_alloc_called_max, memory_alloc_called_sum, memory_dealloc_called_min, memory_dealloc_called_max, memory_dealloc_called_sum, memory_petsc_diff_min, memory_petsc_diff_max, memory_petsc_diff_sum, memory_petsc_peak_min, memory_petsc_peak_max, memory_petsc_peak_sum, percent, children)

    def to_dict(self) -> dict:
        result: dict = {}
        result["tag"] = from_str(self.tag)
        result["file-path"] = from_str(self.file_path)
        result["file-line"] = from_str(str(self.file_line))
        result["function"] = from_str(self.function)
        result["cumul-time-min"] = from_str(self.cumul_time_min)
        result["cumul-time-max"] = from_str(self.cumul_time_max)
        result["cumul-time-sum"] = from_str(self.cumul_time_sum)
        result["call-count-min"] = from_str(str(self.call_count_min))
        result["call-count-max"] = from_str(str(self.call_count_max))
        result["call-count-sum"] = from_str(str(self.call_count_sum))
        result["memory-alloc-min"] = from_str(str(self.memory_alloc_min))
        result["memory-alloc-max"] = from_str(str(self.memory_alloc_max))
        result["memory-alloc-sum"] = from_str(str(self.memory_alloc_sum))
        result["memory-dealloc-min"] = from_str(str(self.memory_dealloc_min))
        result["memory-dealloc-max"] = from_str(str(self.memory_dealloc_max))
        result["memory-dealloc-sum"] = from_str(str(self.memory_dealloc_sum))
        result["memory-peak-min"] = from_str(str(self.memory_peak_min))
        result["memory-peak-max"] = from_str(str(self.memory_peak_max))
        result["memory-peak-sum"] = from_str(str(self.memory_peak_sum))
        result["memory-alloc-called-min"] = from_str(str(self.memory_alloc_called_min))
        result["memory-alloc-called-max"] = from_str(str(self.memory_alloc_called_max))
        result["memory-alloc-called-sum"] = from_str(str(self.memory_alloc_called_sum))
        result["memory-dealloc-called-min"] = from_str(str(self.memory_dealloc_called_min))
        result["memory-dealloc-called-max"] = from_str(str(self.memory_dealloc_called_max))
        result["memory-dealloc-called-sum"] = from_str(str(self.memory_dealloc_called_sum))
        result["memory-petsc-diff-min"] = from_str(str(self.memory_petsc_diff_min))
        result["memory-petsc-diff-max"] = from_str(str(self.memory_petsc_diff_max))
        result["memory-petsc-diff-sum"] = from_str(str(self.memory_petsc_diff_sum))
        result["memory-petsc-peak-min"] = from_str(str(self.memory_petsc_peak_min))
        result["memory-petsc-peak-max"] = from_str(str(self.memory_petsc_peak_max))
        result["memory-petsc-peak-sum"] = from_str(str(self.memory_petsc_peak_sum))
        result["percent"] = from_str(self.percent)
        result["children"] = from_union([lambda x: from_list(lambda x: to_class(Child, x), x), from_none], self.children)
        return result


@dataclass
class Profiler:
    program_name: str
    program_version: str
    program_branch: str
    program_revision: str
    program_build: str
    timer_resolution: str
    task_description: str
    task_size: int
    run_process_count: int
    run_started_at: str
    run_finished_at: str
    children: List[Child]

    @staticmethod
    def from_dict(obj: Any) -> 'Profiler':
        assert isinstance(obj, dict)
        program_name = from_str(obj.get("program-name"))
        program_version = from_str(obj.get("program-version"))
        program_branch = from_str(obj.get("program-branch"))
        program_revision = from_str(obj.get("program-revision"))
        program_build = from_str(obj.get("program-build"))
        timer_resolution = from_str(obj.get("timer-resolution"))
        task_description = from_str(obj.get("task-description"))
        task_size = int(from_str(obj.get("task-size")))
        run_process_count = int(from_str(obj.get("run-process-count")))
        run_started_at = from_str(obj.get("run-started-at"))
        run_finished_at = from_str(obj.get("run-finished-at"))
        children = from_list(Child.from_dict, obj.get("children"))
        return Profiler(program_name, program_version, program_branch, program_revision, program_build, timer_resolution, task_description, task_size, run_process_count, run_started_at, run_finished_at, children)

    def to_dict(self) -> dict:
        result: dict = {}
        result["program-name"] = from_str(self.program_name)
        result["program-version"] = from_str(self.program_version)
        result["program-branch"] = from_str(self.program_branch)
        result["program-revision"] = from_str(self.program_revision)
        result["program-build"] = from_str(self.program_build)
        result["timer-resolution"] = from_str(self.timer_resolution)
        result["task-description"] = from_str(self.task_description)
        result["task-size"] = from_str(str(self.task_size))
        result["run-process-count"] = from_str(str(self.run_process_count))
        result["run-started-at"] = from_str(self.run_started_at)
        result["run-finished-at"] = from_str(self.run_finished_at)
        result["children"] = from_list(lambda x: to_class(Child, x), self.children)
        return result


def profiler_from_dict(s: Any) -> Profiler:
    return Profiler.from_dict(s)


def profiler_to_dict(x: Profiler) -> Any:
    return to_class(Profiler, x)
