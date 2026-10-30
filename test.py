import config
from config import LastDir
from config_classes import DirectorySetting
import mcplatform

# TODO remove

def test_file(lastDir: DirectorySetting, new_path: str):
    
    print("testing", lastDir.v, type(lastDir.v), new_path)
    lastDir.set(new_path)

config.LastDir.world.add_observer(lambda value: print("changed", value))

print("-----", config.Keys.back)
print("-----", repr(config.Keys.back))
print("-----", f"{config.Keys.back}")
print("-----", f"{config.Settings.classic_mouse}")
print("-----", config.LastDir)
print("-----", type(config.LastDir))
print("-----", config.LastDir.world)
print("-----", type(config.LastDir.world))
print("-----", type(config.LastDir.world.get()))
print("-----", type(config.LastDir.world.v))
config.LastDir.world.set("bbbbbb")
print("-----", config.LastDir.world)
print("-----")
print("-----", config.LastDir)
print("-----", type(config.LastDir))
print("-----", config.LastDir.world)
print("-----", type(config.LastDir.world))
test_file(config.LastDir.world, "sssaaa")

mcplatform.askOpenFile(LastDir.filter, "hhhhhhh")

config.save_config()