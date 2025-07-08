# 安全配置指南

## 🔐 API密钥安全

### 重要提醒
- **永远不要**将API密钥直接写在代码中
- **永远不要**将包含API密钥的文件提交到Git仓库
- 使用环境变量来管理敏感信息

### 配置步骤

1. **复制环境变量模板**
   ```bash
   cp env.example .env
   ```

2. **编辑.env文件**
   ```bash
   # 使用你喜欢的编辑器
   nano .env
   # 或
   vim .env
   ```

3. **设置你的API密钥**
   ```bash
   # 硅基流动
   SILICONFLOW_API_KEY=your-actual-api-key-here
   
   # OpenAI
   OPENAI_API_KEY=your-actual-openai-key-here
   ```

4. **加载环境变量**
   ```bash
   # 方法1: 直接加载
   source .env
   
   # 方法2: 使用python-dotenv（推荐）
   pip install python-dotenv
   # 然后在代码中: load_dotenv()
   ```

### 验证配置

运行测试脚本验证配置：
```bash
python test_siliconflow_api.py
```

### 生产环境建议

1. **使用环境变量管理工具**
   - Docker: 使用 `--env-file` 或 `docker-compose.yml`
   - Kubernetes: 使用 Secrets
   - 云服务: 使用云平台的环境变量管理

2. **定期轮换API密钥**
   - 定期更新API密钥
   - 监控API使用情况
   - 设置使用限制

3. **访问控制**
   - 限制API密钥的权限范围
   - 使用最小权限原则
   - 监控异常访问

### 故障排除

如果遇到"未设置API密钥"错误：
1. 检查 `.env` 文件是否存在
2. 确认环境变量已正确加载
3. 验证API密钥格式是否正确
4. 检查网络连接是否正常 