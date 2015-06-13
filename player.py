# -*- coding: utf-8 -*-
# Authors: ep0s TurBoss
# Models: ep0s TurBoss

# Just sandboxing

from direct.task import Task

#from panda3d.core import OrthographicLens

from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletCylinderShape
from panda3d.bullet import BulletCapsuleShape
from panda3d.bullet import BulletCharacterControllerNode
from panda3d.bullet import ZUp

from panda3d.core import Point3
from panda3d.core import CollisionTraverser,CollisionNode
from panda3d.core import CollisionHandlerQueue,CollisionRay
from panda3d.core import Vec3,Vec4,BitMask32, VBase4
from panda3d.core import Point3, TransparencyAttrib,TextNode
from panda3d.core import PandaNode,NodePath
from panda3d.core import TransformState

from direct.actor.Actor import Actor

class Player():
	def __init__(self, app, hp, mana, speed, attackSpeed):
		
		self.app = app
		
		height = 2.5
		radius = 0.4
		
		shape = BulletCapsuleShape(radius, height - 2*radius, ZUp)
		
		self.playerNode = BulletCharacterControllerNode(shape, 0.4, 'Player')
		self.playerNP = self.app.worldNP.attachNewNode(self.playerNode)
		self.playerNP.setPos(-2, 0, 14)
		self.playerNP.setH(45)
		self.playerNP.setCollideMask(BitMask32.allOn())

		self.app.world.attachCharacter(self.playerNP.node())

		self.app.playerShape = self.playerNode
		
			
		self.hp = hp
		self.mana = mana
		self.speed = speed
		self.attackSpeed = attackSpeed
		
		self.cameraDistance = 20
		self.cameraAngle = 80
		self.cameraOrientation = 0
		
		self.floater = NodePath(PandaNode("floater"))
		self.floater.reparentTo(render)
		
		self.keyMap = {"left":0, "right":0, "forward":0, "cam-left":0, "cam-right":0, "jump":0}
		
		self.playerActor = Actor({	"body":"models/dt6",},
							{"body":{"walk":"models/dt6-walk"},
						})
		
		self.playerActor.setHpr(0,0,0)
		self.playerActor.setPos(0,0,-1)
		self.playerActor.setScale(0.1)
		
		self.playerActor.reparentTo(self.playerNP)
		
		self.playerHand = self.playerActor.exposeJoint(None, 'body', 'antebrazoder')
		#self.playerLeg = self.player.controlJoint(None, 'body', 'piernader')
		
		#self.playerLeg.setScale(2,1,1)
		
		self.models = []                 #A list that will store our models objects
		items = [("models/sword1", (0,5.1,-4), (0,90,0), .6),
				("models/maze", (0,5.1,-4), (0,90,0), .6)]
		
		for row in items:
			np = self.app.loader.loadModel(row[0])				#Load the model
			np.setPos(row[1][0], row[1][1], row[1][2])		#Position it
			np.setHpr(row[2][0], row[2][1], row[2][2])		#Rotate it
			np.setScale(row[3])								#Scale it
			np.reparentTo(self.playerHand)
			self.models.append(np)							#Add it to our models list
		
		
		
		self.item = 0
		self.isMoving = False
		
		self.setObject(self.item)							#Make object 0 the first shown
		
		self.app.disableMouse()
		self.app.camera.setPos(self.playerActor.getX(),self.playerActor.getY()+self.cameraDistance, self.cameraAngle)
		
		#lens = OrthographicLens()
		#lens.setFilmSize(20, 15)  # Or whatever is appropriate for your scene
		#self.app.cam.node().setLens(lens)
		
		#self.cTrav = CollisionTraverser()
		
		
		self.app.accept("arrow_left", self.setKey, ["left",1])
		self.app.accept("arrow_right", self.setKey, ["right",1])
		self.app.accept("arrow_up", self.setKey, ["forward",1])
		self.app.accept("a", self.setKey, ["cam-left",1])
		self.app.accept("s", self.setKey, ["cam-right",1])
		self.app.accept("space", self.setKey, ["jump",1])
		
		self.app.accept("arrow_left-up", self.setKey, ["left",0])
		self.app.accept("arrow_right-up", self.setKey, ["right",0])
		self.app.accept("arrow_up-up", self.setKey, ["forward",0])
		self.app.accept("a-up", self.setKey, ["cam-left",0])
		self.app.accept("s-up", self.setKey, ["cam-right",0])
		self.app.accept("space-up", self.setKey, ["jump",0])
		
		
		
		self.app.accept("wheel_up", self.moveCam, [1])
		self.app.accept("wheel_down", self.moveCam, [0])
		
		self.app.accept("i", self.toggleObject)
		
	def jump(self):
		self.playerNP.node().setMaxJumpHeight(10.0)
		self.playerNP.node().setJumpSpeed(10.0)
		self.playerNP.node().doJump()
	
	def moveCam(self, direction):
		
		if direction == 1 and self.cameraAngle < 100:
			self.cameraDistance += 1
			self.cameraAngle += 5
		elif direction == 0 and self.cameraAngle > 10:
			self.cameraDistance -= 1
			self.cameraAngle -= 5
		"""
		print("###################")
		print(self.cameraDistance)
		print(self.cameraAngle)
		print("###################")
		"""
		
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
		
		
		# If a move-key is pressed, move dt6 in the specified direction.
		
		
		speed = Vec3(0, 0, 0)
		omega = 0.0
		"""
		if inputState.isSet('forward'): speed.setY( 3.0)
		if inputState.isSet('reverse'): speed.setY(-3.0)
		if inputState.isSet('left'):    speed.setX(-3.0)
		if inputState.isSet('right'):   speed.setX( 3.0)
		if inputState.isSet('turnLeft'):  omega =  120.0
		if inputState.isSet('turnRight'): omega = -120.0
		"""
		
		if (self.keyMap["left"]!=0):
			omega =  200.0
		if (self.keyMap["right"]!=0):
			omega = -200.0
		if (self.keyMap["forward"]!=0):
			speed.setY( -10.0)
		if (self.keyMap["jump"]!=0):
			self.jump()

		self.playerNP.node().setAngularMovement(omega)
		self.playerNP.node().setLinearMovement(speed, True)
		
		# If dt6 is moving, loop the run animation.
		# If he is standing still, stop the animation.
		
		if (self.keyMap["forward"]!=0) or (self.keyMap["left"]!=0) or (self.keyMap["right"]!=0):
			if self.isMoving is False:
				self.playerActor.loop("walk")
				self.isMoving = True
		else:
			if self.isMoving:
				self.playerActor.stop()
				self.playerActor.pose("walk",1)
				self.isMoving = False
		
		
		return task.cont
		
	def updateCamera(self, task):
		
		# If the camera-left key is pressed, move camera left.
		# If the camera-right key is pressed, move camera right.
		
		#self.app.camera.lookAt(self.playerNP)
		
		#self.app.camera.setX(self.app.camera, self.cameraOrientation * globalClock.getDt())
		
		if (self.keyMap["cam-left"]!=0):
			self.cameraOrientation += 1
			
		if (self.keyMap["cam-right"]!=0):
			self.cameraOrientation -= 1
		
		self.app.camera.setPos(self.playerNP.getX(),self.playerNP.getY()+self.cameraDistance, self.cameraAngle)
		# The camera should look in dt6's direction,
		# but it should also try to stay horizontal, so look at
		# a floater which hovers above dt6's head.
		
		self.floater.setPos(self.playerNP.getPos())
		self.floater.setZ(self.playerNP.getZ() + 2.0)
		
		self.app.camera.lookAt(self.floater)
		return task.cont
