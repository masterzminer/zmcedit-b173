# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling


from pymclevel import TAG_Int
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_Float

displayName = "Change Mob Properties"
	
noop = -1337
	
inputs = (
	("Health", noop),
	("VelocityX", noop),
	("VelocityY", noop),
	("VelocityZ", noop),
	("Fire", noop),
	("FallDistance", noop),
	("Air", noop),
	("AttackTime", noop),
	("HurtTime", noop),
	("Slime Size", noop)
)

def perform(level, box, options):
	health = options["Health"]
	vx = options["VelocityX"]
	vy = options["VelocityY"]
	vz = options["VelocityZ"]
	fire = options["Fire"]
	fall = options["FallDistance"]
	air = options["Air"]
	attackTime = options["AttackTime"]
	hurtTime = options["HurtTime"]
	size = options["Slime Size"]
	

	for (chunk, slices, point) in level.getChunkSlices(box):
		for e in chunk.Entities:
			x = e["Pos"][0].value
			y = e["Pos"][1].value
			z = e["Pos"][2].value
			
			if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
				if "Health" in e:
					if health != noop:
						e["Health"] = TAG_Short(health)
						
					if vx != noop:
						e["Motion"][0] = TAG_Double(vx)
					if vy != noop:
						e["Motion"][1] = TAG_Double(vy)
					if vz != noop:
						e["Motion"][2] = TAG_Double(vz)
					
					if fire != noop:
						e["Fire"] = TAG_Short(fire)
					
					if fall != noop:
						e["FallDistance"] = TAG_Float(fall)
					
					if air != noop:
						e["Air"] = TAG_Short(air)
					
					if attackTime != noop:
						e["AttackTime"] = TAG_Short(attackTime)
					
					if hurtTime != noop:
						e["HurtTime"] = TAG_Short(hurtTime)
					
					if size != noop and e["id"].value == "Slime":
						e["Size"] = TAG_Int(size)
					
					chunk.dirty = True
