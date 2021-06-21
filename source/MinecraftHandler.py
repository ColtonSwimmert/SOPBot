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
    
    
    def __init__(self,discordClient = None,world = None):

        # list of minecraft server commands
        self.commands = { 
                        "" : self.default,
                        "selectworld" : self.selectWorld,
                        "modifyworldsettings" : self.modifyWorldSettings,
                        "displayworldsettings" : self.displayWorldSettings,
                        "listworlds" : self.listWorlds,
                        "startworld" : self.startWorld,
                        "stopworld" : self.stopWorld,
                        "listplayers" : self.listPlayers,
                        "send" : self.message2Server
                        }
        
        self.minecraftPath = "../Minecraft/"
        self.discordClient = discordClient
    
    def default(self):
        pass

    def cleanUp(self): # clean up before turning off bot
        
        if self.worldOnline:
            self.terminateWorld()
     
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
    
            currentLine = line.split("=")
            
            if currentLine[0] == desiredOutputKeys[keyIndex]:
                
                outputString += str(currentLine) + "\n"
                keyIndex = keyIndex + 1
                
                if keyIndex >= keyLength:
                    break
            
        
        await message.channel.send(outputString)
        os.chdir(originalDirectory) 



    async def createWorld(self,message):
        pass



    async def startWorld(self,message):
        
        if self.selectedWorld == None:
            await message.channel.send("No world selected. Please select a world or create a new one...")
            return
        
        if self.worldOnline:
                
            await message.channel.send("World is already being hosted!")
            return
            
        # move to the directory that contains the spigot Jar
        currentDirectory = os.getcwd()
        newDirectory = "../Minecraft/" + self.selectedWorld + "/"
        os.chdir(newDirectory)
        newDirectory = os.getcwd()
        command = newDirectory + "/startWorld.sh"
        
        
        if self.worldOnline == False:
            
            #change to the correct directory
            self.worldProcess = subprocess.Popen(command,stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                
            await message.channel.send("Starting Minecraft world. Using world: " + self.selectedWorld)
            
            # parse through stdout until server setup
            self.myThread = threading.Thread(target=asyncio.run,args=(self.readOutput(message),))
            self.myThread.start()
            
        os.chdir(currentDirectory) # after setup return to original dir
            
    
    async def readOutput(self,message): #used in thread to determine when server is configured
        
        while True:
        
            currentOutput = self.worldProcess.stdout.readline()
            self.worldProcess.stdout.flush()
            splitOutput = currentOutput.split()
        
            if splitOutput[3] == "Done":
                self.worldOnline = True
                break
        
        #once server is setup create a asyncio thread to update discord status
        self.discordStatus = threading.Thread(target=asyncio.run,args=(self.updateDiscordStatus(message),))
        self.discordStatus.start()
    
    
    async def stopWorld(self,message):
        
        playersOnline, maxPlayerCount = self.getPlayerCount()
        
        if playersOnline != "0": # check if there is atleast 1 player online
            
            await message.channel.send("Could not close server due to " + playersOnline + " being online...")
            return

        await message.channel.send("saving and closing " + self.selectedWorld)
        self.terminateWorld()

    
    def terminateWorld(self):

        # stop the server
        self.worldProcess.stdin.write("stop\n")
        self.worldProcess.stdin.flush()
        self.worldProcess.stdin.close()
        self.worldProcess.stdout.close()

        # setworld to none so threads will stop
        self.selectedWorld = None     

        self.worldProcess.terminate() # terminate the process on a stop call
        
        # reset minecraft settings
        self.worldProcess = None
        self.worldOnline = False
        

    def modifyWorldSettings(self):
        # implement server properties handling at a later date.
        pass
     
    async def selectWorld(self,message): 
        
        worldNames = os.listdir(self.minecraftPath)
        worldName = message.content.lower().lstrip()

        outputString = ""
        
        for worldIndex in range(len(worldNames)):
            
            if worldName == worldNames[worldIndex].lower():
                self.selectedWorld = worldNames[worldIndex]
                outputString = "Selected \"" + worldNames[worldIndex] + "\" to be hosted"
                break
            
        if outputString == "":
            outputString = worldName + " was not found in the directory"
            
        await message.channel.send(outputString)
        
    async def listWorlds(self,message): # display list of worlds in discord channel
       worlds = os.listdir(self.minecraftPath)
       worldListing = "List of worlds currently available:\n"
       for world in worlds:
           worldListing += world + ", "
    
       await message.channel.send(worldListing.rstrip(", "))
       
    async def listPlayers(self,message): # list players in current world
        if self.worldOnline == False:
            await message.channel.send("No world hosted currently...")
            return
        
        # run command and obtain result
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        
        while True:
            currentOutput = self.worldProcess.stdout.readline()
            self.worldProcess.stdout.flush()
            
            if "players" in currentOutput: # need to find more optimal way to flush
                outputString = currentOutput
                break
                
        await message.channel.send(outputString)


    async def updateDiscordStatus(self,message): # works but need to update flush prior to updating status
        
        closeCounter = 0
        while(True):
            if self.selectedWorld == None: # destroy thread since no world is hosted. Reset discord status once done
                await self.discordClient.change_presence(activity=None)
                return

            currentPlayers , maxPlayers = self.getPlayerCount()
            gameName = "Hosting " + self.selectedWorld + "(" + currentPlayers + "/" + maxPlayers + " Players)" 
            discordActivity = discord.Game(name=gameName)


            if currentPlayers == "0":
                if closeCounter >= 75: # wait for 25 minutes before closing
                    await self.discordClient.change_presence(activity=None)
                    self.terminateWorld()
                    return 

                closeCounter += 1
            
            else:
                closeCounter = 0

            await self.discordClient.change_presence(activity=discordActivity)
            await asyncio.sleep(20)


    def getPlayerCount(self): # dont return player names, just count
        
        if self.selectedWorld == None:
            return '0' , '0' # return nothing since no world is open
        
        self.worldProcess.stdin.write("list\n")
        self.worldProcess.stdin.flush()
        
        for currentLine in self.worldProcess.stdout:
            
            if "players" in currentLine:
                splitLine = currentLine.split()
                return splitLine[5] , splitLine[10] # index 1: current players, index 2: player limit


    async def message2Server(self,message): # send message to hosted minecraft server
        
        if self.selectedWorld == None:
            thumbsDown = ':thumbsdown:'
            await message.channel.send(thumbsDown)
            return
        
        userMessage = "say " + message.author.name + " - " + message.content + "\n"
        self.worldProcess.stdin.write(userMessage)
        self.worldProcess.stdin.flush()
        thumbsUp = ':thumbsup:'
        await message.channel.send(thumbsUp)