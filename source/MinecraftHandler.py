import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import json
import asyncio



class Minecraft():
    
    # not all of these will be utilized but some are
    #basedirectory = "~/tempSOPbot/SOPbot/Minecraft/"
    serverStatus = "Offline"
    serverPlayerCount = 0
    serverMemoryAllocated = 16
    serverOverclocking = "Average"
    serverPlayerSize = 5
    selectedWorld = None
    worldProcess = None
    worldOnline = False
    discordClient = None
    ClientStatus = None # thread for updating client status (need to use asyncio.run in threading)
    myThread = None # basic thread for setting up server
    discordStatus = None
    selectedWorldDirectory = ""
    
    
    # commands
    commands = {}
    
    
    def __init__(self,discordClient = None,world = None):
        self.commands = { # list of minecraft server commands
                        "selectworld" : self.selectWorld,
                        "modifyworldsettings" : self.modifyWorldSettings,
                        "displayworldsettings" : self.displayWorldSettings,
                        "listworlds" : self.listWorlds,
                        "startworld" : self.startWorld,
                        "stopworld" : self.stopWorld,
                        "listplayers" : self.listPlayers
                        }
        
        self.discordClient = discordClient

     
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
        
        if self.worldOnline:
                
            await message.channel.send("World, " + self.selectedWorld + ", is already being hosted!")
            return
            
        # move to the directory that contains the spigot Jar
        currentDirectory = os.getcwd()
        newDirectory = "../Minecraft/" + self.selectedWorld + "/"
        os.chdir(newDirectory)
        newDirectory = os.getcwd()
        command = newDirectory + "/startWorld.sh"
        
        
        if self.worldOnline== False:
            
            #change to the correct directory
            self.worldProcess = subprocess.Popen(command,stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                
            await message.channel.send("Starting Minecraft world. Using world: " + self.selectedWorld)
            
            #await asyncio.sleep(180) # currently just wait for 3 minutes to start world
            #await message.channel.send(self.selectedWorld + " is ready!")
            
            #while True:
            #    consumeLine = self.worldProcess.stdout.readline()
            #   self.worldProcess.stdout.flush()
            #    if not consumeLine:
            #    break
            
            
            # parse through stdout until server setup
            self.myThread = threading.Thread(target=self.readOutput)
            self.myThread.start()
            
        os.chdir(currentDirectory) # after setup return to original dir
            
    
    def readOutput(self): #used to initialize when server is started
        
        while True:
        
            currentOutput = self.worldProcess.stdout.readline()
            self.worldProcess.stdout.flush()
            splitOutput = currentOutput.split()
        
            if splitOutput[3] == "Done":
                print("time taken to start server: " + splitOutput[4])
                self.worldOnline = True
                break
        
        #once server is setup create a asyncio thread to update discord status
        self.discordStatus = threading.Thread(target=asyncio.run,args=(self.updateDiscordStatus(),))
        self.discordStatus.start()
        
    
    
    async def stopWorld(self,message):
        
        # determine if there are players currently on server
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        worldList = self.worldProcess.stdout.readline()
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
        self.worldProcess = None
        self.worldOnline = False
        
        
        #self.myThread.stop()
        #self.myThread = None
        #discordActivity = discord.Game(name="Not hosting")
        #await self.discordClient.change_presence(activity=discordActivity)
        
         
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
        
        print("writting command")
        # run command and obtain result
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        
        while True:
        
            currentOutput = self.worldProcess.stdout.readline()
            self.worldProcess.stdout.flush()
            splitOutput = currentOutput.split()
            print(currentOutput)
            
            if "players" in splitOutput: # need to find more optimal way to flush
        
                outputString = currentOutput
                break
        
        #splitResult = commandResult.split()
        #playerCounter = int(splitResult[2])
        
        #outputString = "There are currently " + splitResult[2] + " users online. "
        
        
        #if playerCounter  > 0:
            
            #outputString += "Online users:\n"
            
            #for user in splitResult[10:]:
                
                #outputString += user + "\n"
                
                
        await message.channel.send(outputString)


    async def updateDiscordStatus(self): # works but need to update flush prior to updating status
        
        while(True):
            currentPlayers , maxPlayers = self.getPlayerCount()
            gameName = "Hosting " + self.selectedWorld + "(" + currentPlayers + "/" + maxPlayers + " Players)" 
            discordActivity = discord.Game(name=gameName)
            await self.discordClient.change_presence(activity=discordActivity)
            time.sleep(15)
            
            if self.worldOnline == False: # destroy thread since no world is hosted. Reset discord status once done
                return


    def getPlayerCount(self): # dont return player names, just count
        
        if self.worldOnline == False:
            return "" # return nothing since no world is open
        
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        
        while(True):
            
            currentLine = self.worldProcess.stdout.readline()
            
            if "players" in currentLine:
                
                splitLine = currentLine.split()
                return splitLine[5] , splitLine[10] # index 1: current players, index 2: player limit
                
 
