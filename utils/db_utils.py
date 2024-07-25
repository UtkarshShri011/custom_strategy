from prisma import Prisma

async def check_gmx_position(link, copy_status):
    """
    Checks GMX position based on the link and copy status.

    Args:
        link (str): Link identifier.
        copy_status (bool): Copy status.

    Returns:
        dict: GMX position information.
    """
    async with Prisma() as prisma, prisma.tx() as transaction:
        data = await transaction.predicted_alpha_positions.find_first(
            where={
                "link": link,
                "copy_status": copy_status,
            },
        )

        return data
    
async def check_inference_logs(id):
    """
    Checks inference logs based on the ID.

    Args:
        id (str): Inference log ID.

    Returns:
        dict: Inference log information.
    """
    async with Prisma() as prisma, prisma.tx() as transaction:
        data = await transaction.inference_results.find_first(
            where={
                "id": id,
            },
        )

        return data

async def get_open_positions_count():
    async with Prisma() as prisma, prisma.tx() as transaction:
        data = await transaction.predicted_alpha_positions.find_many(
            where={
                "copy_status": True,
            },
        )
        return len(data)
    
async def get_vid_cursor():
    """
    Retrieve the current VID cursor (e.g., from database or configuration).

    Returns:
    - str or None: Current VID cursor value as a string, or None if not available.
    """
    async with Prisma() as prisma, prisma.tx() as transaction:
        data = await transaction.trade_cursor.find_first(order={"vid": "desc"})
        # data = await transaction.query_raw('SELECT * FROM trade_cursor ORDER BY CAST(vid AS INTEGER) DESC LIMIT 1')
        return data
    
async def insert_trade_inference_logs(inference_status, id, vid):
    """
    Inserts or updates trade inference logs with the given status and ID.

    Args:
        inference_status (str): The status of the inference.
        id (str): The ID of the trade.

    Returns:
        None
    """
    async with Prisma() as prisma, prisma.tx() as transaction:
        await transaction.inference_results.upsert(
            where={"id": id},
            data={
                "create": {"id": id, "inference_status": inference_status, "vid": vid},
                "update": {
                    "inference_status": inference_status,
                },
            },
        )

async def update_vid_cursor(
    vid, block_timestamp, token, position_side, link, status, reason
):
    """
    Asynchronously update vid status in the database.

    Parameters:
    - vid (int): Trade ID (VID) to update.
    - status (str): New status ('Skipped' or 'Triggered').
    """
    async with Prisma() as prisma, prisma.tx() as transaction:
        await transaction.trade_cursor.upsert(
            where={
                "vid": vid,
            },
            data={
                "create": {
                    "vid": vid,
                    "block_timestamp": block_timestamp,
                    "token": token,
                    "position_side": position_side,
                    "link": link,
                    "status": status,
                    "reason": reason,
                },
                "update": {
                    "block_timestamp": block_timestamp,
                    "token": token,
                    "position_side": position_side,
                    "link": link,
                    "status": status,
                    "reason": reason,
                },
            },
        )