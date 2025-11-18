import json
import time
from pathlib import Path
from datetime import datetime
from io import BytesIO
import streamlit as st
import pandas as pd

# 认证与日志
try:
    from web.utils.auth_manager import auth_manager
except Exception:
    from ..utils.auth_manager import auth_manager  # type: ignore


USERS_FILE = Path(__file__).parent.parent / "config" / "users.json"


def _load_users() -> dict:
	try:
		if USERS_FILE.exists():
			return json.loads(USERS_FILE.read_text(encoding="utf-8"))
		return {}
	except Exception as e:
		st.error(f"读取用户数据失败: {e}")
		return {}


def _save_users(users: dict) -> bool:
	try:
		USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
		json_content = json.dumps(users, ensure_ascii=False, indent=2)
		USERS_FILE.write_text(json_content, encoding="utf-8")
		# 验证写入是否成功：重新读取并检查文件内容
		if USERS_FILE.exists():
			verify_content = USERS_FILE.read_text(encoding="utf-8")
			verify_data = json.loads(verify_content)
			# 验证关键字段是否匹配（至少验证用户数量）
			if isinstance(verify_data, dict) and len(verify_data) > 0:
				# 检查所有用户的关键字段是否都存在
				for username, user_info in users.items():
					if username not in verify_data:
						return False
					# 验证关键字段
					if not isinstance(verify_data[username], dict):
						return False
		return True
		return False
	except Exception as e:
		st.error(f"保存用户数据失败: {e}")
		return False


def _ensure_admin_self_protection(target_username: str) -> None:
	current = auth_manager.get_current_user() if auth_manager else None
	if current and current.get("username") == target_username:
		st.warning("不允许对当前登录管理员账户执行该高危操作")
		st.stop()


def _render_users_table(users: dict) -> None:
	rows = []
	for username, info in users.items():
		# 格式化提供商权限显示
		provider_perms = info.get("provider_permissions", [])
		provider_display = {
			"dashscope": "阿里百炼",
			"deepseek": "DeepSeek",
			"google": "Google",
			"openai": "OpenAI",
			"openrouter": "OpenRouter",
			"siliconflow": "硅基流动",
			"custom_openai": "自定义OpenAI",
			"qianfan": "文心一言"
		}
		if not provider_perms:
			provider_perms_str = "未授权"
		else:
			provider_perms_str = ", ".join([provider_display.get(p, p) for p in provider_perms[:3]])
			if len(provider_perms) > 3:
				provider_perms_str += f"等{len(provider_perms)}个"
		
		rows.append({
			"用户名": username,
			"角色": info.get("role", "user"),
			"权限": ", ".join(info.get("permissions", [])),
			"LLM提供商": provider_perms_str,
			"点数": int(info.get("points", 0)),
			"创建时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("created_at", time.time())))
		})
	if rows:
		st.dataframe(rows, use_container_width=True)
	else:
		st.info("暂无用户数据")


def _create_user_form(users: dict) -> None:
	st.subheader("新增会员")
	with st.form("create_user_form", clear_on_submit=True):
		col1, col2 = st.columns(2)
		with col1:
			username = st.text_input("用户名", placeholder="例如: user01")
			role = st.selectbox("角色", ["user", "admin"], index=0)
		with col2:
			password = st.text_input("初始密码", type="password", placeholder="建议强密码")
			perms = st.multiselect("权限", ["analysis", "batch_analysis", "config", "admin"], default=["analysis"]) 
			points = st.number_input("初始点数", min_value=0, value=10, step=1)
		submitted = st.form_submit_button("创建")
		if submitted:
			if not username or not password:
				st.error("用户名和密码不能为空")
				return
			if username in users:
				st.error("该用户名已存在")
				return
			# 使用 AuthManager 的哈希规则保持一致
			from web.utils.auth_manager import AuthManager
			hasher = AuthManager()
			users[username] = {
				"password_hash": hasher._hash_password(password),
				"role": role,
				"permissions": perms,
				"provider_permissions": [],  # 默认无提供商权限，需要管理员授权
				"points": int(points),
				"created_at": time.time()
			}
			if _save_users(users):
				st.success("创建成功")
				try:
					st.rerun()
				except:
					st.experimental_rerun()


def _update_user_form(users: dict) -> None:
	st.subheader("编辑会员")
	usernames = list(users.keys())
	if not usernames:
		st.info("暂无用户可编辑")
		return
	selected = st.selectbox("选择用户", usernames)
	if not selected:
		return
	info = users[selected]
	with st.form("update_user_form"):
		col1, col2 = st.columns(2)
		with col1:
			new_role = st.selectbox("角色", ["user", "admin"], index=0 if info.get("role")!="admin" else 1)
			new_password = st.text_input("重置密码(留空则不改)", type="password")
		with col2:
			new_perms = st.multiselect("权限", ["analysis", "batch_analysis", "config", "admin"], default=info.get("permissions", []))
		col3, col4 = st.columns(2)
		with col3:
			new_points = st.number_input("点数", min_value=0, value=int(info.get("points", 0)), step=1)
		with col4:
			delta = st.number_input("增减点数(可为负)", value=0, step=1)
		
		# LLM提供商权限管理
		st.markdown("---")
		st.markdown("#### LLM提供商授权")
		provider_options = {
			"dashscope": "阿里百炼",
			"deepseek": "DeepSeek V3",
			"google": "Google AI",
			"openai": "OpenAI",
			"openrouter": "OpenRouter",
			"siliconflow": "硅基流动",
			"custom_openai": "自定义OpenAI端点",
			"qianfan": "文心一言（千帆）"
		}
		current_provider_perms = info.get("provider_permissions", [])
		new_provider_perms = st.multiselect(
			"允许使用的LLM提供商",
			options=list(provider_options.keys()),
			default=current_provider_perms,
			format_func=lambda x: provider_options.get(x, x),
			help="选择该会员可以使用哪些LLM提供商。会员只能使用被授权的提供商进行股票分析"
		)
		
		submitted = st.form_submit_button("保存变更")
		if submitted:
			if new_password:
				_ensure_admin_self_protection(selected)
				from web.utils.auth_manager import AuthManager
				hasher = AuthManager()
				info["password_hash"] = hasher._hash_password(new_password)
			info["role"] = new_role
			info["permissions"] = new_perms
			info["provider_permissions"] = new_provider_perms
			# 点数处理：优先以 new_points 为基准，再叠加 delta
			base_points = int(new_points)
			final_points = int(max(0, base_points + int(delta)))
			info["points"] = final_points
			if _save_users(users):
				st.success("已保存")
				try:
					st.rerun()
				except:
					st.experimental_rerun()


def _delete_user_form(users: dict) -> None:
	st.subheader("删除会员")
	usernames = [u for u in users.keys()]
	if not usernames:
		st.info("暂无用户可删除")
		return
	selected = st.selectbox("选择要删除的用户", usernames)
	if not selected:
		return
	if selected == "admin":
		st.warning("禁止删除内置管理员账户")
		return
	_ensure_admin_self_protection(selected)
	if st.button("确认删除", type="secondary"):
		users.pop(selected, None)
		if _save_users(users):
			st.success("已删除")
			try:
				st.rerun()
			except Exception:
				st.experimental_rerun()


def _export_users(users: dict) -> None:
	"""导出会员信息"""
	st.subheader("导出会员信息")
	
	if not users:
		st.warning("当前没有会员数据可导出")
		return
	
	# 显示导出信息
	st.info(f"准备导出 {len(users)} 个会员的信息")
	
	# 选择导出格式
	export_format = st.radio(
		"选择导出格式",
		["Excel (.xlsx)", "JSON (.json)"],
		horizontal=True,
		help="Excel格式更适合在Excel中查看和编辑，JSON格式保留完整的数据结构"
	)
	
	# Excel格式下选择导出类型
	excel_export_type = None
	if export_format == "Excel (.xlsx)":
		excel_export_type = st.radio(
			"选择Excel导出类型",
			["批量导入模板（含密码列）", "数据备份（仅密码哈希）"],
			horizontal=True,
			help="批量导入模板：适合批量创建会员，可以填写密码\n数据备份：导出完整系统数据，包含密码哈希"
		)
	
	# 生成文件名
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	
	if export_format == "Excel (.xlsx)":
		if excel_export_type == "批量导入模板（含密码列）":
			# 生成批量导入模板（只包含列名，不包含现有数据）
			rows = [{
				"用户名": "",
				"密码": "",
				"角色": "user",
				"权限": "analysis",
				"LLM提供商权限": "dashscope, deepseek",
				"点数": 0
			}]
			
			# 创建DataFrame
			df = pd.DataFrame(rows)
			
			# 生成Excel文件
			output = BytesIO()
			with pd.ExcelWriter(output, engine='openpyxl') as writer:
				# 写入模板数据（只有表头和一个示例行）
				df.to_excel(writer, sheet_name='会员信息', index=False)
				
				# 写入说明信息
				instructions = [
					["列名", "说明", "示例", "必填"],
					["用户名", "会员登录卡号/用户名", "user001", "是"],
					["密码", "登录密码（明文）", "password123", "是"],
					["角色", "用户角色：user 或 admin", "user", "是"],
					["权限", "权限列表，用逗号分隔", "analysis, batch_analysis", "否"],
					["LLM提供商权限", "允许使用的LLM提供商，用逗号分隔", "dashscope, deepseek, openai", "否"],
					["点数", "初始点数", "10", "否"]
				]
				instructions_df = pd.DataFrame(instructions[1:], columns=instructions[0])
				instructions_df.to_excel(writer, sheet_name='填写说明', index=False)
				
				# 写入提供商说明
				provider_info = [
					["提供商代码", "提供商名称", "说明"],
					["dashscope", "阿里百炼", "阿里巴巴的AI服务"],
					["deepseek", "DeepSeek V3", "DeepSeek AI模型"],
					["google", "Google AI", "Google的AI服务"],
					["openai", "OpenAI", "OpenAI的GPT模型"],
					["openrouter", "OpenRouter", "OpenRouter聚合服务"],
					["siliconflow", "硅基流动", "硅基流动AI服务"],
					["custom_openai", "自定义OpenAI端点", "自定义OpenAI兼容端点"],
					["qianfan", "文心一言（千帆）", "百度的文心一言"]
				]
				provider_df = pd.DataFrame(provider_info[1:], columns=provider_info[0])
				provider_df.to_excel(writer, sheet_name='LLM提供商说明', index=False)
			
			excel_data = output.getvalue()
			filename = f"members_template_{timestamp}.xlsx"
			
			# 提供下载按钮
			st.download_button(
				label="下载批量导入模板",
				data=excel_data,
				file_name=filename,
				mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
				help="下载批量导入模板，填写后可以批量导入会员"
			)
			
			# 显示导出提示
			st.info("**批量导入模板说明**：\n"
			        "- **用户名**：会员的登录卡号/用户名（必填）\n"
			        "- **密码**：登录密码，明文填写（必填，导入后可直接使用）\n"
			        "- **角色**：user（普通用户）或 admin（管理员）\n"
			        "- **权限**：多个权限用逗号分隔，如：analysis, batch_analysis, config\n"
			        "- **LLM提供商权限**：允许使用的LLM提供商，用逗号分隔，如：dashscope, deepseek, openai（可选，留空表示未授权）\n"
			        "- **点数**：初始点数，默认为0\n"
			        "- 填写完成后，使用下方的导入功能上传此文件\n"
			        "- 详细提供商代码请查看Excel中的「LLM提供商说明」工作表")
		
		else:  # 数据备份（仅密码哈希）
			# 准备Excel数据
			rows = []
			for username, info in users.items():
				# 处理创建时间
				created_at = info.get("created_at", time.time())
				if isinstance(created_at, (int, float)):
					created_time = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
				else:
					created_time = str(created_at)
				
				# 处理权限列表，转换为逗号分隔的字符串
				permissions = info.get("permissions", [])
				permissions_str = ", ".join(permissions) if isinstance(permissions, list) else str(permissions)
				
				# 处理LLM提供商权限列表，转换为逗号分隔的字符串
				provider_permissions = info.get("provider_permissions", [])
				provider_permissions_str = ", ".join(provider_permissions) if isinstance(provider_permissions, list) else str(provider_permissions)
				
				rows.append({
					"用户名": username,
					"密码哈希": info.get("password_hash", ""),
					"角色": info.get("role", "user"),
					"权限": permissions_str,
					"LLM提供商权限": provider_permissions_str,
					"点数": int(info.get("points", 0)),
					"创建时间": created_time
				})
			
			# 创建DataFrame
			df = pd.DataFrame(rows)
			
			# 生成Excel文件
			output = BytesIO()
			with pd.ExcelWriter(output, engine='openpyxl') as writer:
				# 写入会员数据
				df.to_excel(writer, sheet_name='会员信息', index=False)
				
				# 写入导出信息
				export_info_df = pd.DataFrame([{
					"导出时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
					"会员总数": len(users),
					"版本": "1.0"
				}])
				export_info_df.to_excel(writer, sheet_name='导出信息', index=False)
			
			excel_data = output.getvalue()
			filename = f"members_backup_{timestamp}.xlsx"
			
			# 提供下载按钮
			st.download_button(
				label="下载备份文件",
				data=excel_data,
				file_name=filename,
				mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
				help="下载当前所有会员信息的备份文件（包含密码哈希）"
			)
			
			# 显示导出提示
			st.info("**数据备份说明**：\n"
			        "- 此文件包含所有会员的完整数据\n"
			        "- 密码哈希列：用于系统验证，请勿修改\n"
			        "- 权限列：多个权限用逗号和空格分隔（如：analysis, batch_analysis）\n"
			        "- LLM提供商权限列：多个提供商用逗号和空格分隔（如：dashscope, deepseek, openai）\n"
			        "- 导入时需要保留所有列，否则可能导入失败")
	
	else:  # JSON格式
		# 生成导出数据（包含元数据）
		export_data = {
			"export_info": {
				"export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
				"total_users": len(users),
				"version": "1.0"
			},
			"users": users
		}
		
		# 生成JSON字符串
		json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
		filename = f"members_export_{timestamp}.json"
		
		# 提供下载按钮
		st.download_button(
			label="下载JSON文件",
			data=json_data,
			file_name=filename,
			mime="application/json",
			help="下载当前所有会员信息的JSON文件"
		)


def _import_users(users: dict) -> None:
	"""导入会员信息"""
	st.subheader("导入会员信息")
	
	# 文件上传
	uploaded_file = st.file_uploader(
		"选择要导入的文件",
		type=["json", "xlsx"],
		help="支持JSON和Excel(.xlsx)格式\n"
		     "• 批量导入模板：包含\"密码\"列（明文），填写用户名和密码即可批量导入\n"
		     "• 数据备份文件：包含\"密码哈希\"列，用于系统数据备份和恢复"
	)
	
	if uploaded_file is not None:
		try:
			# 检测文件类型
			file_name = uploaded_file.name.lower()
			import_users = {}
			export_info = {}
			
			if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
				# Excel格式处理
				st.info("检测到Excel格式文件，正在解析...")
				
				# 读取Excel文件到内存
				excel_data = uploaded_file.read()
				excel_buffer = BytesIO(excel_data)
				
				# 读取会员信息表
				df = pd.read_excel(excel_buffer, sheet_name='会员信息', engine='openpyxl')
				
				# 尝试读取导出信息（如果存在）
				try:
					# 重新创建buffer以读取第二个sheet
					excel_buffer2 = BytesIO(excel_data)
					info_df = pd.read_excel(excel_buffer2, sheet_name='导出信息', engine='openpyxl')
					if not info_df.empty:
						export_info = {
							"export_time": str(info_df.iloc[0].get("导出时间", "")),
							"total_users": int(info_df.iloc[0].get("会员总数", 0))
						}
				except Exception as e:
					pass  # 如果没有导出信息表，跳过
				
				# 验证必需的列
				has_password_col = "密码" in df.columns
				has_password_hash_col = "密码哈希" in df.columns
				
				required_columns = ["用户名", "角色"]
				missing_columns = [col for col in required_columns if col not in df.columns]
				
				if missing_columns:
					st.error(f"Excel文件缺少必需的列：{', '.join(missing_columns)}")
					st.info("必需的列：用户名、角色")
					return
				
				# 检查密码相关列
				if not has_password_col and not has_password_hash_col:
					st.error("Excel文件必须包含\"密码\"列或\"密码哈希\"列")
					st.info("**批量导入模板**：应包含\"密码\"列（明文）\n"
					        "**数据备份文件**：应包含\"密码哈希\"列")
					return
				
				# 导入AuthManager用于生成密码哈希
				from web.utils.auth_manager import AuthManager
				auth_hasher = AuthManager()
				
				# 统计信息
				password_set_count = 0
				password_hash_count = 0
				skip_count = 0
				skip_reasons = []
				
				# 转换Excel数据为用户数据格式
				for _, row in df.iterrows():
					username = str(row["用户名"]).strip()
					if not username or pd.isna(row["用户名"]) or username == "":
						skip_count += 1
						continue  # 跳过空用户名
					
					# 处理密码：优先使用"密码"列（明文），如果为空则使用"密码哈希"列
					password_value = str(row.get("密码", "")).strip() if has_password_col else ""
					password_hash_value = str(row.get("密码哈希", "")).strip() if has_password_hash_col else ""
					
					# 确定使用哪个密码哈希
					if password_value and password_value.lower() not in ['nan', 'none', '']:
						# 如果密码列有值，生成新的密码哈希
						clean_password = password_value.strip().replace('\n', '').replace('\r', '')
						if clean_password:
							password_hash = auth_hasher._hash_password(clean_password)
							password_set_count += 1
						else:
							skip_reasons.append(f"{username}: 密码值为空")
							skip_count += 1
							continue
					elif password_hash_value and password_hash_value.lower() not in ['nan', 'none', '']:
						# 使用密码哈希列的值
						password_hash = password_hash_value
						password_hash_count += 1
					else:
						# 两者都为空，跳过该用户
						skip_reasons.append(f"{username}: 密码和密码哈希都为空")
						skip_count += 1
						continue
					
					# 处理角色
					role = str(row.get("角色", "user")).strip()
					if role not in ["user", "admin"]:
						role = "user"  # 默认值
					
					# 处理权限字段：从字符串转换为列表
					permissions_str = str(row.get("权限", ""))
					if permissions_str and permissions_str.lower() not in ['nan', 'none', '']:
						# 分割权限字符串（支持逗号、分号分隔）
						permissions = [p.strip() for p in permissions_str.replace(';', ',').split(',') if p.strip()]
					else:
						permissions = ["analysis"]  # 默认权限
					
					# 处理点数
					points_value = row.get("点数", 0)
					if pd.notna(points_value):
						try:
							points = int(points_value)
						except:
							points = 0
					else:
						points = 0
					
					# 处理创建时间：尝试解析时间字符串，如果失败则使用当前时间
					created_time_str = str(row.get("创建时间", ""))
					if created_time_str and created_time_str.lower() not in ['nan', 'none', '']:
						try:
							# 尝试解析时间字符串
							dt = pd.to_datetime(created_time_str)
							created_at = dt.timestamp()
						except:
							created_at = time.time()
					else:
						created_at = time.time()
					
					# 处理提供商权限（支持多种列名）
					provider_perms_str = ""
					for col_name in ["LLM提供商权限", "提供商权限", "provider_permissions"]:
						if col_name in row:
							provider_perms_str = str(row.get(col_name, ""))
							break
					
					# 验证和清理提供商权限
					valid_providers = {
						"dashscope", "deepseek", "google", "openai", 
						"openrouter", "siliconflow", "custom_openai", "qianfan"
					}
					
					if provider_perms_str and provider_perms_str.lower() not in ['nan', 'none', '']:
						# 分割并清理提供商权限
						raw_providers = [p.strip() for p in provider_perms_str.replace(';', ',').split(',') if p.strip()]
						# 验证提供商名称是否有效
						provider_permissions = [p for p in raw_providers if p in valid_providers]
						# 记录无效的提供商名称
						invalid_providers = [p for p in raw_providers if p not in valid_providers]
						if invalid_providers:
							skip_reasons.append(f"{username}: 无效的LLM提供商名称 {', '.join(invalid_providers)}（已忽略）")
					else:
						provider_permissions = []  # 默认无权限，需要管理员授权
					
					import_users[username] = {
						"password_hash": password_hash,
						"role": role,
						"permissions": permissions,
						"provider_permissions": provider_permissions,
						"points": points,
						"created_at": created_at
					}
				
				# 显示处理统计
				if password_set_count > 0:
					st.success(f"检测到 {password_set_count} 个用户设置了密码（将从密码生成哈希）")
				if password_hash_count > 0:
					st.info(f"检测到 {password_hash_count} 个用户使用密码哈希（将直接导入）")
				if skip_count > 0:
					st.warning(f"跳过了 {skip_count} 行无效数据")
					if len(skip_reasons) <= 10:
						for reason in skip_reasons:
							st.text(f"  • {reason}")
					else:
						for reason in skip_reasons[:10]:
							st.text(f"  • {reason}")
						st.text(f"  ... 还有 {len(skip_reasons) - 10} 条")
				
				if export_info:
					st.info(f"导入文件信息：{export_info.get('export_time', '未知时间')}，共 {export_info.get('total_users', len(import_users))} 个会员")
				else:
					st.info(f"从Excel文件解析到 {len(import_users)} 个会员")
			
			else:
				# JSON格式处理
				file_content = uploaded_file.read().decode("utf-8")
				import_data = json.loads(file_content)
				
				# 验证文件格式
				if not isinstance(import_data, dict):
					st.error("文件格式错误：根节点必须是对象")
					return
				
				# 处理新旧格式兼容
				if "users" in import_data:
					# 新格式（包含export_info）
					import_users = import_data.get("users", {})
					export_info = import_data.get("export_info", {})
					if export_info:
						st.info(f"导入文件信息：{export_info.get('export_time', '未知时间')}，共 {export_info.get('total_users', 0)} 个会员")
				else:
					# 旧格式（直接是用户数据）
					import_users = import_data
					st.info("检测到旧格式文件，直接导入用户数据")
			
			if not import_users:
				st.warning("导入文件中没有会员数据")
				return
			
			# 显示导入预览
			st.markdown("---")
			st.markdown("#### 导入预览")
			
			preview_rows = []
			provider_display = {
				"dashscope": "阿里百炼",
				"deepseek": "DeepSeek",
				"google": "Google",
				"openai": "OpenAI",
				"openrouter": "OpenRouter",
				"siliconflow": "硅基流动",
				"custom_openai": "自定义OpenAI",
				"qianfan": "文心一言"
			}
			for username, info in import_users.items():
				# 格式化提供商权限显示
				provider_perms = info.get("provider_permissions", [])
				if not provider_perms:
					provider_perms_str = "未授权"
				else:
					provider_perms_str = ", ".join([provider_display.get(p, p) for p in provider_perms[:3]])
					if len(provider_perms) > 3:
						provider_perms_str += f"等{len(provider_perms)}个"
				
				preview_rows.append({
					"用户名": username,
					"角色": info.get("role", "user"),
					"权限": ", ".join(info.get("permissions", [])),
					"LLM提供商": provider_perms_str,
					"点数": int(info.get("points", 0))
				})
			
			if preview_rows:
				st.dataframe(preview_rows, use_container_width=True)
			
			# 导入选项
			st.markdown("---")
			st.markdown("#### 导入选项")
			
			import_mode = st.radio(
				"选择导入模式",
				["合并模式（保留现有，新增或更新）", "替换模式（完全替换现有数据）"],
				help="合并模式：保留现有会员，导入的会员会更新或新增\n替换模式：完全替换所有会员数据，仅保留导入的数据"
			)
			
			# 安全检查：如果是替换模式，显示警告
			if import_mode == "替换模式（完全替换现有数据）":
				current_count = len(users)
				import_count = len(import_users)
				st.warning(f"**危险操作**：替换模式将删除当前的 {current_count} 个会员，仅保留导入的 {import_count} 个会员！")
				
				# 如果当前登录的用户不在导入数据中，给出警告
				current_user = auth_manager.get_current_user() if auth_manager else None
				if current_user:
					current_username = current_user.get("username")
					if current_username and current_username not in import_users:
						st.error(f"**严重警告**：当前登录用户 '{current_username}' 不在导入数据中，替换后您将无法登录！")
			
			# 显示统计信息
			existing_usernames = set(users.keys())
			import_usernames = set(import_users.keys())
			
			new_count = len(import_usernames - existing_usernames)
			update_count = len(import_usernames & existing_usernames)
			
			if import_mode == "合并模式（保留现有，新增或更新）":
				keep_count = len(existing_usernames - import_usernames)
				st.info(f"📊 导入统计：新增 {new_count} 个，更新 {update_count} 个，保留现有 {keep_count} 个")
			else:
				st.info(f"📊 导入统计：将导入 {import_count} 个会员，删除 {len(existing_usernames - import_usernames)} 个现有会员")
			
			# 确认导入按钮
			st.markdown("---")
			if st.button("✅ 确认导入", type="primary"):
				# 记录导入前的用户数量
				before_count = len(users)
				
				# 验证导入数据的完整性
				valid_users = {}
				invalid_users = []
				
				for username, user_info in import_users.items():
					if not isinstance(user_info, dict):
						invalid_users.append(f"{username}: 数据格式错误")
						continue
					
					# 检查必要字段
					required_fields = ["password_hash", "role"]
					missing_fields = [field for field in required_fields if field not in user_info]
					
					if missing_fields:
						invalid_users.append(f"{username}: 缺少字段 {', '.join(missing_fields)}")
						continue
					
					# 确保有默认值
					if "permissions" not in user_info:
						user_info["permissions"] = []
					if "provider_permissions" not in user_info:
						user_info["provider_permissions"] = []  # 默认无提供商权限
					else:
						# 验证提供商权限的有效性（JSON导入时也需要验证）
						valid_providers = {
							"dashscope", "deepseek", "google", "openai", 
							"openrouter", "siliconflow", "custom_openai", "qianfan"
						}
						provider_perms = user_info.get("provider_permissions", [])
						if isinstance(provider_perms, list):
							# 过滤掉无效的提供商
							valid_provider_perms = [p for p in provider_perms if p in valid_providers]
							invalid_provider_perms = [p for p in provider_perms if p not in valid_providers]
							if invalid_provider_perms:
								invalid_users.append(f"{username}: 无效的LLM提供商名称 {', '.join(invalid_provider_perms)}（已忽略）")
							user_info["provider_permissions"] = valid_provider_perms
						elif isinstance(provider_perms, str):
							# 如果是字符串，转换为列表
							raw_providers = [p.strip() for p in provider_perms.replace(';', ',').split(',') if p.strip()]
							valid_provider_perms = [p for p in raw_providers if p in valid_providers]
							invalid_provider_perms = [p for p in raw_providers if p not in valid_providers]
							if invalid_provider_perms:
								invalid_users.append(f"{username}: 无效的LLM提供商名称 {', '.join(invalid_provider_perms)}（已忽略）")
							user_info["provider_permissions"] = valid_provider_perms
					if "points" not in user_info:
						user_info["points"] = 0
					if "created_at" not in user_info:
						user_info["created_at"] = time.time()
					
					valid_users[username] = user_info
				
				if invalid_users:
					st.warning(f"⚠️ 以下 {len(invalid_users)} 个用户数据不完整，将被跳过：")
					for msg in invalid_users[:5]:  # 最多显示5个
						st.text(f"  • {msg}")
					if len(invalid_users) > 5:
						st.text(f"  ... 还有 {len(invalid_users) - 5} 个")
				
				if not valid_users:
					st.error("❌ 没有有效的用户数据可以导入")
					return
				
				# 执行导入
				if import_mode == "替换模式（完全替换现有数据）":
					# 完全替换
					users.clear()
					users.update(valid_users)
				else:
					# 合并模式：更新现有，新增新的
					users.update(valid_users)
				
				# 保存数据
				if _save_users(users):
					# 验证保存是否成功：重新读取文件确认
					verify_users = _load_users()
					actual_count = len(verify_users)
					after_count = len(users)
					
					st.success(f"✅ 导入成功！")
					st.info(f"📊 导入前: {before_count} 个会员 → 导入后: {actual_count} 个会员")
					st.info(f"📊 本次有效导入: {len(valid_users)} 个会员（跳过了 {len(invalid_users)} 个无效数据）")
					
					# 显示新导入的用户列表（基于之前的统计）
					if import_mode == "合并模式（保留现有，新增或更新）" and new_count > 0:
						st.info(f"🆕 本次新增了 {new_count} 个新会员")
					
					# 如果是从密码列导入的，提醒用户可以登录（基于之前的统计）
					if password_set_count > 0:
						st.success("🔑 **重要提示**：导入的会员已设置密码，现在可以使用Excel中填写的密码直接登录！")
					
					# 强制刷新页面以显示最新数据
					time.sleep(0.8)
					try:
						st.rerun()
					except:
						# 兼容旧版本Streamlit
						try:
							st.experimental_rerun()
						except:
							st.info("💡 请手动刷新页面以查看最新数据")
				else:
					st.error("❌ 保存失败，请检查文件权限或磁盘空间")
		
		except json.JSONDecodeError as e:
			st.error(f"❌ JSON格式错误：{str(e)}")
		except Exception as e:
			st.error(f"❌ 导入失败：{str(e)}")
			st.exception(e)


def render_member_management():
	# 权限保护
	if not auth_manager or not auth_manager.check_permission("admin"):
		st.error("❌ 您没有权限访问会员管理")
		return

	st.title("👥 会员管理")
	users = _load_users()

	with st.expander("当前会员", expanded=True):
		_render_users_table(users)

	st.markdown("---")
	col_a, col_b, col_c = st.columns(3)
	with col_a:
		_create_user_form(users)
	with col_b:
		_update_user_form(users)
	with col_c:
		_delete_user_form(users)
	
	# 导出/导入功能
	st.markdown("---")
	st.markdown("### 📦 批量管理")
	col_export, col_import = st.columns(2)
	with col_export:
		_export_users(users)
	with col_import:
		_import_users(users)


def main():
	render_member_management()


