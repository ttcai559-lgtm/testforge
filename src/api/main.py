"""
TestForge - FastAPI Backend

提供REST API接口给React前端使用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.protocols import HTTPHandler
from src.core import AssertionEngine, AssertionResult
from src.storage import YAMLStorage

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
assertion_engine = AssertionEngine()
storage = YAMLStorage("./testcases")


# ==================== Pydantic Models ====================

class TestCaseRequest(BaseModel):
    name: str
    method: str
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, str]] = {}
    body: Optional[Any] = None
    assertions: Optional[List[str]] = []


class SendRequestPayload(BaseModel):
    method: str
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, str]] = {}
    body: Optional[Any] = None
    assertions: Optional[List[str]] = []


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
    """
    try:
        # 构建请求配置
        config = {
            "method": payload.method,
            "url": payload.url,
            "headers": payload.headers or {},
            "params": payload.params or {},
            "body": payload.body
        }

        # 发送请求
        request = http_handler.build_request(config)
        response = http_handler.send_request(request)

        # 执行断言
        assertion_results = []
        if payload.assertions:
            context = {
                "status": response.status_code,
                "response": response.body if isinstance(response.body, dict) else {},
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
            data=response.body,
            headers=response.headers,
            elapsedMs=response.elapsed_ms,
            assertionResults=assertion_results
        )

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

        filename = storage.save_testcase(testcase_dict)
        return {"message": "Test case saved successfully", "filename": filename}
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
