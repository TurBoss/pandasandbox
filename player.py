# -*- coding: utf-8 -*-
# Authors: ep0s TurBoss
# Models: ep0s TurBoss

# Player


from random import randint as random

from direct.task import Task

from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollideMask

from panda3d.core import Vec3,Vec4,BitMask32, VBase4, LVecBase4
from panda3d.core import Point3, TransparencyAttrib,TextNode
from panda3d.core import PandaNode,NodePath
from panda3d.core import TransformState
from panda3d.core import OrthographicLens
from panda3d.core import ModifierButtons
from panda3d.core import Shader

from direct.actor.Actor import Actor

from direct.interval.IntervalGlobal import LerpQuatInterval, Sequence

class Player():
	def __init__(self, game, hp, mana, strength, dexterity, vigor, magic):

		self.game = game

		self.ori = 0.0
		self.lastori = -1
		self.zoomLevel = 0.0
		self.nextAttack = 0.0

		self.attacked = False

		# Atributes

		self.hp = hp
		self.mana = mana

		self.strength = strength
		self.dexterity = dexterity
		self.vigor = vigor
		self.magic = magic

		# Atributes calculated

		self.attackDamage = random(1, 7) + self.strength/100				# physical dmg = weapon damage * %str
		self.magicDamage = random(3, 12) + self.magic/100					# magic dmg = skill damage * %magic
		self.speed = 15 + 0													# speed = base speed + item
		self.runSpeed = 25 + 0												# run speed = base speed + item
		self.lateralSpeed = 10												# speed when moving sidewards
		self.lateralRunSpeed = 20											# run speed when moving sidewards
		self.backwardsSpeed = 10											# speed when moving backwards
		self.backwardsRunSpeed = 20											# run speed when moving backwards
		self.defense = 5 + self.vigor/2										# defense = armour + 1/2 vigor
		self.criticalChance = 10 + 0										# crit chance = base item + skill
		self.criticalMultiplier = self.attackDamage*1.5						# crit mult = base item + skill
		self.magicDefense = 2 + self.magic/2								# magic def = base item + 1/2 magic
		self.attackSpeed = (0.2 * self.dexterity) / 60						# attack speed = base * dex / 60


		self.keyMap = {
						"left":0,
						"right":0,
						"forward":0,
						"backward":0,

						"cam-left":0,
						"cam-right":0,

						"jump":0,
						"attack":0,
						"run":0
						}

		# Player Parts

		parts = ["head", "larm", "rarm", "lboot", "rboot", "lleg", "rleg", "lhand", "rhand", "torso"]

		self.previousPart = { name: None for name in parts }

		# Player Models & Animations

		models = { name: "models/hero/%s" % name for name in parts }

		animations = { name:{
								"standby":"models/hero/%s-standby" % name,
								"walk":"models/hero/%s-walk" % name,
								"walk-back":"models/hero/%s-walk-back" % name,
								"walk-side":"models/hero/%s-walk-side" % name,
								"slash-front": "models/hero/%s-slash-front" % name
							} for name in parts
						}

		for itemClass, items in self.game.items["items"].items():
			if itemClass == "armours":
				for itemType, value in items["lightarmours"].items():
					modelName = value["model"]

				for itemType, value in items["midarmours"].items():
					modelName = value["model"]

				for itemType, value in items["heavyarmours"].items():
					modelName = value["model"]

					models["torso-%s" % modelName] = "models/hero/torso-%s" % modelName

					animations["torso-%s" % modelName] = {
															"standby":"models/hero/torso-%s-standby" % modelName,
															"walk":"models/hero/torso-%s-walk" % modelName,
															"walk-back":"models/hero/torso-%s-walk-back" % modelName,
															"walk-side":"models/hero/torso-%s-walk-side" % modelName,
															"slash-front":"models/hero/torso-%s-slash-front" % modelName
														}

				for itemType, value in items["helmets"].items():
					modelName = value["model"]

					models["head-%s" % modelName] = "models/hero/head-%s" % modelName

					animations["head-%s" % modelName] = {
															"standby":"models/hero/head-%s-standby" % modelName,
															"walk":"models/hero/head-%s-walk" % modelName,
															"walk-back":"models/hero/head-%s-walk-back" % modelName,
															"walk-side":"models/hero/head-%s-walk-side" % modelName,
															"slash-front":"models/hero/head-%s-slash-front" % modelName
														}



		# Init Actor

		self.playerActor = Actor(models, animations)



		# Hide All Player Parts

		for itemClass, items in self.game.items["items"].items():
			if itemClass == "armours":
				for itemType, value in items["lightarmours"].items():
					modelName = value["model"]

				for itemType, value in items["midarmours"].items():
					modelName = value["model"]

				for itemType, value in items["heavyarmours"].items():
					modelName = value["model"]
					self.playerActor.hidePart("torso-%s" % modelName)

				for itemType, value in items["helmets"].items():
					modelName = value["model"]
					self.playerActor.hidePart("head-%s" % modelName)



		#self.playerActor.ls()

		# Shaders

		self.shader = Shader.load("shaders/testShader.sha", Shader.SL_Cg)
		#self.playerActor.setShader(self.shader)

		# End shaders

		self.moveFloater = NodePath(PandaNode("moveFloater"))
		self.moveFloater.reparentTo(render)
		self.moveFloater.setPos(self.game.playerStartPos)

		self.floater = NodePath(PandaNode("floater"))
		self.floater.reparentTo(render)
		#self.floater.setZ(8.0)

		self.playerActor.setHpr(0,0,0)
		self.playerActor.setScale(0.5)

		self.playerActor.reparentTo(self.moveFloater)

		#self.playerHand = self.playerActor.exposeJoint(None, 'body', 'manod')
		#self.playerHead = self.playerActor.controlJoint(None, 'body', 'cabeza')
		#self.playerHead.setScale(10,10,10)

		self.inventory = [["0" for x in range(10)] for x in range(5)]

		#			COLS-ROWS		#			COLS-ROWS
		self.inventory[0][3] = self.game.items["items"]["armours"]["heavyarmours"]["ironplate"]
		self.inventory[0][4] = self.game.items["items"]["armours"]["heavyarmours"]["steelplate"]
		self.inventory[0][5] = self.game.items["items"]["armours"]["heavyarmours"]["cuirass"]
		self.inventory[3][3] = self.game.items["items"]["armours"]["midarmours"]["leatherarmour"]
		self.inventory[0][0] = self.game.items["items"]["weapons"]["swords"]["longsword"]
		self.inventory[1][0] = self.game.items["items"]["armours"]["midarmours"]["leatherarmour"]
		self.inventory[0][8] = self.game.items["items"]["weapons"]["swords"]["longsword"]
		self.inventory[0][7] = self.game.items["items"]["weapons"]["spears"]["ironspear"]
		self.inventory[3][9] = self.game.items["items"]["armours"]["midarmours"]["leatherarmour"]
		self.inventory[1][9] = self.game.items["items"]["armours"]["midarmours"]["leatherarmour"]
		self.inventory[1][8] = self.game.items["items"]["armours"]["boots"]["leatherboots"]
		self.inventory[1][7] = self.game.items["items"]["armours"]["helmets"]["woolchaco"]
		self.inventory[0][6] = self.game.items["items"]["armours"]["helmets"]["goldencrown"]
		self.inventory[0][8] = self.game.items["items"]["armours"]["helmets"]["ironhelmet"]
		self.inventory[1][6] = self.game.items["items"]["armours"]["cloacks"]["woolcloack"]
		self.inventory[2][9] = self.game.items["items"]["armours"]["midarmours"]["leatherarmour"]
		self.inventory[2][8] = self.game.items["items"]["armours"]["boots"]["leatherboots"]
		self.inventory[2][7] = self.game.items["items"]["armours"]["helmets"]["woolchaco"]
		self.inventory[2][6] = self.game.items["items"]["armours"]["cloacks"]["woolcloack"]
		self.inventory[2][5] = self.game.items["items"]["armours"]["gloves"]["woolgloves"]
		self.inventory[1][5] = self.game.items["items"]["armours"]["gloves"]["woolgloves"]
		self.inventory[2][4] = self.game.items["items"]["accesories"]["rings"]["simplering"]
		self.inventory[1][4] = self.game.items["items"]["accesories"]["rings"]["simplering"]
		self.inventory[2][3] = self.game.items["items"]["accesories"]["trinkets"]["rubyamulet"]
		self.inventory[1][3] = self.game.items["items"]["accesories"]["trinkets"]["rubyamulet"]
		self.inventory[2][2] = self.game.items["items"]["armours"]["shields"]["ironshield"]
		self.inventory[1][2] = self.game.items["items"]["armours"]["shields"]["ironshield"]

		self.equip = {
						"armour":None,
						"helmet":None,
						"gloves":None,
						"boots":None,

						"cloack":None,

						"ringLeft":None,
						"ringRight":None,
						"trinket":None,

						"weapon":None,
						"weaponLeft":None,
						"weaponRight":None,

						"shield":None
					}

		self.models = []                 #A list that will store our models objects
		items = [("models/sword1", (0.0, 0.6, 1.5), (0,-90,0), 0.2),
				("models/maze", (0.0, 0.6, -1.5), (0,90,0), 0.2)]
		"""
		for row in items:
			np = self.game.loader.loadModel(row[0])				#Load the model
			np.setPos(row[1][0], row[1][1], row[1][2])		#Position it
			np.setHpr(row[2][0], row[2][1], row[2][2])		#Rotate it
			np.setScale(row[3])								#Scale it
			np.reparentTo(self.playerHand)
			#weaponNP.reparentTo(self.playerHand)
			self.models.append(np)							#Add it to our models list
		"""


		self.item = 0
		
		self.isMovingForward = False
		self.isMovingBackward = False
		self.isMovingSideRight = False
		self.isMovingSideLeft = False
		
		self.isMovingForwardLeft = False
		self.isMovingForwardRight = False
		
		self.isMovingSideRightUp = False
		self.isMovingSideRightDown = False
		
		self.isMovingSideLeftUp = False
		self.isMovingSideLeftDown = False
		
		self.isMovingBackwardLeft = False
		self.isMovingBackwardRight = False
		
		self.isAttacking = False

		self.setupControls()
		self.setupCamera()

		self.playerActor.loop("standby", "head")

		self.game.taskMgr.add(self.checkEquip, "checkTorsoTask", extraArgs=["torso", "armour"], appendTask=True)
		self.game.taskMgr.add(self.checkEquip, "checkHeadTask", extraArgs=["head", "helmet"], appendTask=True)

	def update(self, task):
		self.playerActor.setShaderInput("timer", task.time)
		return task.cont

	def checkEquip(self, partName, equipPart, task):

		# Check Equiped Parts

		if self.previousPart[partName] != self.equip[equipPart]:
			if self.equip[equipPart] != None and self.previousPart[partName] == None:
				self.playerActor.hidePart(partName)
				self.playerActor.showPart("%s-%s" % (partName, self.equip[equipPart]["model"]))
				self.previousPart[partName] = self.equip[equipPart]

			elif self.equip[equipPart] != None and self.previousPart[partName] != None:
				self.playerActor.hidePart("%s-%s" % (partName, self.previousPart[partName]["model"]))
				self.playerActor.showPart("%s-%s" % (partName, self.equip[equipPart]["model"]))
				self.previousPart[partName] = self.equip[equipPart]


			elif self.equip[equipPart] == None:
				self.playerActor.hidePart("%s-%s" % (partName, self.previousPart[partName]["model"]))
				self.playerActor.showPart(partName)
				self.previousPart[partName] = None

		return task.cont

	def setupCamera(self):

		self.game.disableMouse()
		self.game.camera.setPos(self.playerActor.getPos()+50)

		self.lens = OrthographicLens()
		self.lens.setFilmSize(45+self.zoomLevel, 35+self.zoomLevel)  # Or whatever is appropriate for your scene

		self.game.cam.node().setLens(self.lens)

		self.game.camLens.setFov(120)

	def setupControls(self):

		self.game.accept("a", self.setKey, ["left",1])
		self.game.accept("shift-a", self.setKey, ["left",1])
		self.game.accept("d", self.setKey, ["right",1])
		self.game.accept("shift-d", self.setKey, ["right",1])
		self.game.accept("w", self.setKey, ["forward",1])
		self.game.accept("shift-w", self.setKey, ["forward",1])
		self.game.accept("s", self.setKey, ["backward",1])
		self.game.accept("shift-s", self.setKey, ["backward",1])

		self.game.accept("a-up", self.setKey, ["left",0])
		self.game.accept("d-up", self.setKey, ["right",0])
		self.game.accept("w-up", self.setKey, ["forward",0])
		self.game.accept("s-up", self.setKey, ["backward",0])

		self.game.accept("mouse1", self.setKey, ["attack",1])
		self.game.accept("mouse1-up", self.setKey, ["attack",0])

		self.game.accept("shift-mouse1", self.setKey, ["attack",1])
		self.game.accept("shift-mouse1-up", self.setKey, ["attack",0])

		#self.game.accept("q", self.setKey, ["cam-left",1])
		#self.game.accept("e", self.setKey, ["cam-right",1])

		#self.game.accept("q-up", self.setKey, ["cam-left",0])
		#self.game.accept("e-up", self.setKey, ["cam-right",0])

		self.game.accept("space", self.setKey, ["jump",1])
		self.game.accept("space-up", self.setKey, ["jump",0])


		self.game.accept("shift", self.setKey, ["run",1])
		self.game.accept("shift-up", self.setKey, ["run",0])

		self.game.accept("wheel_up", self.moveCam, [1])
		self.game.accept("wheel_down", self.moveCam, [0])

		self.game.accept("shift-wheel_up", self.moveCam, [1])
		self.game.accept("shift-wheel_down", self.moveCam, [0])

		self.game.accept("t", self.toggleObject)

	def moveCam(self, zoom):
		if zoom == 0:
			self.zoomLevel += 5
			#if self.zoomLevel >= 30:
				#self.zoomLevel = 30

		elif zoom == 1:
			self.zoomLevel -= 5
			if self.zoomLevel <= 0:
				self.zoomLevel = 0

		#print self.zoomLevel
		self.lens.setFilmSize(45+self.zoomLevel, 35+self.zoomLevel)
		self.game.cam.node().setLens(self.lens)

	#def checkAttack(self):
		#animControl = self.playerActor.getAnimControl('slash', "body")

		#return animControl.isPlaying()


	def attack(self):
		if self.isAttacking is False:
			self.playerActor.play("slash-front")
			self.isAttacking = True

		self.isAttacking = False


	def setKey(self, key, value):
		self.keyMap[key] = value

	def setObject(self, i):
		for np in self.models: np.hide()
		self.models[i].show()
		self.item = i

	def toggleObject(self):

		if self.item == 1:
			self.item = 0
		else:
			self.item = 1

		for np in self.models: np.hide()
		self.models[self.item].show()

	def move(self, task):

		#self.playerActor.setPos(self.moveFloater.getPos())
		#self.playerActor.setZ(self.moveFloater.getZ())

		dt = globalClock.getDt()
		speed = 0

		if (self.keyMap["left"]):

			if (self.keyMap["run"]):
				speed = self.runSpeed
				#self.playerActor.setPlayRate(2.0, 'walk-side')
			else:
				speed = self.speed
				#self.playerActor.setPlayRate(1.0, 'walk-side')

			self.moveFloater.setX(self.moveFloater, speed * dt)
			self.moveFloater.setY(self.moveFloater, -speed * dt)

		if (self.keyMap["right"]):

			if (self.keyMap["run"]):
				speed = self.runSpeed
				#self.playerActor.setPlayRate(2.0, 'walk-side')
			else:
				speed = self.lateralSpeed
				#self.playerActor.setPlayRate(1.0, 'walk-side')

			self.moveFloater.setX(self.moveFloater, -speed * dt)
			self.moveFloater.setY(self.moveFloater, speed * dt)


		if (self.keyMap["forward"]):

			if (self.keyMap["run"]):
				speed = self.runSpeed
				#self.playerActor.setPlayRate(1.5, 'walk')
			else:
				speed = self.speed
				#self.playerActor.setPlayRate(1.0, 'walk')

			self.moveFloater.setY(self.moveFloater, -speed * dt)
			self.moveFloater.setX(self.moveFloater, -speed * dt)


		if (self.keyMap["backward"]):

			if (self.keyMap["run"]):
				speed = self.runSpeed
				#self.playerActor.setPlayRate(2.0, 'walk-back')
			else:
				speed = self.speed
				#self.playerActor.setPlayRate(1.0, 'walk-back')

			self.moveFloater.setY(self.moveFloater, speed * dt)
			self.moveFloater.setX(self.moveFloater, speed * dt)

		if (self.keyMap["attack"])  and (task.time > self.nextAttack):
			self.attack()
			self.nextAttack = task.time + self.attackSpeed
		self.keyMap["attack"] = 0


		"""
		if self.lastori != self.ori :
			turn = Sequence(LerpQuatInterval(self.playerActor, duration=0.05,  hpr=Vec3(self.ori, 0, 0), blendType='easeOut')).start()
			self.lastori = self.ori
		"""

		self.playerActor.headsUp(self.game.lookPoint)
		self.playerActor.setH(self.playerActor.getH()-180)

		#print(self.playerActor.getH())

		# If player is moving, loop the run animation.
		# If he is standing still, stop the animation.

		if self.keyMap["forward"] and self.keyMap["right"]:

			if ((self.playerActor.getH() < -45) and (self.playerActor.getH() > -135)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -135) and (self.playerActor.getH() > -225)):
					
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
					
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")
					
					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -225) and (self.playerActor.getH() > -315)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif (((self.playerActor.getH() < -315) and (self.playerActor.getH() < 0)) or ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -45))):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
					
				if self.isMovingSideLeft is False:
					
					if (self.keyMap["run"]):
						self.playerActor.setPlayRate(2.0, 'walk-side')
					else:
						self.playerActor.setPlayRate(1.0, 'walk-side')
					
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False
		
		elif self.keyMap["right"] and self.keyMap["backward"]:

			if ((self.playerActor.getH() < -135) and (self.playerActor.getH() > -225)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -225) and (self.playerActor.getH() > -315)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif (((self.playerActor.getH() < -315) and (self.playerActor.getH() < 0)) or ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -45))):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -45) and (self.playerActor.getH() > -135)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False
		
		elif self.keyMap["backward"] and self.keyMap["left"]:

			if ((self.playerActor.getH() < -225) and (self.playerActor.getH() > -315)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif (((self.playerActor.getH() < -315) and (self.playerActor.getH() < 0)) or ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -45))):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -45) and (self.playerActor.getH() > -135)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -135) and (self.playerActor.getH() > -225)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False
		
		elif self.keyMap["left"] and self.keyMap["forward"]:

			if (((self.playerActor.getH() < -315) and (self.playerActor.getH() < 0)) or ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -45))):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -45) and (self.playerActor.getH() > -135)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -135) and (self.playerActor.getH() > -225)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -225) and (self.playerActor.getH() > -315)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False
					
		elif self.keyMap["forward"]:

			if ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -90)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -90) and (self.playerActor.getH() > -180)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -180) and (self.playerActor.getH() > -270)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -270) and (self.playerActor.getH() < 0)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False

		elif self.keyMap["backward"]:

			if ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -90)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -90) and (self.playerActor.getH() > -180)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -180) and (self.playerActor.getH() > -270)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -270) and (self.playerActor.getH() < 0)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False

		elif self.keyMap["left"]:

			if ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -90)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -90) and (self.playerActor.getH() > -180)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

			elif ((self.playerActor.getH() < -180) and (self.playerActor.getH() > -270)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -270) and (self.playerActor.getH() < 0)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

		elif self.keyMap["right"]:

			if ((self.playerActor.getH() < 0) and (self.playerActor.getH() > -90)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideLeft is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = True
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -90) and (self.playerActor.getH() > -180)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk')
				else:
					self.playerActor.setPlayRate(1.0, 'walk')
				
				if self.isMovingForward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk")

					self.isMovingForward = True
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -180) and (self.playerActor.getH() > -270)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-side')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-side')
				
				if self.isMovingSideRight is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-side")

					self.isMovingForward = False
					self.isMovingSideRight = True
					self.isMovingSideLeft = False
					self.isMovingBackward = False

			elif ((self.playerActor.getH() < -270) and (self.playerActor.getH() < 0)):
				
				if (self.keyMap["run"]):
					self.playerActor.setPlayRate(2.0, 'walk-back')
				else:
					self.playerActor.setPlayRate(1.0, 'walk-back')
				
				if self.isMovingBackward is False:
					self.playerActor.stop()
					self.playerActor.loop("walk-back")

					self.isMovingForward = False
					self.isMovingSideRight = False
					self.isMovingSideLeft = False
					self.isMovingBackward = True

		else:
			if self.isMovingForward or self.isMovingBackward or self.isMovingSideLeft or self.isMovingSideRight:
				self.playerActor.stop()
				self.playerActor.loop("standby")
				self.isMovingForward = False
				self.isMovingBackward = False
				self.isMovingSideLeft = False
				self.isMovingSideRight = False

		return task.cont


	def updateCamera(self, task):

		self.floater.setPos(self.moveFloater.getPos())
		self.floater.setZ(self.moveFloater.getZ() + 2.0)

		self.game.camera.setPos(self.floater.getPos()+50)
		# The camera should look in player's direction,
		# but it should also try to stay horizontal, so look at
		# a floater which hovers above player's head.


		self.game.camera.lookAt(self.floater)

		return task.cont
