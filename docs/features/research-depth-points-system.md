# 研究深度点数系统

## 功能概述

本功能实现了根据研究深度级别（1-5级）来消耗不同点数的扣点系统。研究深度级别越高，分析越详细，消耗的点数也越多。

## 功能特点

- ✅ **组合点数计算**：根据研究深度级别（1-5级）和选择的模型计算消耗的点数
- ✅ **计算公式**：总点数 = 研究深度基础点数 + 模型点数（根据开关状态）
- ✅ **点数消耗开关**：可以独立控制研究深度点数和模型点数的消耗
  - 启用研究深度点数消耗：研究深度级别会消耗点数
  - 启用模型点数消耗：模型选择会消耗点数
  - 两个开关都可以独立开启或关闭
- ✅ **研究深度默认点数配置**：
  - 1级 - 快速分析：1点（基础）
  - 2级 - 基础分析：2点（基础）
  - 3级 - 标准分析：3点（基础）
  - 4级 - 深度分析：5点（基础）
  - 5级 - 全面分析：8点（基础）
- ✅ **模型点数**：根据选择的LLM模型额外消耗点数（如 qwen-turbo: 1点, qwen-max: 3点等）
- ✅ **可配置**：管理员可以在配置管理界面修改各研究深度级别和模型的点数，以及开关状态
- ✅ **用户界面提示**：在分析表单中根据开关状态显示研究深度和模型组合的总点数消耗
- ✅ **批量分析支持**：批量分析时根据研究深度、模型和股票数量计算总点数消耗

## 实现细节

### 1. 核心函数

#### `get_analysis_points(research_depth: int, llm_provider: str = None, llm_model: str = None) -> int`
获取分析消耗的总点数（研究深度 + 模型选择）。

**参数**：
- `research_depth`: 研究深度级别（1-5）
- `llm_provider`: LLM提供商（可选，如果提供则会加上模型点数）
- `llm_model`: 模型名称（可选，如果提供则会加上模型点数）

**返回**：
- 消耗的总点数 = 研究深度基础点数 + 模型点数

**示例**：
```python
from web.utils.model_points import get_analysis_points

# 获取3级研究深度 + qwen-max 模型的总点数
points = get_analysis_points(3, 'dashscope', 'qwen-max')  # 返回 6 (3 + 3)

# 只获取研究深度基础点数（不提供模型信息）
points = get_analysis_points(3)  # 返回 3
```

#### `get_research_depth_points(research_depth: int) -> int`
根据研究深度级别获取基础点数。

**参数**：
- `research_depth`: 研究深度级别（1-5）

**返回**：
- 研究深度基础点数

**示例**：
```python
from web.utils.model_points import get_research_depth_points

# 获取1级研究深度基础点数
points = get_research_depth_points(1)  # 返回 1

# 获取5级研究深度基础点数
points = get_research_depth_points(5)  # 返回 8
```

#### `get_model_points(llm_provider: str, llm_model: str) -> int`
根据模型获取消耗的点数。

**参数**：
- `llm_provider`: LLM提供商
- `llm_model`: 模型名称

**返回**：
- 模型点数

**示例**：
```python
from web.utils.model_points import get_model_points

# 获取 qwen-max 模型的点数
points = get_model_points('dashscope', 'qwen-max')  # 返回 3

# 获取 qwen-turbo 模型的点数
points = get_model_points('dashscope', 'qwen-turbo')  # 返回 1
```

### 2. 配置文件

研究深度点数配置存储在 `web/config/model_points.json` 文件中：

```json
{
  "version": "1.0",
  "research_depth_points": {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 5,
    "5": 8
  }
}
```

### 3. 扣点逻辑

#### 单股票分析
在 `web/app.py` 中，单股票分析的扣点逻辑已更新为基于研究深度和模型：

```python
from utils.model_points import get_analysis_points

research_depth = form_data.get('research_depth', 3)
llm_provider = st.session_state.get('llm_provider', 'dashscope')
llm_model = st.session_state.get('llm_model', 'qwen-turbo')
points_cost = get_analysis_points(research_depth, llm_provider, llm_model)

if not auth_manager.try_deduct_points(username, points_cost):
    st.error(f"点数不足，需要 {points_cost} 点（研究深度 {research_depth} 级 + 模型）")
    return
```

#### 批量分析
批量分析时，总点数 = 股票数量 × (研究深度基础点数 + 模型点数)：

```python
research_depth = form_data.get('research_depth', 3)
llm_provider = st.session_state.get('llm_provider', 'dashscope')
llm_model = st.session_state.get('llm_model', 'qwen-turbo')
points_per_stock = get_analysis_points(research_depth, llm_provider, llm_model)
need_points = len(stock_symbols) * points_per_stock
```

### 4. 用户界面

#### 分析表单
在单股票分析表单中：
- 研究深度选择器显示每个级别的基础点数（如：1级 - 快速分析 (1点基础)）
- 实时显示总点数消耗：研究深度基础点数 + 模型点数
- 例如：3级研究深度 (3点) + qwen-max模型 (3点) = 6点

#### 批量分析表单
在批量分析表单中：
- 显示每个研究深度级别的基础点数
- 显示每个股票的总点数消耗（研究深度 + 模型）
- 在解析股票代码后显示预估的总点数消耗 = 股票数量 × (研究深度基础点数 + 模型点数)

### 5. 配置管理

管理员可以在配置管理界面的"研究深度点数设置"页面中：
- 查看当前所有研究深度级别的点数配置
- 编辑特定级别的点数配置
- **设置点数消耗开关**：
  - 启用/禁用研究深度点数消耗
  - 启用/禁用模型点数消耗
- 查看默认配置说明

### 6. 点数消耗开关

#### 开关配置
管理员可以在"研究深度点数设置"页面中控制两个独立的开关：
- **启用研究深度点数消耗**：控制研究深度级别是否消耗点数
- **启用模型点数消耗**：控制模型选择是否消耗点数

#### 开关状态说明
- **两个都启用**：总点数 = 研究深度基础点数 + 模型点数
- **只启用研究深度**：总点数 = 研究深度基础点数
- **只启用模型**：总点数 = 模型点数
- **两个都关闭**：总点数 = 0（不消耗点数）

#### 配置函数
```python
from web.utils.model_points import set_points_toggle_config

# 启用研究深度点数消耗，禁用模型点数消耗
set_points_toggle_config(enable_research_depth_points=True, enable_model_points=False)

# 只修改研究深度点数开关
set_points_toggle_config(enable_research_depth_points=False)

# 获取当前开关状态
from web.utils.model_points import get_points_toggle_config
config = get_points_toggle_config()
# 返回: {"enable_research_depth_points": True, "enable_model_points": True}
```

## 使用示例

### 修改研究深度点数配置

```python
from web.utils.model_points import set_research_depth_points

# 将1级研究深度的点数设置为2点
set_research_depth_points(1, 2)

# 将5级研究深度的点数设置为10点
set_research_depth_points(5, 10)
```

### 获取所有研究深度点数配置

```python
from web.utils.model_points import get_all_research_depth_points

# 获取所有配置
all_config = get_all_research_depth_points()
# 返回: {1: 1, 2: 2, 3: 3, 4: 5, 5: 8}
```

## 点数计算说明

### 计算公式
**总点数 = 研究深度基础点数 + 模型点数**

### 研究深度基础点数

| 级别 | 名称 | 基础点数 | 说明 |
|------|------|---------|------|
| 1级 | 快速分析 | 1点 | 最快速度，最低基础成本，适合日常快速决策 |
| 2级 | 基础分析 | 2点 | 速度较快，基础成本较低，适合常规投资决策 |
| 3级 | 标准分析 | 3点 | 平衡速度和质量，基础成本中等，适合重要投资决策 |
| 4级 | 深度分析 | 5点 | 分析深度高，基础成本较高，适合重大投资决策 |
| 5级 | 全面分析 | 8点 | 最全面的分析，基础成本最高，适合最重要的投资决策 |

### 模型点数示例

| 提供商 | 模型 | 点数 | 说明 |
|--------|------|------|------|
| dashscope | qwen-turbo | 1点 | 快速模型 |
| dashscope | qwen-plus | 2点 | 平衡模型 |
| dashscope | qwen-max | 3点 | 高质量模型 |
| google | gemini-2.5-flash | 2点 | 快速模型 |
| google | gemini-2.5-pro | 4点 | 高质量模型 |
| openai | gpt-4o | 5点 | 最高质量模型 |
| openrouter | anthropic/claude-3.7-sonnet | 5点 | Claude 3.7 Sonnet |
| openrouter | anthropic/claude-opus-4 | 8点 | Claude 4 Opus（顶级） |
| openrouter | anthropic/claude-3.5-sonnet | 4点 | Claude 3.5 Sonnet |
| openrouter | openai/gpt-4o | 5点 | GPT-4o |
| openrouter | openai/gpt-4-turbo | 4点 | GPT-4 Turbo |
| openrouter | openai/gpt-3.5-turbo | 1点 | GPT-3.5 Turbo |
| openrouter | default | 2点 | 其他OpenRouter模型（默认） |

### 计算示例

#### 两个开关都启用（默认）
- **1级研究深度 + qwen-turbo** = 1 + 1 = **2点**
- **3级研究深度 + qwen-max** = 3 + 3 = **6点**
- **5级研究深度 + gpt-4o** = 8 + 5 = **13点**
- **批量分析（3个股票，3级研究深度，qwen-max）** = 3 × (3 + 3) = **18点**

#### 只启用研究深度点数
- **1级研究深度 + qwen-turbo** = 1 + 0 = **1点**
- **3级研究深度 + qwen-max** = 3 + 0 = **3点**
- **5级研究深度 + gpt-4o** = 8 + 0 = **8点**

#### 只启用模型点数
- **1级研究深度 + qwen-turbo** = 0 + 1 = **1点**
- **3级研究深度 + qwen-max** = 0 + 3 = **3点**
- **5级研究深度 + gpt-4o** = 0 + 5 = **5点**

#### 两个开关都关闭
- **任意研究深度 + 任意模型** = 0 + 0 = **0点**（不消耗点数）

## 注意事项

1. **点数验证**：在开始分析前，系统会检查用户是否有足够的点数（如果开关启用）
2. **扣点时机**：点数在分析开始前扣除，如果分析失败不会退还点数
3. **管理员账户**：管理员账户不扣减点数，直接返回成功
4. **配置缓存**：配置修改后需要调用 `reload_config()` 刷新缓存
5. **开关状态**：如果两个开关都关闭，分析将不消耗任何点数，可以直接开始分析
6. **开关影响**：开关状态的修改会立即生效，影响所有后续的分析请求
7. **OpenRouter模型**：OpenRouter模型使用精确匹配，如果找不到精确匹配，会使用default配置（2点）。常见模型如Claude、GPT-4o等已配置具体点数。

## 相关文件

- `web/utils/model_points.py` - 研究深度点数配置和函数
- `web/app.py` - 扣点逻辑实现
- `web/components/analysis_form.py` - 单股票分析表单
- `web/components/batch_analysis_form.py` - 批量分析表单
- `web/modules/config_management.py` - 配置管理界面
- `web/config/model_points.json` - 配置文件（如果存在）

## 未来改进

1. 支持根据分析师数量动态调整点数
2. 支持根据市场类型（A股、美股、港股）设置不同的点数
3. 添加点数消耗历史记录
4. 支持点数套餐和优惠活动

