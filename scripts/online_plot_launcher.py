import subprocess
import iblrig
from pathlib import Path

script = Path(iblrig.__file__).parent.joinpath("online_plots.py")

argument = "/home/nico/Downloads/FlatIron/mainenlab/Subjects/ZM_3003/2020-07-30/001/raw_behavior_data/_iblrig_taskData.raw.jsonable"

pl = subprocess.Popen(["python", script, argument])  # script, argument])

pl.terminate()