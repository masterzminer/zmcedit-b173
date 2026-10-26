import config
from config import LastDir
from config_classes import DirectorySetting
import mcplatform

# TODO remove

def test_file(lastDir: DirectorySetting, new_path: str):
    
    print("testing", lastDir.directory, type(lastDir.directory), new_path)
    lastDir.directory = new_path

config.LastDir.world.add_observer(lambda value: print("changed", value))

print("-----", config.Keys.back)
print("-----", config.LastDirectories)
print("-----", type(config.LastDirectories))
print("-----", config.LastDirectories.world)
print("-----", type(config.LastDirectories.world))
config.LastDirectories.world = "bbbbbb"
print("-----", config.LastDirectories.world)
print("-----")
print("-----", config.LastDir)
print("-----", type(config.LastDir))
print("-----", config.LastDir.world)
print("-----", type(config.LastDir.world))
test_file(config.LastDir.world, "sssaaa")

mcplatform.askOpenFile(LastDir.filter, "hhhhhhh")

config.save_config()