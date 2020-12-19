#!/usr/bin/python
import discord
import re
import random
import threading
import time
from gpiozero import Buzzer
from datetime import datetime
import os
import subprocess
import json
import asyncio

buzzer = Buzzer(15)


class Minecraft():
    
    # private members
    basedirectory = "~/tempSOPbot/SOPbot/Minecraft/"
    serverStatus = "Offline"
    serverPlayerCount = 0
    serverMemoryAllocated = 16
    serverOverclocking = "Average"
    serverPlayerSize = 5
    selectedWorld = None
    worldProcess = None
    worldOnline = False
    
    # commands
    commands = {}
    
    
    selectedWorldDirectory = ""
    
    def __init__(self,world = None):
        self.commands = { # list of minecraft server commands
                        "selectworld" : self.selectWorld,
                        "modifyworldsettings" : self.modifyWorldSettings,
                        "displayworldsettings" : self.displayWorldSettings,
                        "listworlds" : self.listWorlds,
                        "startworld" : self.startWorld,
                        "stopworld" : self.stopWorld,
                        "listplayers" : self.listPlayers
                        }
        

     
    async def displayWorldSettings(self,message):
        
        if self.selectedWorld == None:
            
            await message.channel.send("No world currently selected. List worlds with \"$OPCRAFT listworlds\"")
            return
        
        originalDirectory = os.getcwd()
        os.chdir("../Minecraft/" + self.selectedWorld + "/")
        
    
        output = subprocess.check_output("cat server.properties",text=True,shell=True)
        outputString = self.selectedWorld + " properties:\n"
        
        output = output.split("\n")
        
        
        desiredOutputKeys = ["gamemode","pvp","difficulty","max-players","spawn-protection","max-world-size"]
        keyLength = len(desiredOutputKeys)
        keyIndex = 0
        for line in output:
            print(line)
            currentLine = line.split("=")
            
            if currentLine[0] == desiredOutputKeys[keyIndex]:
                
                outputString += str(currentLine) + "\n"
                keyIndex = keyIndex + 1
                
                if keyIndex >= keyLength:
                    break
                
                
        
        await message.channel.send(outputString)
        os.chdir(originalDirectory) 
    
    
    async def startWorld(self,message):
    #java -Xms512M -Xmx1008M -jar ~/tempSOPbot/SOPbot/Minecraft/world2/spigot-1.16.3.jar nogui
        
        
        if self.selectedWorld == None:
            await message.channel.send("No world selected. Please select a world or create a new one...")
            return
            
        # change to the correct world directory
        
        if self.worldOnline:
                
            await message.channel.send("World, " + self.selectedWorld + ", is already being hosted!")
            
            
        currentDirectory = os.getcwd()
        
        newDirectory = "../Minecraft/" + self.selectedWorld + "/"
        os.chdir(newDirectory)
        
        command = "java -Xms512M -Xmx1008M -jar ~/tempSOPbot/SOPbot/Minecraft/world2/spigot-1.16.3.jar nogui"
            
        if self.worldOnline== False:
                
            #change to the correct directory
            self.worldProcess = subprocess.Popen(command,stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,shell=True,text=True)
                
            await message.channel.send("Starting Minecraft world. Using world: " + self.selectedWorld)
            
            await asyncio.sleep(180) # currently just wait for 3 minutes to start world
            await message.channel.send(self.selectedWorld + " is ready!")
            self.worldOnline = True
                
                
            os.chdir(currentDirectory)
            
    async def stopWorld(self,message):
        
        # determine if there are players currently on server
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        worldList = self.worldProcess.stdout.readline().split()
        #playerCount = int(worldList[2])
        
        
        #if playerCount > 0:
            #errorMessage = ""
            ##errorMessage += "Could not close server due to " + worldList[2] + " players connected to the world.\n"
            
            #await message.channel.send(errorMessage)
           # return
        
        # stop the server
        self.worldProcess.stdin.write("stop\n")
        self.worldProcess.stdin.flush()
        self.worldProcess.stdin.close()
        self.worldProcess.stdout.close()
        await message.channel.send("saving and closing " + self.selectedWorld)
            
        self.worldProcess.terminate() # terminate the process on a stop call
        self.worldOnline = False
        
         
    def modifyWorldSettings(self):
        # implement server properties handling at a later date.
        pass
        
     
     
    async def selectWorld(self,message): 
        
        originalDirectory = os.getcwd()
        os.chdir("../Minecraft/")
        worldNames = os.listdir()
        
        worldName = message.content.lower()
        outputString = ""
        
        for worldIndex in range(len(worldNames)):
            
            if worldName == worldNames[worldIndex].lower():
                self.selectedWorld = worldNames[worldIndex]
                outputString = "Selected \"" + worldNames[worldIndex] + "\" to be hosted"
                break
            
        if outputString == "":
            outputString = worldName + " was not found in the directory"
            
        await message.channel.send(outputString)
        
    async def listWorlds(self,message):
       
       originalDirectory = os.getcwd()
       
       os.chdir("../Minecraft/")
       worlds = os.listdir()
       
       worldListing = "List of worlds currently available:\n"
       
       for world in worlds:
           
           worldListing += world + ", "
        
       await message.channel.send(worldListing)
       os.chdir(originalDirectory)
       
    async def listPlayers(self,message):
        
        if self.worldOnline == False:
            
            await message.channel.send("No world hosted currently...")
            return
        
        # run command and obtain result
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        commandResult = self.worldProcess.stdout.readline()
        
        
        outputString = commandResult
        #splitResult = commandResult.split()
        #playerCounter = int(splitResult[2])
        
        #outputString = "There are currently " + splitResult[2] + " users online. "
        
        
        #if playerCounter  > 0:
            
            #outputString += "Online users:\n"
            
            #for user in splitResult[10:]:
                
                #outputString += user + "\n"
                
                
        await message.channel.send(outputString)
        
        
class discordChat(): # handler for any chat related functions

    # command
    commands = {}

    
    def __init__(self):
        
        self.commands = {
                "buzz" : self.tryBuzz,
                "wutface": self.displayWut,
                "repeat": self.repeat,
                "flip" : self.flipCoin
                }
        
            
    async def tryBuzz(self,message):
        await message.channel.send("buzzing")
        buzzer.on()
        time.sleep(1)
        buzzer.off()   
    
     
    async def displayWut(self,message):
    
        await message.channel.send(file=discord.File('wutface.jpg'))
    
     
    def repeat(self):
        pass

    async def flipCoin(self,message):
    
        await message.channel.send("Flipping...")
        random.seed(datetime.now())
        coinVal = random.randint(0,1)
        output = ""
    
    
        time.sleep(1.5)
    
        if coinVal == 0:
            output = "Heads!"
        else:
            output = "Tails!"
        
        await message.channel.send(output)


class MyClient(discord.Client):
    
    # prefix members
    prefix  = "$OP "
    minecraftPrefix = "$OPCRAFT "
    
    # Handlers
    minecraftHandler = Minecraft()
    chatHandler = discordChat()
    
    
    # client handler dictionary
    handlers = {}
    
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.handlers = {
             self.prefix : self.chatHandler,
             self.minecraftPrefix : self.minecraftHandler
            }

    async def on_message(self, message):

        for key in self.handlers:
            
            if message.content.startswith(key): 
                
                message.content = message.content.lstrip(key)
                await self.handlerCommands(message,key)
                break
            
    async def handlerCommands(self,message,messagePrefix): # send commands to the respective handlers
        
        # obtain handler, command, and remove the command from message
        handler = self.handlers[messagePrefix]
        parsedInput = message.content.split(" ")
        command = parsedInput[0].lower()
        
        
        if len(parsedInput) == 1:
            
            message.content = "" # give empty parameter
        else:    
            message.content = parsedInput[1].lower() 
        
        
        function2Call = None
        try: 
            function2Call = handler.commands[command]
            
        except KeyError:
            
            errorMessage = command + " is not part of the " + messagePrefix + " namespace..."
            
        
        if function2Call == None: # cant run function in try block or else infinite loop may occur on error.
            
            await message.channel.send(errorMessage)
        else:
            
            await handler.commands[command](message)
        
client = MyClient()
client.run('NzY5MDc0ODA1MjEwNDgwNjYw.X5Juug.ngiA-FdQ53kJQ0_Ic1OQOb7Co2g')

