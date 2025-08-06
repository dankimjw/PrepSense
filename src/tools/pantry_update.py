async def deduct(conn, user_id: str, deductions: list[dict]):
    async with conn.transaction(isolation="serializable"):
        for d in deductions:
            q = """
                UPDATE pantry_item
                   SET qty_canon = qty_canon - $1,
                       updated_at = now()
                 WHERE item_id = $2
                   AND user_id  = $3
                   AND qty_canon >= $1
            """
            await conn.execute(q, d["need"], d["item_id"], user_id)
