# 研究深度点数系统

## 功能概述

本功能实现了根据研究深度级别（1-5级）来消耗不同点数的扣点系统。研究深度级别越高，分析越详细，消耗的点数也越多。

## 功能特点

- ✅ **基于研究深度的点数计算**：根据研究深度级别（1-5级）计算消耗的点数
- ✅ **默认点数配置**：
  - 1级 - 快速分析：1点
  - 2级 - 基础分析：2点
  - 3级 - 标准分析：3点
  - 4级 - 深度分析：5点
  - 5级 - 全面分析：8点
- ✅ **可配置**：管理员可以在配置管理界面修改各研究深度级别的点数
- ✅ **用户界面提示**：在分析表单中显示不同研究深度对应的点数消耗
- ✅ **批量分析支持**：批量分析时根据研究深度和股票数量计算总点数消耗

## 实现细节

### 1. 核心函数

#### `get_research_depth_points(research_depth: int) -> int`
根据研究深度级别获取消耗的点数。

**参数**：
- `research_depth`: 研究深度级别（1-5）

**返回**：
- 消耗的点数

**示例**：
```python
from web.utils.model_points import get_research_depth_points

# 获取1级研究深度消耗的点数
points = get_research_depth_points(1)  # 返回 1

# 获取5级研究深度消耗的点数
points = get_research_depth_points(5)  # 返回 8
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
在 `web/app.py` 中，单股票分析的扣点逻辑已更新为基于研究深度：

```python
from utils.model_points import get_research_depth_points

research_depth = form_data.get('research_depth', 3)
points_cost = get_research_depth_points(research_depth)

if not auth_manager.try_deduct_points(username, points_cost):
    st.error(f"点数不足，需要 {points_cost} 点（研究深度 {research_depth} 级）")
    return
```

#### 批量分析
批量分析时，总点数 = 股票数量 × 研究深度点数：

```python
research_depth = form_data.get('research_depth', 3)
points_per_stock = get_research_depth_points(research_depth)
need_points = len(stock_symbols) * points_per_stock
```

### 4. 用户界面

#### 分析表单
在单股票分析表单中，研究深度选择器会显示每个级别对应的点数：

- 1级 - 快速分析 (1点)
- 2级 - 基础分析 (2点)
- 3级 - 标准分析 (3点)
- 4级 - 深度分析 (5点)
- 5级 - 全面分析 (8点)

#### 批量分析表单
在批量分析表单中，除了显示每个级别的点数外，还会在解析股票代码后显示预估的总点数消耗。

### 5. 配置管理

管理员可以在配置管理界面的"研究深度点数设置"页面中：
- 查看当前所有研究深度级别的点数配置
- 编辑特定级别的点数配置
- 查看默认配置说明

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

## 研究深度级别说明

| 级别 | 名称 | 默认点数 | 说明 |
|------|------|---------|------|
| 1级 | 快速分析 | 1点 | 最快速度，最低成本，适合日常快速决策 |
| 2级 | 基础分析 | 2点 | 速度较快，成本较低，适合常规投资决策 |
| 3级 | 标准分析 | 3点 | 平衡速度和质量，适合重要投资决策 |
| 4级 | 深度分析 | 5点 | 分析深度高，成本较高，适合重大投资决策 |
| 5级 | 全面分析 | 8点 | 最全面的分析，成本最高，适合最重要的投资决策 |

## 注意事项

1. **点数验证**：在开始分析前，系统会检查用户是否有足够的点数
2. **扣点时机**：点数在分析开始前扣除，如果分析失败不会退还点数
3. **管理员账户**：管理员账户不扣减点数，直接返回成功
4. **配置缓存**：配置修改后需要调用 `reload_config()` 刷新缓存

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

