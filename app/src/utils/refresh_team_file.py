
import json
import os
import time
from src.routes.bot.bot import fetch_by_id
from src.logger import Logger

logger = Logger()

async def refresh_team_file(file_path, expire_time) -> None:
    if not os.path.exists(file_path):
        await get_team_data()
    if os.path.getmtime(file_path) < time.time() - expire_time: 
        os.remove(file_path)
        await get_team_data()


async def get_team_data():
    owner_id = [529007366365249546]
    owner_data = []
    owner_info = ""
    celestial_id = [485157849211863040]
    celestial_data = []
    celestial_info = ""
    guardian_id = [435848199551451146, 640935141958483978, 187126200873910272]
    guardian_data = []
    guardian_info = ""
    tech_id = [371350209160019970]
    tech_data = []
    tech_info = ""
    lumi_id = [628517615270363137, 1218643132363702352, 971730515256287303, 713397233936105532, 593568851203981324, 1055723680979746896]
    left_lumi = []
    right_lumi = []
    lumi_info = ""
    for _id in owner_id:
        return_data, _ = await fetch_by_id(_id)
        owner_data.append(return_data["user"])
        owner_info = "The founder of the community!"
        # logger.print(f"Owner data fetched: {owner_data}")
    for _id in celestial_id:
        return_data, _ = await fetch_by_id(_id)
        celestial_data.append(return_data["user"])
        celestial_info = "Administrator of the community!"
        # logger.print(f"Celestial data fetched: {celestial_data}")
    for _id in guardian_id:
        return_data, _ = await fetch_by_id(_id)
        guardian_data.append(return_data["user"])
        guardian_info = "The community moderators!"
        # logger.print(f"Guardian data fetched: {guardian_data}")
    for _id in tech_id:
        return_data, _ = await fetch_by_id(_id)
        tech_data.append(return_data["user"])
        tech_info = "The one who manages the bot!"
        # logger.print(f"Tech data fetched: {tech_data}")
    for i in range(len(lumi_id)):
        return_data, _ = await fetch_by_id(lumi_id[i])
        if i % 2 == 0:
            left_lumi.append(return_data["user"])
        else:
            right_lumi.append(return_data["user"])
        lumi_info = "The community event holders!"
        # logger.print(f"Lumi data fetched: {left_lumi} {right_lumi}")
        
    team_data = {"owner": (owner_data, owner_info, "Sanctuary Keeper"), "celestial": (celestial_data, celestial_info, "Celestial Guardian"), "guardian": (guardian_data, guardian_info, "Sky Guardian"), "tech": (tech_data, tech_info, "Tech Oracle"), "lumi": ({"left": left_lumi,"right": right_lumi}, lumi_info, "Event Luminary")}
    # logger.print(f"Team data created: {team_data}")
    open("team.json", "w").write(json.dumps(team_data, indent=4))
    Logger().log("PRINT", "Team data created.")