# 环境变量配置管理功能

## 功能概述

在管理员界面中直接配置和管理`.env`文件中的环境变量，无需手动编辑文件。支持分类显示、安全编辑、批量导入导出等功能。

## 功能特性

### 核心功能
- ✅ 分类显示环境变量（LLM API密钥、数据源API、数据库配置等）
- ✅ 安全编辑敏感信息（API密钥使用密码输入框）
- ✅ 实时验证配置值格式
- ✅ 自动备份功能
- ✅ 批量导入/导出.env文件
- ✅ 保留注释和格式

### 安全特性
- 🔒 敏感信息（API密钥、密码）使用密码输入框
- 🔒 显示时只显示部分字符（如：`***1234`）
- 🔒 自动验证配置格式
- 🔒 修改前自动备份

## 使用方法

### 访问配置页面

1. 登录管理员账户
2. 进入 **配置管理** → **环境变量配置**

### 编辑单个环境变量

1. 在相应的分类标签页中找到要编辑的变量
2. 点击变量名称展开编辑区域
3. 在输入框中输入新值
4. 点击 **💾 保存** 按钮
5. 系统会验证值格式，验证通过后保存

### 删除环境变量

1. 展开要删除的变量
2. 点击 **🗑️ 删除** 按钮
3. 变量将被设置为空值

### 重置为默认值

1. 展开要重置的变量
2. 点击 **🔄 重置** 按钮（仅对有默认值的变量显示）
3. 变量将被重置为默认值

### 备份.env文件

1. 点击 **💾 备份.env文件** 按钮
2. 系统会创建带时间戳的备份文件
3. 备份文件保存在.env文件同目录下

### 导出.env文件

1. 点击 **📥 导出.env文件** 按钮
2. 点击 **💾 下载.env文件** 按钮下载

### 导入.env文件

1. 点击 **选择.env文件** 上传文件
2. 系统会自动解析文件内容
3. 显示检测到的环境变量数量
4. 点击 **📤 导入配置** 按钮
5. 系统会自动备份现有配置后导入新配置

## 环境变量分类

### LLM API密钥
- DASHSCOPE_API_KEY - 阿里百炼
- OPENAI_API_KEY - OpenAI
- GOOGLE_API_KEY - Google AI
- ANTHROPIC_API_KEY - Anthropic
- DEEPSEEK_API_KEY - DeepSeek
- SILICONFLOW_API_KEY - 硅基流动
- QIANFAN_API_KEY - 百度千帆

### 数据源API密钥
- FINNHUB_API_KEY - Finnhub（美股数据）
- TUSHARE_TOKEN - Tushare（A股/港股数据）

### 社交媒体API
- REDDIT_CLIENT_ID - Reddit客户端ID
- REDDIT_CLIENT_SECRET - Reddit客户端密钥

### 数据库配置
- MONGODB_HOST - MongoDB主机地址
- MONGODB_PORT - MongoDB端口
- MONGODB_USERNAME - MongoDB用户名
- MONGODB_PASSWORD - MongoDB密码
- MONGODB_DATABASE - MongoDB数据库名
- MONGODB_AUTH_SOURCE - MongoDB认证源
- TRADINGAGENTS_REDIS_URL - Redis连接URL

### 系统配置
- TRADINGAGENTS_LOG_LEVEL - 日志级别
- TRADINGAGENTS_LOG_DIR - 日志目录
- TRADINGAGENTS_RESULTS_DIR - 结果目录
- OPENAI_ENABLED - 是否启用OpenAI
- DOCKER_CONTAINER - 是否在Docker中运行

### 其他配置
- 未分类的自定义环境变量

## 配置验证规则

### 环境变量名验证
- 必须全大写字母、数字和下划线
- 不能以数字开头
- 格式示例：`DASHSCOPE_API_KEY` ✅

### 特定变量验证

#### MONGODB_PORT
- 必须是整数
- 范围：1-65535

#### TRADINGAGENTS_LOG_LEVEL
- 必须是：DEBUG, INFO, WARNING, ERROR, CRITICAL

#### OPENAI_ENABLED / DOCKER_CONTAINER
- 必须是：true/false, 1/0, yes/no

## 注意事项

### ⚠️ 重要提示

1. **重启应用**：修改.env文件后，需要重启应用才能生效
2. **敏感信息**：API密钥等敏感信息请妥善保管，不要泄露
3. **备份建议**：修改前建议先备份.env文件
4. **删除变量**：删除变量会将其设置为空值，不会从文件中移除
5. **文件格式**：系统会自动处理包含空格、引号等特殊字符的值

### 最佳实践

1. **定期备份**：在大量修改前，先备份.env文件
2. **测试环境**：建议先在测试环境验证配置
3. **版本控制**：不要将.env文件提交到版本控制系统
4. **权限管理**：确保只有管理员可以访问配置页面

## 常见问题

### Q: 修改后为什么没有生效？
A: 修改.env文件后需要重启应用才能生效。请重启Web应用。

### Q: 如何恢复误删的配置？
A: 可以使用备份功能恢复，或者从备份文件导入。

### Q: 可以添加自定义环境变量吗？
A: 可以。自定义变量会显示在"其他配置"分类中。

### Q: 导入.env文件会覆盖现有配置吗？
A: 是的。导入时会自动备份现有配置，然后完全替换为新配置。

### Q: 敏感信息如何安全显示？
A: 敏感信息（API密钥等）使用密码输入框，显示时只显示最后4位字符。

### Q: 可以批量编辑多个变量吗？
A: 目前支持批量导入/导出，单个编辑需要逐个操作。

## 技术实现

### 核心类
- `EnvConfigManager`: 环境变量管理器
  - `load_env_variables()`: 加载所有环境变量
  - `set_env_variable()`: 设置单个环境变量
  - `delete_env_variable()`: 删除环境变量
  - `save_env_variables()`: 批量保存环境变量
  - `validate_env_variable()`: 验证环境变量格式
  - `backup_env_file()`: 备份.env文件

### 文件处理
- 使用`python-dotenv`库处理.env文件
- 保留原始文件的注释和格式
- 自动处理特殊字符（空格、引号等）

### 安全措施
- 敏感信息使用密码输入框
- 显示时只显示部分字符
- 自动验证配置格式
- 修改前自动备份

## 更新日志

- **v1.0** (2025-01-15): 初始版本
  - 支持分类显示环境变量
  - 支持单个和批量编辑
  - 支持导入/导出.env文件
  - 支持自动备份
  - 支持配置验证

