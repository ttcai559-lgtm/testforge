"""
FastAPI接口：AI测试用例生成服务
"""
import os
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid

from .generator import TestCaseGenerator
from .config import UPLOAD_DIR, OUTPUT_DIR, DEFAULT_AI_MODEL

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="TestForge AI测试用例生成服务",
    description="从需求文档自动提取测试点并生成XMind思维导图",
    version="1.0.0"
)

# 全局生成器实例
generator = TestCaseGenerator(ai_model=DEFAULT_AI_MODEL)

# 任务状态存储（简单版本，生产环境应使用Redis）
task_status = {}


# ========================
# 数据模型
# ========================

class GenerateRequest(BaseModel):
    """生成请求"""
    document_path: str
    output_filename: Optional[str] = None
    enable_defect_detection: bool = True
    enable_question_generation: bool = True
    ai_model: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str  # pending/processing/completed/failed
    progress: int  # 0-100
    message: str
    result: Optional[dict] = None


class GenerateResponse(BaseModel):
    """生成响应"""
    success: bool
    task_id: str
    message: str


# ========================
# API端点
# ========================

@app.post("/api/upload", response_model=dict)
async def upload_document(file: UploadFile = File(...)):
    """
    上传需求文档

    Args:
        file: 上传的文件（Word或PDF）

    Returns:
        上传结果，包含文件路径
    """
    try:
        # 验证文件格式
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.docx', '.pdf']:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式：{file_ext}，仅支持 .docx 和 .pdf"
            )

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)

        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"文件上传成功：{file_path}")

        return {
            "success": True,
            "file_id": file_id,
            "file_path": file_path,
            "original_filename": file.filename,
            "file_size": len(content)
        }

    except Exception as e:
        logger.error(f"文件上传失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_test_cases(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    生成测试用例（异步）

    Args:
        request: 生成请求参数
        background_tasks: 后台任务

    Returns:
        任务ID，可用于查询生成进度
    """
    try:
        # 验证文件存在
        if not os.path.exists(request.document_path):
            raise HTTPException(status_code=404, detail="文档文件不存在")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 初始化任务状态
        task_status[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": "任务已创建，等待处理",
            "result": None
        }

        # 添加后台任务
        background_tasks.add_task(
            _generate_task,
            task_id,
            request
        )

        logger.info(f"创建生成任务：{task_id}")

        return GenerateResponse(
            success=True,
            task_id=task_id,
            message="任务已创建，请使用task_id查询进度"
        )

    except Exception as e:
        logger.error(f"创建任务失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态和结果
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(**task_status[task_id])


@app.get("/api/download/{filename}")
async def download_xmind(filename: str):
    """
    下载生成的XMind文件

    Args:
        filename: 文件名

    Returns:
        XMind文件
    """
    file_path = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Test Case Generator",
        "version": "1.0.0"
    }


# ========================
# 后台任务
# ========================

def _generate_task(task_id: str, request: GenerateRequest):
    """
    后台生成任务

    Args:
        task_id: 任务ID
        request: 生成请求
    """
    try:
        # 更新状态：处理中
        task_status[task_id].update({
            "status": "processing",
            "progress": 10,
            "message": "正在解析文档..."
        })

        # 创建生成器（如果指定了AI模型）
        if request.ai_model:
            gen = TestCaseGenerator(ai_model=request.ai_model)
        else:
            gen = generator

        # 更新状态：AI提取
        task_status[task_id].update({
            "progress": 30,
            "message": "正在使用AI提取测试点..."
        })

        # 生成测试用例
        result = gen.generate(
            document_path=request.document_path,
            output_filename=request.output_filename,
            enable_defect_detection=request.enable_defect_detection,
            enable_question_generation=request.enable_question_generation
        )

        if result['success']:
            # 更新状态：完成
            task_status[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": "生成完成",
                "result": {
                    "xmind_path": result['xmind_path'],
                    "xmind_filename": os.path.basename(result['xmind_path']),
                    "statistics": result['statistics'],
                    "document_title": result.get('document_title', '')
                }
            })
            logger.info(f"任务完成：{task_id}")
        else:
            # 更新状态：失败
            task_status[task_id].update({
                "status": "failed",
                "progress": 0,
                "message": f"生成失败：{result.get('error', '未知错误')}",
                "result": None
            })
            logger.error(f"任务失败：{task_id}, 错误：{result.get('error')}")

    except Exception as e:
        # 更新状态：异常
        task_status[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"处理异常：{str(e)}",
            "result": None
        })
        logger.error(f"任务异常：{task_id}, 错误：{e}", exc_info=True)


# ========================
# 启动服务
# ========================

if __name__ == "__main__":
    import uvicorn

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
