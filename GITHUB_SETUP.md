# TestForge - GitHub仓库设置指南

## 📦 创建GitHub仓库

### 步骤1: 在GitHub上创建新仓库

1. 登录 GitHub: https://github.com
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `testforge`
   - **Description**: `TestForge - Professional API Testing Platform with Python Backend`
   - **Visibility**: Public 或 Private（根据需求选择）
   - ⚠️ **不要勾选** "Initialize this repository with a README"
   - ⚠️ **不要** 添加 .gitignore 和 license（我们已经有了）
4. 点击 "Create repository"

### 步骤2: 推送代码到GitHub

创建仓库后，GitHub会显示命令。由于我们已经有本地仓库，使用以下命令：

#### 方式一：使用HTTPS（推荐）

```bash
cd D:\Python_file\tool_project\testforge

# 添加远程仓库
git remote add origin https://github.com/你的用户名/testforge.git

# 推送代码
git push -u origin master
```

#### 方式二：使用SSH（需要先配置SSH密钥）

```bash
cd D:\Python_file\tool_project\testforge

# 添加远程仓库（SSH方式）
git remote add origin git@github.com:你的用户名/testforge.git

# 推送代码
git push -u origin master
```

### 步骤3: 验证推送成功

访问你的GitHub仓库页面：
```
https://github.com/你的用户名/testforge
```

应该能看到所有文件，包括：
- README.md
- src/
- requirements.txt
- Dockerfile
- 等等...

## 🔐 处理身份验证

### 如果遇到身份验证问题：

#### 选项1: 使用Personal Access Token（推荐）

1. 访问 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击 "Generate new token (classic)"
3. 勾选必要的权限：
   - ✅ repo (完整的仓库访问权限)
4. 生成并复制token
5. 推送时，用户名输入你的GitHub用户名，密码输入刚才的token

#### 选项2: 使用GitHub CLI

```bash
# 安装 GitHub CLI
# 访问 https://cli.github.com/ 下载安装

# 登录
gh auth login

# 推送代码
git push -u origin master
```

#### 选项3: 配置SSH密钥

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥到剪贴板
cat ~/.ssh/id_ed25519.pub

# 在GitHub Settings → SSH and GPG keys → New SSH key 中添加
```

## 🌐 如果遇到网络问题

### 问题1: Connection timeout

可能需要配置代理：

```bash
# 设置代理（根据你的代理端口调整）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 推送
git push -u origin master

# 推送后可以取消代理
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 问题2: Connection was reset

尝试增加缓冲区大小：

```bash
git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

### 问题3: 使用镜像站（中国用户）

```bash
# 可以先推送到Gitee等国内平台，再同步到GitHub
```

## 📊 推送成功后的操作

### 1. 添加仓库描述和标签

在GitHub仓库页面：
- 点击右侧的 ⚙️ 图标
- 添加描述: "Professional API Testing Platform with FastAPI backend"
- 添加标签: `api-testing`, `fastapi`, `python`, `testing-tools`, `automation`

### 2. 设置仓库主题（可选）

在 Settings → General → About:
- Website: 你的部署地址（如果有）
- Topics: api-testing, fastapi, python, pytest, yaml

### 3. 创建README徽章（可选）

在README.md顶部添加：

```markdown
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
```

## 🔗 完整的推送示例

```bash
# 进入testforge目录
cd D:\Python_file\tool_project\testforge

# 检查当前状态
git status

# 查看提交历史
git log --oneline -5

# 添加远程仓库（替换成你的用户名）
git remote add origin https://github.com/你的用户名/testforge.git

# 验证远程仓库
git remote -v

# 推送代码（首次推送）
git push -u origin master

# 后续推送只需要
git push
```

## 📝 推送后的后续管理

### 保持两个仓库同步

如果forge-apis推送成功，在README中添加链接：

**testforge/README.md**
```markdown
## Related Projects

- [forge-apis](https://github.com/ttcai559-lgtm/forge-apis) - React frontend for TestForge
```

**forge-apis/README.md**
```markdown
## Related Projects

- [testforge](https://github.com/你的用户名/testforge) - Python backend for TestForge
```

### 创建组织（可选）

如果想统一管理：
1. 创建GitHub组织，如 "TestForge-Team"
2. 将两个仓库转移到组织下
3. 统一的URL前缀：
   - `github.com/TestForge-Team/testforge`
   - `github.com/TestForge-Team/forge-apis`

## ✅ 验证清单

推送成功后，检查以下内容：

- [ ] README.md 显示正常
- [ ] 所有代码文件都存在
- [ ] .gitignore 正常工作（node_modules、__pycache__等被忽略）
- [ ] 提交历史完整
- [ ] 文件结构清晰
- [ ] requirements.txt 完整
- [ ] Docker配置正确

## 🎉 成功！

恭喜！TestForge后端代码已成功推送到GitHub！

**下一步：**
1. 为forge-apis配置README，说明如何连接到testforge后端
2. 在两个仓库的README中互相引用
3. 考虑创建 GitHub Actions 自动化测试和部署

---

## 💡 提示

- 使用 `git push --force` 要非常小心，只在确认无误时使用
- 定期备份代码到远程仓库
- 使用分支进行功能开发：`git checkout -b feature/new-feature`
- 保持提交信息清晰有意义

**需要帮助？** 查看 [GitHub文档](https://docs.github.com/cn) 或提issue
