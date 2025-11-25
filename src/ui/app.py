"""
TestForge - Streamlit Web UI

主界面应用
"""

import streamlit as st
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.protocols import HTTPHandler
from src.core import AssertionEngine
from src.storage import YAMLStorage

# 页面配置
st.set_page_config(
    page_title="TestForge - API Testing Tool",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }

    /* 卡片容器 */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }

    /* 状态标签 */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }

    .status-success {
        background-color: #10b981;
        color: white;
    }

    .status-error {
        background-color: #ef4444;
        color: white;
    }

    /* 按钮样式增强 */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* 输入框样式 */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
    }

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* 选择框样式 */
    .stSelectbox>div>div {
        border-radius: 8px;
    }

    /* 分隔线 */
    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 2px solid #e5e7eb;
    }

    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* JSON显示优化 */
    .stJson {
        background-color: #f9fafb;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化Session State
if "storage" not in st.session_state:
    st.session_state.storage = YAMLStorage("./testcases")
if "response" not in st.session_state:
    st.session_state.response = None
if "assertion_results" not in st.session_state:
    st.session_state.assertion_results = []


def main():
    # 自定义标题
    st.markdown("""
    <div class="main-header">
        <h1>🔨 TestForge</h1>
        <p>Professional API Testing Tool - 测试工具集合体</p>
    </div>
    """, unsafe_allow_html=True)

    # 创建三栏布局
    col1, col2, col3 = st.columns([1, 2.5, 2.5])

    # ===== 左侧：用例管理 =====
    with col1:
        st.markdown("### 📋 Test Cases")

        # 用例列表
        testcases = st.session_state.storage.list_testcases()

        if testcases:
            st.markdown(f"<small style='color: #6b7280;'>Found {len(testcases)} test case(s)</small>", unsafe_allow_html=True)

            selected_case = st.selectbox(
                "Select:",
                options=["<New Test Case>"] + testcases,
                label_visibility="collapsed"
            )

            # 加载用例
            if selected_case != "<New Test Case>":
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📂 Load", use_container_width=True):
                        testcase = st.session_state.storage.load_testcase(selected_case)
                        st.session_state.current_testcase = testcase
                        st.success("Loaded!")
                        st.rerun()
                with col_b:
                    if st.button("🗑️ Delete", use_container_width=True):
                        st.session_state.storage.delete_testcase(selected_case)
                        st.warning("Deleted!")
                        st.rerun()
        else:
            st.info("💡 No test cases yet.\nCreate and save one!")

        st.divider()

        # 保存用例
        st.markdown("### 💾 Save Test")

        save_name = st.text_input(
            "Test case name:",
            value=st.session_state.get("testcase_name", "my_test"),
            placeholder="my_api_test",
            label_visibility="collapsed"
        )

        if st.button("💾 Save Current Test", type="primary", use_container_width=True):
            # 从界面收集当前配置
            testcase = {
                "name": save_name,
                "description": st.session_state.get("testcase_desc", ""),
                "request": {
                    "method": st.session_state.get("method", "GET"),
                    "url": st.session_state.get("url", ""),
                    "headers": st.session_state.get("headers_dict", {}),
                    "params": st.session_state.get("params_dict", {}),
                    "body": st.session_state.get("body_dict", None)
                },
                "assertions": st.session_state.get("assertions_list", [])
            }

            filename = st.session_state.storage.save_testcase(testcase)
            st.success(f"✓ Saved!")
            st.rerun()

        st.divider()

        # 统计信息
        st.markdown("### 📊 Statistics")
        if st.session_state.response:
            col_x, col_y = st.columns(2)
            with col_x:
                st.metric("Status", st.session_state.response.status_code)
            with col_y:
                st.metric("Time", f"{st.session_state.response.elapsed_ms:.0f}ms")
        else:
            st.caption("No recent requests")

    # ===== 中间：请求配置 =====
    with col2:
        st.markdown("### 📤 Request Configuration")

        # 基本配置
        col_method, col_url = st.columns([1, 3])

        with col_method:
            method = st.selectbox(
                "Method",
                options=["GET", "POST", "PUT", "DELETE", "PATCH"],
                index=0 if "current_testcase" not in st.session_state else
                      ["GET", "POST", "PUT", "DELETE", "PATCH"].index(
                          st.session_state.current_testcase.get("request", {}).get("method", "GET")
                      ),
                key="method",
                label_visibility="collapsed"
            )

        with col_url:
            url = st.text_input(
                "URL",
                value=st.session_state.get("current_testcase", {}).get("request", {}).get("url", "https://httpbin.org/get"),
                placeholder="https://api.example.com/endpoint",
                key="url",
                label_visibility="collapsed"
            )

        # 使用tabs组织详细配置
        tab1, tab2, tab3, tab4 = st.tabs(["🔧 Headers", "🔍 Params", "📦 Body", "✅ Assertions"])

        with tab1:
            headers_text = st.text_area(
                "Request Headers (JSON format)",
                value=json.dumps(
                    st.session_state.get("current_testcase", {}).get("request", {}).get("headers", {}),
                    indent=2
                ),
                height=200,
                placeholder='{\n  "Content-Type": "application/json",\n  "Authorization": "Bearer token"\n}',
                help="Enter headers as JSON object"
            )

        with tab2:
            params_text = st.text_area(
                "Query Parameters (JSON format)",
                value=json.dumps(
                    st.session_state.get("current_testcase", {}).get("request", {}).get("params", {}),
                    indent=2
                ),
                height=200,
                placeholder='{\n  "page": 1,\n  "limit": 10\n}',
                help="Enter query parameters as JSON object"
            )

        with tab3:
            if method in ["POST", "PUT", "PATCH"]:
                body_text = st.text_area(
                    "Request Body (JSON format)",
                    value=json.dumps(
                        st.session_state.get("current_testcase", {}).get("request", {}).get("body", {}),
                        indent=2
                    ),
                    height=200,
                    placeholder='{\n  "username": "test",\n  "password": "test123"\n}',
                    help="Enter request body as JSON object"
                )
            else:
                st.info("Request body is available for POST, PUT, and PATCH methods.")
                body_text = "{}"

        with tab4:
            st.markdown("**Common Assertions:**")
            st.code("""status == 200
response['success'] == True
elapsed_ms < 1000
'data' in response""", language="python")

            assertions_text = st.text_area(
                "Your Assertions (one per line)",
                value="\n".join(st.session_state.get("current_testcase", {}).get("assertions", [])),
                height=150,
                placeholder="status == 200\nresponse['success'] == True\nelapsed_ms < 1000",
                help="Python expressions to validate the response"
            )

        # 发送请求按钮
        if st.button("🚀 Send Request", type="primary", use_container_width=True):
            try:
                # 解析JSON
                headers_dict = json.loads(headers_text) if headers_text.strip() else {}
                params_dict = json.loads(params_text) if params_text.strip() else {}
                body_dict = json.loads(body_text) if body_text.strip() and method in ["POST", "PUT", "PATCH"] else None

                # 保存到session state
                st.session_state.headers_dict = headers_dict
                st.session_state.params_dict = params_dict
                st.session_state.body_dict = body_dict
                st.session_state.assertions_list = [a.strip() for a in assertions_text.split("\n") if a.strip()]

                # 构建请求
                handler = HTTPHandler()
                config = {
                    "method": method,
                    "url": url,
                    "headers": headers_dict,
                    "params": params_dict,
                    "body": body_dict
                }

                request = handler.build_request(config)

                # 发送请求
                with st.spinner("Sending request..."):
                    response = handler.send_request(request)
                    st.session_state.response = response

                # 执行断言
                if assertions_text.strip():
                    engine = AssertionEngine()
                    context = {
                        "status": response.status_code,
                        "response": response.body if isinstance(response.body, dict) else {},
                        "headers": response.headers,
                        "elapsed_ms": response.elapsed_ms
                    }

                    assertions = [a.strip() for a in assertions_text.split("\n") if a.strip()]
                    results = engine.evaluate_all(assertions, context)
                    st.session_state.assertion_results = results

                st.success("Request sent successfully!")
                st.rerun()

            except json.JSONDecodeError as e:
                st.error(f"JSON Parse Error: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

    # ===== 右侧：响应展示 =====
    with col3:
        st.markdown("### 📥 Response")

        if st.session_state.response:
            response = st.session_state.response

            # 状态码和响应时间 - 使用metrics
            col_status, col_time = st.columns(2)
            with col_status:
                status_emoji = "✅" if 200 <= response.status_code < 300 else "❌"
                st.metric("Status", f"{status_emoji} {response.status_code}")
            with col_time:
                time_color = "normal" if response.elapsed_ms < 1000 else "inverse"
                st.metric("Response Time", f"{response.elapsed_ms:.0f} ms",
                         delta=None if response.elapsed_ms < 1000 else "Slow",
                         delta_color=time_color)

            st.divider()

            # 使用tabs组织响应内容
            resp_tab1, resp_tab2, resp_tab3 = st.tabs(["📄 Body", "📋 Headers", "✅ Assertions"])

            with resp_tab1:
                if isinstance(response.body, dict):
                    # 显示JSON格式
                    if response.body:
                        st.json(response.body)
                    else:
                        st.info("Empty response body")
                else:
                    # 显示文本格式
                    st.code(str(response.body), language="text")

            with resp_tab2:
                if response.headers:
                    st.json(response.headers)
                else:
                    st.info("No headers received")

            with resp_tab3:
                if st.session_state.assertion_results:
                    # 统计
                    passed = sum(1 for r in st.session_state.assertion_results if r.passed)
                    total = len(st.session_state.assertion_results)
                    pass_rate = (passed / total * 100) if total > 0 else 0

                    # 显示通过率
                    if pass_rate == 100:
                        st.success(f"🎉 All {total} assertions passed!")
                    else:
                        st.warning(f"⚠️ {passed}/{total} assertions passed ({pass_rate:.0f}%)")

                    st.divider()

                    # 详细结果
                    for idx, result in enumerate(st.session_state.assertion_results, 1):
                        if result.passed:
                            st.markdown(f"""
                            <div style='background-color: #d1fae5; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #10b981;'>
                                <strong>#{idx} ✅ Passed</strong><br>
                                <code>{result.assertion}</code>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background-color: #fee2e2; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #ef4444;'>
                                <strong>#{idx} ❌ Failed</strong><br>
                                <code>{result.assertion}</code><br>
                                <small style='color: #991b1b;'>{result.message}</small>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("💡 Add assertions in the Request Configuration tab to validate responses.")

        else:
            # 空状态
            st.markdown("""
            <div style='text-align: center; padding: 3rem 1rem; color: #6b7280;'>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>📭</div>
                <h3>No Response Yet</h3>
                <p>Configure your request and click <strong>Send Request</strong> to see the response here.</p>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
