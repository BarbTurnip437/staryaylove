# 豆芽人联盟：星芽之约 —— staryaylove

《豆芽人联盟：星芽之约》是一款使用 python 打造的文本型 galgame。  
所有角色名称及剧情版权归豆芽人联盟。

## 配置文件格式

配置文件全部使用 toml 格式。  
以下图表中的文件是必须存在的。

- main.py
- data/
  - flag_init.toml
  - project.toml
  - role/
    - main.toml

- data/flag_init.toml 存放的是标志的初始化。
- data/project.toml 应当只包含一个字段 —— name，为刚开始启动程序时输出的第一句话
- data/role/main.toml 是 role 的入口点，role 下的文件格式将会在下文说明。

由于我真的太懒了下文由AI生成。

## 配置文件格式详解

### 概述

配置文件全部使用 **TOML** 格式。TOML 是一种语义清晰的极简配置文件格式，易于阅读和编写。

配置文件由 Python 标准库的 [`tomllib`](https://docs.python.org/3/library/tomllib.html) 模块进行解析（Python 3.11+）。

### 文件结构

```
data/
├── project.toml          # 项目配置（启动标题）
├── flag_init.toml        # 标志（flags）初始化文件
└── role/
    ├── main.toml         # 剧情入口点
    ├── chapter/          # 章节剧情
    ├── route/            # 角色路线
    └── ending/           # 结局
```

---

### 1. project.toml

项目配置文件，仅包含一个字段：

```toml
name = "游戏标题"
```

**解析方式**：在 [`main()`](main.py:281) 函数中加载，程序启动时输出 `name` 字段内容。

---

### 2. flag_init.toml

标志（flags）初始化文件，用于定义新游戏时的初始状态。

**示例**：
```toml
progress = 0

[likeability]
"千日坂芷芽" = 0
"渚浔笑辞" = 0
```

**解析规则**：
- 支持嵌套的表（table）结构
- 键名不能包含 `.` 字符（由 [`flags_init_valid()`](main.py:146) 函数验证）
- 在 [`main()`](main.py:281) 函数中加载，与系统默认标志合并

---

### 3. role/*.toml（剧情文件）

剧情文件是游戏的核心，每个文件代表一个剧情节点。

#### 3.1 基本结构

```toml
text = """剧情文本内容"""
interval = 0.04          # 可选：逐字打印间隔（秒）
require_input = true     # 可选：是否需要用户输入，默认 true
```

#### 3.2 actions 数组

`actions` 是一个数组，定义用户输入后的分支逻辑：

```toml
[[actions]]
requirement = { input_pattern = '^1' }
goto = "chapter/1"
```

**`actions` 字段说明**：

| 字段              | 类型   | 说明                                                           |
| ----------------- | ------ | -------------------------------------------------------------- |
| `requirement`     | 对象   | 执行条件                                                       |
| `goto`            | 字符串 | 跳转到指定剧情文件（相对于 `data/role/` 的路径，不含 `.toml`） |
| `exit`            | 整数   | 设置退出标志，结束游戏循环                                     |
| `text`            | 字符串 | 要输出的文本                                                   |
| `interval`        | 浮点数 | 逐字打印间隔                                                   |
| `require_input`   | 布尔值 | 是否需要用户输入                                               |
| `set_ran_action`  | 布尔值 | 是否标记为已执行，默认为 `true`                                |
| `flag_operations` | 对象   | 标志操作                                                       |

**`requirement` 字段说明**：

| 字段              | 类型   | 说明                                 |
| ----------------- | ------ | ------------------------------------ |
| `input_pattern`   | 字符串 | 正则表达式，匹配用户输入             |
| `capture`         | 布尔值 | 捕获所有未匹配的输入（作为默认分支） |
| `flag_conditions` | 数组   | 标志条件检查                         |

#### 3.3 flag_operations（标志操作）

用于修改游戏状态标志：

```toml
[actions.flag_operations]
progress = 10
likeability."千日坂芷芽" = ["add", "$likeability.千日坂芷芽", 5]
```

**操作格式**：
- **直接赋值**：`flag_name = 值`
- **函数调用**：`flag_name = ["函数名", 参数 1, 参数 2, ...]`
  - 使用 `$` 引用其他标志：`$likeability.千日坂芷芽`
  - 支持的函数见下方「可用函数列表」

#### 3.4 解析流程

1. [`run_role()`](main.py:265) 函数根据 `flags["sys"]["file"]` 加载对应的 TOML 文件
2. 输出 `text` 字段内容（使用 [`slow_print()`](main.py:133) 逐字打印）
3. 如果需要输入，等待用户输入
4. [`run_actions()`](main.py:157) 函数遍历 `actions` 数组：
   - 检查 `requirement.input_pattern` 是否匹配用户输入
   - 检查 `requirement.flag_conditions` 是否满足
   - 执行匹配的动作（`goto`、`exit`、`text`、`flag_operations` 等）

---

### 4. 可用函数列表

在 `flag_operations` 中可调用的函数（定义于 [`FUNCTION_MAPPING`](main.py:26)）：

**运算符**：`abs`, `add`, `and`, `concat`, `contains`, `eq`, `floordiv`, `ge`, `gt`, `le`, `lt`, `matmul`, `mod`, `mul`, `ne`, `or`, `pow`, `sub`, `truediv`, `xor` 等

**类型转换**：`int`, `float`, `str`, `bool`

**字典操作**：`max_value`, `max_value_key`, `min_value`, `min_value_key`

**其他**：`attrgetter`, `itemgetter`, `methodcaller` 等

---

### 5. 存档格式（save.json）

游戏进度保存在 `save.json` 文件中：

```json
{
  "meta": {
    "version": [0, 1, 0]
  },
  "data": {
    "flags": {
      "sys": {
        "file": "chapter/1.toml"
      },
      "progress": 10,
      "likeability": {
        "千日坂芷芽": 5
      }
    }
  }
}
```

---
