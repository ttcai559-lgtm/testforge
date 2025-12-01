"""
TestForge - FastAPI Backend

提供REST API接口给React前端使用
"""




from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os
import shutil
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.protocols import HTTPHandler, ProtobufHandler
from src.core import AssertionEngine, AssertionResult
from src.storage import YAMLStorage, EnvironmentStorage

# 导入AI测试用例生成模块
try:
    from src.ai_testcase_gen.generator import TestCaseGenerator
except ImportError:
    TestCaseGenerator = None

app = FastAPI(title="TestForge API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
http_handler = HTTPHandler()
protobuf_handler = ProtobufHandler("./proto_files", "./compiled_protos")
assertion_engine = AssertionEngine()
storage = YAMLStorage("./testcases")
env_storage = EnvironmentStorage("./environments")


# ==================== Pydantic Models ====================

class TestCaseRequest(BaseModel):
    id: Optional[str] = None  # 文件名（用于更新已存在的用例）
    name: str
    method: str
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, str]] = {}
    body: Optional[Any] = None
    assertions: Optional[List[str]] = []
    environment: Optional[str] = None  # 关联的媒体名称
    requestMessageType: Optional[str] = None  # Protobuf请求Message类型
    responseMessageType: Optional[str] = None  # Protobuf响应Message类型


class SendRequestPayload(BaseModel):
    method: str
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, str]] = {}
    body: Optional[Any] = None
    assertions: Optional[List[str]] = []
    environment: Optional[str] = None  # 关联的媒体名称
    request_message_type: Optional[str] = None  # Protobuf请求Message类型
    response_message_type: Optional[str] = None  # Protobuf响应Message类型


class AssertionResultResponse(BaseModel):
    assertion: str
    passed: bool
    error: Optional[str] = None


class ResponseData(BaseModel):
    status: int
    statusText: str
    data: Any
    headers: Dict[str, str]
    elapsedMs: float
    assertionResults: Optional[List[AssertionResultResponse]] = []


class EnvironmentRequest(BaseModel):
    name: str
    base_url: str
    default_headers: Optional[Dict[str, Any]] = None
    default_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    protocol: Optional[str] = "json"  # "json" or "protobuf"


# ==================== API Routes ====================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "TestForge API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.post("/api/send-request", response_model=ResponseData)
async def send_request(payload: SendRequestPayload):
    """
    发送HTTP请求并执行断言
    支持JSON和Protobuf协议
    """
    try:
        # 检查是否需要使用Protobuf协议
        use_protobuf = False
        if payload.environment:
            environment = env_storage.load_environment(payload.environment)
            if environment and environment.get("protocol") == "protobuf":
                use_protobuf = True

                # 验证必需的Protobuf参数
                if not payload.request_message_type:
                    raise HTTPException(
                        status_code=400,
                        detail="request_message_type is required for Protobuf protocol"
                    )
                if not payload.response_message_type:
                    raise HTTPException(
                        status_code=400,
                        detail="response_message_type is required for Protobuf protocol"
                    )

        # 准备请求头和body
        headers = dict(payload.headers or {})
        request_body = payload.body

        # 如果是Protobuf协议,将JSON转换为二进制
        if use_protobuf:
            if not isinstance(payload.body, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Request body must be a JSON object for Protobuf conversion"
                )

            # 转换JSON到Protobuf
            binary_data = protobuf_handler.json_to_protobuf(
                payload.environment,
                payload.request_message_type,
                payload.body
            )

            if binary_data is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to convert JSON to Protobuf for message type: {payload.request_message_type}"
                )

            request_body = binary_data
            headers["Content-Type"] = "application/x-protobuf"

        # 构建请求配置
        config = {
            "method": payload.method,
            "url": payload.url,
            "headers": headers,
            "params": payload.params or {},
            "body": request_body
        }

        # 发送请求
        request = http_handler.build_request(config)
        response = http_handler.send_request(request)

        # 处理响应数据
        response_data = response.body

        # 如果是Protobuf协议,将二进制响应转换为JSON
        if use_protobuf:
            if isinstance(response.body, bytes):
                json_data = protobuf_handler.protobuf_to_json(
                    payload.environment,
                    payload.response_message_type,
                    response.body
                )

                if json_data is None:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to convert Protobuf response to JSON for message type: {payload.response_message_type}"
                    )

                response_data = json_data
            else:
                # 如果响应不是二进制,可能是错误响应,保持原样
                response_data = response.body

        # 如果最终 response_data 仍然是二进制数据（非Protobuf协议的二进制响应），转换为描述字符串
        if isinstance(response_data, bytes):
            response_data = f"<Binary data, {len(response_data)} bytes>"

        # 执行断言
        assertion_results = []
        if payload.assertions:
            context = {
                "status": response.status_code,
                "response": response_data if isinstance(response_data, dict) else {},
                "headers": response.headers,
                "elapsed_ms": response.elapsed_ms
            }

            results = assertion_engine.evaluate_all(payload.assertions, context)
            assertion_results = [
                AssertionResultResponse(
                    assertion=r.assertion,
                    passed=r.passed,
                    error=r.message if not r.passed else None
                )
                for r in results
            ]

        # 返回响应数据
        return ResponseData(
            status=response.status_code,
            statusText=f"{response.status_code} {'OK' if 200 <= response.status_code < 300 else 'Error'}",
            data=response_data,
            headers=response.headers,
            elapsedMs=response.elapsed_ms,
            assertionResults=assertion_results
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/testcases")
async def list_testcases():
    """
    获取所有测试用例列表
    """
    try:
        cases = storage.list_testcases()
        return {"testcases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/testcases/{name}")
async def get_testcase(name: str):
    """
    加载指定测试用例
    """
    try:
        testcase = storage.load_testcase(name)
        if not testcase:
            raise HTTPException(status_code=404, detail="Test case not found")
        return testcase
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/testcases")
async def save_testcase(testcase: TestCaseRequest):
    """
    保存测试用例
    """
    try:
        testcase_dict = {
            "name": testcase.name,
            "description": f"Test case for {testcase.method} {testcase.url}",
            "request": {
                "method": testcase.method,
                "url": testcase.url,
                "headers": testcase.headers or {},
                "params": testcase.params or {},
                "body": testcase.body
            },
            "assertions": testcase.assertions or []
        }

        # Always include these fields to ensure they're saved
        testcase_dict["environment"] = testcase.environment
        testcase_dict["requestMessageType"] = testcase.requestMessageType
        testcase_dict["responseMessageType"] = testcase.responseMessageType

        # Use the testcase id as filename if it looks like a filename
        filename = None
        if hasattr(testcase, 'id') and testcase.id and (testcase.id.endswith('.yaml') or testcase.id.endswith('.yml')):
            filename = testcase.id

        saved_filename = storage.save_testcase(testcase_dict, filename=filename)
        return {"message": "Test case saved successfully", "filename": saved_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/testcases/{name}")
async def delete_testcase(name: str):
    """
    删除测试用例
    """
    try:
        storage.delete_testcase(name)
        return {"message": f"Test case '{name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Environment Management Routes ====================

@app.get("/api/environments")
async def list_environments():
    """
    获取所有环境（媒体）列表
    """
    try:
        environments = env_storage.get_all_environments()
        return {"environments": environments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environments/{name}")
async def get_environment(name: str):
    """
    加载指定环境
    """
    try:
        environment = env_storage.load_environment(name)
        if not environment:
            raise HTTPException(status_code=404, detail="Environment not found")
        return environment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/environments")
async def save_environment(environment: EnvironmentRequest):
    """
    保存环境配置
    """
    try:
        env_data = {
            "name": environment.name,
            "base_url": environment.base_url,
            "default_headers": environment.default_headers or {},
            "default_params": environment.default_params or {},
            "description": environment.description or "",
            "protocol": environment.protocol or "json"
        }

        filename = env_storage.save_environment(env_data)
        return {"message": "Environment saved successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/environments/{name}")
async def delete_environment(name: str):
    """
    删除环境
    """
    try:
        success = env_storage.delete_environment(name)
        if not success:
            raise HTTPException(status_code=404, detail="Environment not found")

        # 同时删除关联的proto文件
        protobuf_handler.delete_proto_files(name)

        return {"message": f"Environment '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Protobuf Management Routes ====================

@app.post("/api/environments/{name}/proto")
async def upload_proto_file(name: str, file: UploadFile = File(...)):
    """
    上传proto文件到指定环境
    """
    try:
        # 检查环境是否存在
        environment = env_storage.load_environment(name)
        if not environment:
            raise HTTPException(status_code=404, detail="Environment not found")

        # 检查环境协议类型
        if environment.get("protocol", "json") != "protobuf":
            raise HTTPException(
                status_code=400,
                detail="Environment protocol must be 'protobuf' to upload proto files"
            )

        # 检查文件类型
        if not file.filename.endswith(".proto"):
            raise HTTPException(status_code=400, detail="File must be a .proto file")

        # 读取文件内容
        proto_content = await file.read()

        # 保存proto文件
        proto_path = protobuf_handler.save_proto_file(name, proto_content)

        # 编译proto文件
        success, message = protobuf_handler.compile_proto(name)

        if not success:
            raise HTTPException(status_code=500, detail=f"Proto compilation failed: {message}")

        # 获取编译后的message类型列表
        message_types = protobuf_handler.get_message_types(name)

        return {
            "message": "Proto file uploaded and compiled successfully",
            "proto_path": proto_path,
            "compilation_message": message,
            "message_types": message_types,  # 返回message类型列表
            "message_count": len(message_types)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environments/{name}/messages")
async def get_proto_messages(name: str):
    """
    获取proto文件中定义的所有message类型
    """
    try:
        # 检查环境是否存在
        environment = env_storage.load_environment(name)
        if not environment:
            raise HTTPException(status_code=404, detail="Environment not found")

        # 检查是否有proto文件
        if not protobuf_handler.has_proto_file(name):
            return {"messages": []}

        # 获取message类型列表
        messages = protobuf_handler.get_message_types(name)

        return {"messages": messages}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/environments/{name}/proto")
async def check_proto_status(name: str):
    """
    检查环境的proto文件状态
    """
    try:
        # 检查环境是否存在
        environment = env_storage.load_environment(name)
        if not environment:
            raise HTTPException(status_code=404, detail="Environment not found")

        has_proto = protobuf_handler.has_proto_file(name)

        return {
            "environment": name,
            "protocol": environment.get("protocol", "json"),
            "has_proto_file": has_proto,
            "message_count": len(protobuf_handler.get_message_types(name)) if has_proto else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI测试用例生成 API ====================

@app.post("/api/ai/generate-testcases")
async def generate_testcases(
    file: UploadFile = File(...),
    ai_model: str = "claude",
    enable_defect_detection: bool = True,
    enable_question_generation: bool = True
):
    """
    AI测试用例生成接口

    上传需求文档（Word/PDF），返回生成的XMind文件路径
    """
    import time

    if TestCaseGenerator is None:
        raise HTTPException(
            status_code=501,
            detail="AI测试用例生成功能未安装，请先安装依赖: pip install python-docx PyMuPDF anthropic xmind"
        )

    # 验证文件类型
    allowed_extensions = ['.docx', '.doc', '.pdf']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{file_ext}。支持的格式: {', '.join(allowed_extensions)}"
        )

    # 创建临时上传目录
    upload_dir = Path(__file__).parent.parent / "ai_testcase_gen" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 保存上传的文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename

    try:
        # 保存文件
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 记录开始时间
        start_time = time.time()

        # 生成测试用例
        generator = TestCaseGenerator(ai_model=ai_model)
        result = generator.generate(
            document_path=str(file_path),
            enable_defect_detection=enable_defect_detection,
            enable_question_generation=enable_question_generation
        )

        # 计算耗时
        elapsed_time = time.time() - start_time

        # 提取相对路径用于下载
        xmind_path = result.get("xmind_path", "")
        if xmind_path:
            # 转换为相对于outputs目录的路径
            xmind_filename = Path(xmind_path).name
        else:
            raise HTTPException(status_code=500, detail="XMind文件生成失败")

        # 返回结果
        summary = result.get("summary", result.get("statistics", {}))
        return {
            "success": True,
            "xmind_filename": xmind_filename,
            "download_url": f"/api/ai/download/{xmind_filename}",
            "elapsed_time": round(elapsed_time, 2),
            "elapsed_time_formatted": f"{int(elapsed_time // 60)}分{int(elapsed_time % 60)}秒" if elapsed_time >= 60 else f"{int(elapsed_time)}秒",
            "summary": {
                "total_test_cases": summary.get("total_cases", summary.get("total_test_cases", 0)),
                "total_questions": summary.get("questions_count", summary.get("total_questions", 0)),
                "total_defects": summary.get("defects_count", summary.get("total_defects", 0)),
                "modules_count": summary.get("modules_count", 0)
            }
        }

    except Exception as e:
        # 清理上传的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.post("/api/ai/generate-testcases-stream")
async def generate_testcases_stream(
    file: UploadFile = File(...),
    ai_model: str = "claude",
    enable_defect_detection: bool = True,
    enable_question_generation: bool = True
):
    """
    AI测试用例生成接口 (流式响应版本)

    使用SSE (Server-Sent Events) 实时推送生成进度
    """
    import time
    import queue
    import threading

    if TestCaseGenerator is None:
        raise HTTPException(
            status_code=501,
            detail="AI测试用例生成功能未安装，请先安装依赖: pip install python-docx PyMuPDF anthropic xmind"
        )

    # 验证文件类型
    allowed_extensions = ['.docx', '.doc', '.pdf']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{file_ext}。支持的格式: {', '.join(allowed_extensions)}"
        )

    # 创建临时上传目录
    upload_dir = Path(__file__).parent.parent / "ai_testcase_gen" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 保存上传的文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename

    # 进度队列
    progress_queue = queue.Queue()

    def progress_callback(message: str, percent: int):
        """进度回调函数，将进度放入队列"""
        progress_queue.put({
            "type": "progress",
            "message": message,
            "percent": percent
        })

    async def generate_stream():
        """生成器函数，用于SSE流式响应"""
        try:
            # 保存文件
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # 记录开始时间
            start_time = time.time()

            # 在后台线程中运行生成任务
            result_container = {}
            error_container = {}

            def run_generation():
                try:
                    generator = TestCaseGenerator(ai_model=ai_model)
                    generator.set_progress_callback(progress_callback)

                    result = generator.generate(
                        document_path=str(file_path),
                        enable_defect_detection=enable_defect_detection,
                        enable_question_generation=enable_question_generation
                    )
                    result_container['result'] = result
                except Exception as e:
                    error_container['error'] = str(e)
                finally:
                    # 发送结束信号
                    progress_queue.put(None)

            # 启动生成线程
            gen_thread = threading.Thread(target=run_generation)
            gen_thread.start()

            # 持续发送进度更新
            while True:
                try:
                    # 从队列获取进度，设置超时避免阻塞
                    progress_data = progress_queue.get(timeout=0.5)

                    if progress_data is None:
                        # 结束信号
                        break

                    # 发送SSE格式的进度数据
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

                except queue.Empty:
                    # 没有新进度，发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"

            # 等待生成线程完成
            gen_thread.join()

            # 计算耗时
            elapsed_time = time.time() - start_time

            # 检查是否有错误
            if 'error' in error_container:
                yield f"data: {json.dumps({'type': 'error', 'message': error_container['error']}, ensure_ascii=False)}\n\n"
                return

            # 提取结果
            result = result_container.get('result', {})
            xmind_path = result.get("xmind_path", "")

            if xmind_path:
                xmind_filename = Path(xmind_path).name
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': 'XMind文件生成失败'}, ensure_ascii=False)}\n\n"
                return

            # 发送最终结果
            summary = result.get("summary", result.get("statistics", {}))
            final_data = {
                "type": "complete",
                "success": True,
                "xmind_filename": xmind_filename,
                "download_url": f"/api/ai/download/{xmind_filename}",
                "elapsed_time": round(elapsed_time, 2),
                "elapsed_time_formatted": f"{int(elapsed_time // 60)}分{int(elapsed_time % 60)}秒" if elapsed_time >= 60 else f"{int(elapsed_time)}秒",
                "summary": {
                    "total_test_cases": summary.get("total_cases", summary.get("total_test_cases", 0)),
                    "total_questions": summary.get("questions_count", summary.get("total_questions", 0)),
                    "total_defects": summary.get("defects_count", summary.get("total_defects", 0)),
                    "modules_count": summary.get("modules_count", 0)
                }
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 清理上传的文件
            if file_path.exists():
                file_path.unlink()

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/ai/download/{filename:path}")
async def download_xmind(filename: str):
    """
    下载生成的XMind文件
    """
    from urllib.parse import unquote

    # URL解码文件名
    decoded_filename = unquote(filename)

    # 验证文件名安全性
    if ".." in decoded_filename or "/" in decoded_filename or "\\" in decoded_filename:
        raise HTTPException(status_code=400, detail="非法的文件名")

    # 构建文件路径 - 指向实际的outputs目录 (testforge/outputs/)
    outputs_dir = Path(__file__).parent.parent.parent / "outputs"
    file_path = outputs_dir / decoded_filename

    # 调试日志
    print(f"下载请求 - 原始文件名: {filename}")
    print(f"下载请求 - 解码文件名: {decoded_filename}")
    print(f"下载请求 - 文件路径: {file_path}")
    print(f"下载请求 - 文件存在: {file_path.exists()}")

    # 检查文件是否存在
    if not file_path.exists():
        # 如果文件不存在,尝试列出目录中的所有文件
        print(f"可用文件列表:")
        if outputs_dir.exists():
            for f in outputs_dir.iterdir():
                print(f"  - {f.name}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {decoded_filename}")

    # 返回文件
    return FileResponse(
        path=str(file_path),
        filename=decoded_filename,
        media_type="application/octet-stream"
    )


@app.get("/api/ai/history")
async def get_history():
    """
    获取历史生成的测试用例列表
    """
    outputs_dir = Path(__file__).parent.parent.parent / "outputs"

    if not outputs_dir.exists():
        return {"files": [], "total": 0}

    files = []
    for file_path in sorted(outputs_dir.glob("*.xmind"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        files.append({
            "filename": file_path.name,
            "size": stat.st_size,
            "created_at": stat.st_mtime,
            "download_url": f"/api/ai/download/{file_path.name}"
        })

    return {"files": files, "total": len(files)}


@app.delete("/api/ai/delete/{filename:path}")
async def delete_file(filename: str):
    """
    删除指定的XMind文件
    """
    from urllib.parse import unquote

    # URL解码文件名
    decoded_filename = unquote(filename)

    # 验证文件名安全性
    if ".." in decoded_filename or "/" in decoded_filename or "\\" in decoded_filename:
        raise HTTPException(status_code=400, detail="非法的文件名")

    # 构建文件路径 - 指向实际的outputs目录 (testforge/outputs/)
    outputs_dir = Path(__file__).parent.parent.parent / "outputs"
    file_path = outputs_dir / decoded_filename

    # 检查文件是否存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {decoded_filename}")

    # 删除文件
    try:
        file_path.unlink()
        print(f"已删除文件: {file_path}")
        return {"success": True, "message": f"文件 {decoded_filename} 已删除"}
    except Exception as e:
        print(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


@app.get("/api/ai/status")
async def ai_status():
    """
    检查AI测试用例生成功能状态
    """
    return {
        "available": TestCaseGenerator is not None,
        "supported_formats": [".docx", ".doc", ".pdf"],
        "supported_models": ["claude", "openai"],
        "features": {
            "defect_detection": True,
            "question_generation": True,
            "confidence_scoring": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
