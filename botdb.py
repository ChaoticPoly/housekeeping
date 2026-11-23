import os
import aiomysql

pool: aiomysql.Pool | None = None

async def init_pool():
    global pool
    pool = await aiomysql.create_pool(
        host = os.getenv('DB_HOST', '127.0.0.1'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD'),
        db = os.getenv('DB_NAME'),
        autocommit = True,
        minsize = 1,
        maxsize=10,
    )

async def close_pool():
    if pool is not None:
        pool.close()
        await pool.wait_closed()

async def dbSaveRole(guild_id: int, user_id: int, role_id: int):
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO custom_roles (guild_id, user_id, role_id) VALUES (%s, %s, %s)",
                (guild_id, user_id, role_id),
            )

async def dbGetRole(guild_id: int, user_id: int):
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT role_id FROM custom_role WHERE guild_id = %s AND user_id = %s",
                (guild_id, user_id),
            )
            row = await cur.fetchone()
            return row[0] if row else None

async def dbDeleteRole(guild_id: int, user_id: int):
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM custom_roles WHERE guild_id = %s AND user_id = %s",
                (guild_id, user_id),
            )
