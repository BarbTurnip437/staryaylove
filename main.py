version_info = (0, 1, 0)
__version__ = ".".join(map(str, version_info))

import json
import operator
import re
import time
import tomllib
from contextlib import chdir
from pathlib import Path
from typing import Callable, Iterable, Sequence, Optional

from type_annotations import *

DATA_PATH = Path("data")
ROLE_PATH = DATA_PATH / "role"
ROLE_MAIN = ROLE_PATH / "main.toml"
FLAG_INIT_FILE = DATA_PATH / "flag_init.toml"
PROJECT_FILE = DATA_PATH / "project.toml"
SAVE_FILE = Path("save.json")
FLAGS_DEFAULT: FlagsFormat = {
    "sys": {
        "file": str(ROLE_MAIN.relative_to(ROLE_PATH)),
    }
}
FUNCTION_MAPPING: dict[str, Callable] = {
    "abs": operator.abs,
    "add": operator.add,
    "and": operator.and_,
    "attrgetter": operator.attrgetter,
    "call": operator.call,
    "concat": operator.concat,
    "contains": operator.contains,
    "countOf": operator.countOf,
    "delitem": operator.delitem,
    "eq": operator.eq,
    "floordiv": operator.floordiv,
    "ge": operator.ge,
    "getitem": operator.getitem,
    "gt": operator.gt,
    "iadd": operator.iadd,
    "iand": operator.iand,
    "iconcat": operator.iconcat,
    "ifloordiv": operator.ifloordiv,
    "ilshift": operator.ilshift,
    "imatmul": operator.imatmul,
    "imod": operator.imod,
    "imul": operator.imul,
    "index": operator.index,
    "index_of": operator.indexOf,
    "inv": operator.inv,
    "invert": operator.invert,
    "ior": operator.ior,
    "ipow": operator.ipow,
    "irshift": operator.irshift,
    "is": operator.is_,
    "is_none": operator.is_none,
    "is_not": operator.is_not,
    "is_not_none": operator.is_not_none,
    "isub": operator.isub,
    "itemgetter": operator.itemgetter,
    "itruediv": operator.itruediv,
    "ixor": operator.ixor,
    "le": operator.le,
    "length_hint": operator.length_hint,
    "lshift": operator.lshift,
    "lt": operator.lt,
    "matmul": operator.matmul,
    "methodcaller": operator.methodcaller,
    "mod": operator.mod,
    "mul": operator.mul,
    "ne": operator.ne,
    "neg": operator.neg,
    "not": operator.not_,
    "or": operator.or_,
    "pos": operator.pos,
    "pow": operator.pow,
    "rshift": operator.rshift,
    "setitem": operator.setitem,
    "sub": operator.sub,
    "truediv": operator.truediv,
    "truth": operator.truth,
    "xor": operator.xor,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "max_value": lambda d: (
        max(d.values()) if isinstance(d, dict) and d else None
    ),
    "max_value_key": lambda d: (
        max(d.items(), key=lambda item: item[1])[0]
        if isinstance(d, dict) and d
        else None
    ),
    "min_value": lambda d: (
        min(d.values()) if isinstance(d, dict) and d else None
    ),
    "min_value_key": lambda d: (
        min(d.items(), key=lambda item: item[1])[0]
        if isinstance(d, dict) and d
        else None
    ),
}


class Save:
    @staticmethod
    def load() -> SaveFormat:
        with SAVE_FILE.open(encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def dump(flags: FlagsFormat):
        with SAVE_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "meta": {"version": version_info},
                    "data": {"flags": flags},
                },
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )


def load_data(path: str) -> DataFormat:
    with open(path, "rb") as f:
        return tomllib.load(f)  # pyright: ignore[reportReturnType]


def slow_print(text: Iterable, interval: Optional[float] = None):
    """进行逐字输出"""
    if interval is None:
        interval = 0.04

    for char in text:
        try:
            print(char, end="", flush=True)
            time.sleep(interval)
        except KeyboardInterrupt:
            interval /= 10


def flags_init_valid(d: dict[str, Any]) -> bool:
    for key, value in d.items():
        if "." in key:
            return False
        if isinstance(value, dict):
            if not flags_init_valid(value):
                return False

    return True


def run_actions(
    flags: FlagsFormat,
    actions: Sequence[DataActionFormat],
    user_input: str,
) -> FlagsFormat:
    def apply_operation(full_flag: str, op):
        """Recursively apply an operation for a flag path."""
        parts = [p.strip('"') for p in full_flag.split(".")]
        # Navigate to target container, ensuring each intermediate key exists
        target = flags
        for p in parts[:-1]:
            if p not in target:
                raise KeyError(
                    f"Flag path {full_flag} not found at segment {p}"
                )
            target = target[p]
        key = parts[-1]
        if isinstance(op, (list, tuple)):
            func_name = op[0]
            func = FUNCTION_MAPPING.get(func_name)
            if func is None:
                raise KeyError(
                    f"Function {func_name} not found in FUNCTION_MAPPING"
                )
            resolved_args = []
            for arg in op[1:]:
                if isinstance(arg, str) and arg.startswith("$"):
                    path = arg[1:]
                    sub_parts = [sp.strip('"') for sp in path.split(".")]
                    val = flags
                    for sp in sub_parts:
                        val = val[sp]
                    resolved_args.append(val)
                else:
                    resolved_args.append(arg)
            target[key] = func(*resolved_args)
        elif isinstance(op, dict):
            for sub_key, sub_op in op.items():
                apply_operation(f"{full_flag}.{sub_key}", sub_op)
        else:
            target[key] = op

    ran_action = False

    for action in actions:
        requirement = action.get("requirement", {})
        input_pattern = requirement.get("input_pattern")
        capture = requirement.get("capture")
        # Evaluate flag_conditions if present
        flag_conditions = requirement.get("flag_conditions", [])
        if flag_conditions:
            all_pass = True
            for cond in flag_conditions:
                if not isinstance(cond, list) and not cond:
                    all_pass = False
                    break
                func_name = cond[0]
                func = FUNCTION_MAPPING[func_name]
                args = []
                for arg in cond[1:]:
                    if isinstance(arg, str) and arg.startswith("$"):
                        path = arg[1:]
                        sub_parts = [sp.strip('"') for sp in path.split(".")]
                        val = flags
                        for sp in sub_parts:
                            val = val[sp]
                        args.append(val)
                    else:
                        args.append(arg)
                if not func(*args):
                    all_pass = False
                    break
            if not all_pass:
                continue
        if (
            input_pattern is not None
            and re.match(input_pattern, user_input) is None
        ):
            continue
        if capture == ran_action:
            continue

        ran_action = action.get("set_ran_action", True)

        goto = action.get("goto")
        if goto is not None:
            flags["sys"]["file"] = goto + ".toml"

        exit = action.get("exit")
        if exit is not None:
            flags["sys"]["exit"] = exit

        text = action.get("text")
        interval = action.get("interval")
        if text is not None:
            slow_print(text, interval)

        require_input = action.get("require_input")
        if require_input:
            user_input = input()

        flag_operations = action.get("flag_operations", {})
        for flag, operation in flag_operations.items():
            apply_operation(flag, operation)

    return flags


def run_role(flags: FlagsFormat) -> FlagsFormat:
    with chdir(ROLE_PATH):
        data = load_data(flags["sys"]["file"])

    slow_print(data["text"], data.get("interval"))
    if data.get("require_input", True):
        user_input = input()
    else:
        user_input = ""

    if (actions := data.get("actions")) is not None:
        flags = run_actions(flags, actions, user_input)

    return flags


def main():
    with PROJECT_FILE.open("rb") as f:
        project: ProjectFormat = tomllib.load(f)  # type: ignore

    print(project["name"])
    print("1. 新游戏")
    print("2. 继续游戏")

    while True:
        user_input = input("> ").strip()
        if user_input == "1":
            with FLAG_INIT_FILE.open("rb") as f:
                flags_declare = tomllib.load(f)
            if not flags_init_valid(flags_declare):
                raise SyntaxError("你不能初始化名称带“.”的标志")
            flags = FLAGS_DEFAULT
            flags.update(flags_declare)  # type: ignore
            break
        elif user_input == "2":
            try:
                flags = Save.load()["data"]["flags"]
            except FileNotFoundError:
                print("存档不存在请，先创建新存档。")
            else:
                break
        else:
            print("未知的输入，请重新输入。")

    try:
        while flags["sys"].get("exit") is None:
            flags = run_role(flags)
            Save.dump(flags)
    except KeyboardInterrupt:
        print("退出...")


if __name__ == "__main__":
    main()
