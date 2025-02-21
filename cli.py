import asyncio

import typer
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.session import AsyncSessionLocal
from core.init_data import init as init_data
from repositories import user_repository
from schemas.auth import UserCreate

app = typer.Typer()


async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


@app.command()
def init():
    """初始化数据库数据"""

    async def _init():
        async for db in get_db():
            await init_data(db)
            typer.echo("数据初始化完成")

    asyncio.run(_init())


@app.command()
def create_user(
    email: str = typer.Option(..., "--email", "-e", help="用户邮箱"),
    username: str = typer.Option(..., "--username", "-u", help="用户名"),
    password: str = typer.Option(..., "--password", "-p", help="密码"),
    superuser: bool = typer.Option(False, "--superuser", help="是否是超级用户"),
):
    """创建用户"""

    async def _create_user():
        async for db in get_db():
            user = await user_repository.get_by_email(db, email=email)
            if user:
                typer.echo(f"用户 {email} 已存在")
                return

            user_in = UserCreate(
                email=email,
                username=username,
                password=password,
                is_superuser=superuser,
                is_active=True,
            )
            user = await user_repository.create(db, obj_in=user_in)
            typer.echo(f"用户 {user.email} 创建成功")

    asyncio.run(_create_user())


@app.command()
def reset_password(
    email: str = typer.Option(..., "--email", "-e", help="用户邮箱"),
    password: str = typer.Option(..., "--password", "-p", help="新密码"),
):
    """重置用户密码"""

    async def _reset_password():
        async for db in get_db():
            user = await user_repository.get_by_email(db, email=email)
            if not user:
                typer.echo(f"用户 {email} 不存在")
                return

            user_in = {"password": password}
            user = await user_repository.update(db, db_obj=user, obj_in=user_in)
            typer.echo(f"用户 {user.email} 密码重置成功")

    asyncio.run(_reset_password())


if __name__ == "__main__":
    app()
