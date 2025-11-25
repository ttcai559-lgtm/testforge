# TestForge

> 测试工具集合体 - 灵活、轻量、Python原生的API测试工具

## 项目愿景

TestForge 是一个面向Python开发者和测试工程师的API测试工具平台。

**1.0 MVP目标：**
- ✅ HTTP请求调试（GET/POST/PUT/DELETE）
- ✅ 灵活的断言引擎
- ✅ 用例保存和复用

**后续迭代方向：**
- 🔮 Protobuf协议支持
- 🎭 Mock服务（JSON/Protobuf）
- 🔗 Mock地址生成

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run src/ui/app.py
```

## 架构设计

**分层架构：**
```
UI层（Streamlit）
   ↓
业务层（TestCase、Assertion、Executor）
   ↓
协议层（ProtocolHandler - 插件化）
   ↓
数据层（Storage）
```

**核心特性：**
- 🔌 协议插件化 - 轻松扩展新协议
- 📦 模块解耦 - UI/业务/数据完全分离
- 🐍 Python原生 - 易于脚本化和自动化
- 🐳 Docker支持 - 一键部署

## 开发状态

- [x] 协议抽象层接口设计
- [x] HTTPHandler实现
- [x] 断言引擎
- [x] Streamlit UI
- [x] 用例存储（YAML）
- [x] Docker打包

**Status:** ✅ 1.0 MVP Complete!

## License

MIT License

---

🔨 Built with TestForge
