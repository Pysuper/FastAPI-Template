from fastapi import APIRouter, BackgroundTasks

from tasks.worker import example_task

router = APIRouter()


@router.post("/async-task")
async def create_async_task(word: str, background_tasks: BackgroundTasks):
    # 创建异步任务
    task = example_task.delay(word)
    return {"task_id": task.id, "status": "Task created"}
