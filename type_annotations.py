from typing import Any, NotRequired, Optional, TypeAlias, TypedDict


class FlagsSysFormat(TypedDict):
    file: str
    exit: NotRequired[Optional[int]]


class FlagsRequiredFormat(TypedDict):
    sys: FlagsSysFormat


FlagsFormat: TypeAlias = FlagsRequiredFormat | dict[str, Any]


class DataActionRequirementsFormat(TypedDict):
    input_pattern: NotRequired[str]
    capture: NotRequired[bool]
    flag_conditions: list[FlagOperation]


FlagOperation: TypeAlias = Any | list[str | Any]


class DataActionFormat(TypedDict):
    requirement: NotRequired[DataActionRequirementsFormat]
    goto: NotRequired[str]
    exit: NotRequired[int]
    text: NotRequired[str]
    interval: NotRequired[float]
    require_input: NotRequired[bool]
    set_ran_action: NotRequired[bool]
    flag_operations: NotRequired[dict[str, FlagOperation]]


class DataFormat(TypedDict):
    text: str
    interval: NotRequired[float]
    require_input: NotRequired[bool]
    actions: NotRequired[list[DataActionFormat]]


class ProjectFormat(TypedDict):
    name: str


class SaveMetaFormat(TypedDict):
    version: tuple[int, int, int]


class SavedataFormat(TypedDict):
    flags: FlagsFormat


class SaveFormat(TypedDict):
    meta: SaveMetaFormat
    data: SavedataFormat
