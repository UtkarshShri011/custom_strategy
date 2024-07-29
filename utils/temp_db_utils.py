# pylint: disable=too-many-arguments
# pylint: disable = line-too-long
# pylint: skip-file
'Temporary database utilities.'
from __future__ import annotations

import psycopg2


async def fetch_db_connection():
    """
    Fetches the database connection.
    """
    db_connection = psycopg2.connect(
        dbname='alfredfeatures',
        port=5433,
        user='viewer',
        password='viewer',
        host='localhost',
    )
    return db_connection


async def check_gmx_position(link, copy_status):
    """
    Checks GMX position based on the link and copy status.

    Args:
        link (str): Link identifier.
        copy_status (bool): Copy status.

    Returns:
        dict: GMX position information.
    """
    conn = await fetch_db_connection()
    if conn is None:
        raise ValueError('Could not connect to database.')
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM predicted_alpha_positions WHERE link = '{link}' AND copy_status = '{copy_status}'",
    )
    data = cursor.fetchall()
    cursor.close()

    return data


async def check_inference_logs(inference_id: str):
    """
    Checks inference logs based on the ID.

    Args:
        inference_id (str): Inference log ID.

    Returns:
        dict: Inference log information.
    """
    conn = await fetch_db_connection()
    if conn is None:
        raise ValueError('Could not connect to database.')
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM inference_results WHERE id = '{inference_id}'",
    )
    data = cursor.fetchall()
    cursor.close()
    return data


async def get_open_positions_count():
    """
    Returns:
        int: Count of open positions.
    """
    conn = await fetch_db_connection()
    if conn is None:
        raise ValueError('Could not connect to database.')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT COUNT(*) FROM predicted_alpha_positions WHERE copy_status = True',
    )
    data = cursor.fetchall()
    cursor.close()
    return len(data)


async def get_vid_cursor():
    """
    Retrieve the current VID cursor (e.g., from database or configuration).

    Returns:
    - str or None: Current VID cursor value as a string, or None if not available.
    """

    conn = await fetch_db_connection()
    if conn is None:
        raise ValueError('Could not connect to database.')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM trade_cursor ORDER BY CAST(vid AS INTEGER) DESC LIMIT 1',
    )
    data = cursor.fetchall()
    cursor.close()
    return data


async def insert_trade_inference_logs(inference_status, inference_id, vid):
    """
    Inserts or updates trade inference logs with the given status and ID.

    Args:
        inference_status (str): The status of the inference.
        id (str): The ID of the trade.

    Returns:
        None
    """
    conn = psycopg2.connect(
        dbname='postgres',
        port=5432,
        user='postgres',
        password='utkarsh',
        host='localhost',
    )
    cursor = conn.cursor()
    if conn is None:
        raise ValueError('Could not connect to database.')
    # check if table is created or not
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS inference_results (id VARCHAR(255) PRIMARY KEY, inference_status VARCHAR(255), vid VARCHAR(255))',
    )
    cursor.commit()

    # insert data
    cursor.execute(
        f"INSERT INTO inference_results (id, inference_status, vid) VALUES ('{inference_id}', '{inference_status}', '{vid}') ON CONFLICT (id) DO UPDATE SET inference_status = '{inference_status}'",
    )
    conn.commit()
    cursor.close()
    conn.close()


def update_vid_cursor(
    self,
    vid,
    block_timestamp,
    token,
    position_side,
    link,
    status,
    reason,
):
    """
    Asynchronously update vid status in the database.

    Parameters:
    - vid (int): Trade ID (VID) to update.
    - status (str): New status ('Skipped' or 'Triggered').
    """
    self._log.error(f'Trade Cursor : {vid} {status} {reason}')
    # conn = psycopg2.connect(
    #     dbname="postgres",
    #     port=5432,
    #     user="postgres",
    #     password="utkarsh",
    #     host="localhost",
    # )
    # if conn is None:
    #     raise ValueError("Could not connect to database.")
    # cursor = conn.cursor()
    # # check if table is created or not

    # cursor.execute(
    #     "CREATE TABLE IF NOT EXISTS trade_cursor (vid VARCHAR(255) PRIMARY KEY, block_timestamp VARCHAR(255), token VARCHAR(255), position_side VARCHAR(255), link VARCHAR(255), status VARCHAR(255), reason VARCHAR(255))"
    # )
    # cursor.commit()

    # cursor.execute(
    #     f"UPDATE trade_cursor SET block_timestamp = '{block_timestamp}', token = '{token}', position_side = '{position_side}', link = '{link}', status = '{status}', reason = '{reason}' WHERE vid = '{vid}'"
    # )
    # conn.commit()
    # cursor.close()
    # conn.close()
