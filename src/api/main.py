"""
TestForge - FastAPI Backend

提供REST API接口给React前端使用
"""




from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.protocols import HTTPHandler, ProtobufHandler
from src.core import AssertionEngine, AssertionResult
from src.storage import YAMLStorage, EnvironmentStorage

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

        return {
            "message": "Proto file uploaded and compiled successfully",
            "proto_path": proto_path,
            "compilation_message": message
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
