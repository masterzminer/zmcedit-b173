

import log
import directories

class ItemType (object):
    def __init__(self, id, name, image_coords=None, max_damage=0, damage_value=0, stacksize=64):
        self.id = id
        self.name = name
        self.image_coords = image_coords
        self.max_damage = max_damage
        self.damage_value = damage_value
        self.stacksize = stacksize
    def __repr__(self):
        return f"ItemType({self.id}, '{self.name}')"
    def __str__(self):
        return f"ItemType {self.id}: {self.name}"

class Items (object):
    def __init__(self, filename):
        try:
            with open(filename) as f:
                items_txt = f.read()
        except Exception as e:
            log.info(f"Error reading items.txt: {e}")
            raise RuntimeError("Cannot find built in assets for items")

        self.item_types = {}
        self.item_groups = []
        
        for line in items_txt.split("\n"):
            try:
                line = line.strip()
                if len(line) == 0: continue
                if line[0] == "#": continue;
                tilde = line[0] == "~"
                if tilde: 
                    fields = line.split()
                    name, icon, items = fields[1:4]
                    items = items.split(",")
                    self.item_groups.append((name, icon, items))
                    continue

                stacksize = 64
                damage_value = None
                max_damage = 0

                fields = line.split()
                if len(fields) >= 3 and not tilde:
                    max_damage = None
                    id, name, image_coords = fields[0:3]
                    if len(fields) > 3:
                        info = fields[3]
                        if info[0] == '(':
                            info = info[1:-1]
                        if info[0] == 'x':
                            stacksize = int(info[1:])
                        elif info[0] == '+':
                            max_damage = int(info[1:])
                        else:
                            damage_value = int(info)
                    id = int(id)
                    name = name.replace("_", " ")
                    image_coords = image_coords.split(",")

                    self.item_types[(id, damage_value)] = ItemType(id, name, image_coords, max_damage, damage_value, stacksize)
            except Exception as e:
                log.error(f"Error reading item data from line: {line}, {e}")

        self.names = dict((item.name, item.id) for item in self.item_types.values())

    def findItem(self, id=0, damage=None):
        item = self.item_types.get((id, damage))
        if item: return item

        item = self.item_types.get((id, None))
        if item: return item

        item = self.item_types.get((id, 0))
        if item: return item
        
        return ItemType(id, f"Unknown Item {id}:{damage}", damage_value=damage)

class ItemNotFound(KeyError): pass

items = Items(directories.ITEMS_FILE)