import os
import time

from src.utils.database import close_connection, create_connection
from src.config import config
from src.utils.refresh_team_file import refresh_team_file
from src.utils.remove_old_uploads import remove_expired_files
from src.routes.bot.bot import client
from src.logger import Logger
from discord.ext import tasks
from discord import Status

logger = Logger()

team_path = config.BASE_DIR + "/team.json"

@tasks.loop(hours=1)
async def printer():
    logger.log("PRINT", "Looping...")
    await rm_loop()

@client.event
async def on_ready() -> None:
    printer.start()
    await client.change_presence(status=Status.offline) # Set bot status to invisible
    logger.log("PRINT", "Bot is ready.")


async def rm_loop():
    if not client.is_ready():
        logger.log("PRINT", "Bot is not ready.")
        time.sleep(5)
    await refresh_team_file(team_path, config.TEAM_EXPIRE_TIME)
    
    connection = create_connection("Website")
    await remove_expired_files(connection, config.UPLOAD_DIR)
    close_connection(connection)


def main() -> None:
    if os.path.exists(team_path):
        os.remove(team_path)
    logger.log("PRINT", "Starting the worker.")
    client.run(config.TOKEN)
    logger.log("PRINT", "Worker stopped.")


if __name__ == "__main__":
    main()
