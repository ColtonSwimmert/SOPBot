import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio
import json

class discordUserEvents():
    '''
    Base class to handle data about user added sound clips and images
    '''
    
    JSON_FILE_NAME = "testJsonFile.json"
    EventInfo = None
    
    
    def __init__(self): # load data from json file. Update json while program is running
        
        jsonFile = open(self.JSON_FILE_NAME,"r")
        self.EventInfo = json.load(jsonFile)
        jsonFile.close()
        
    def setAuthorInfo(self): # store who added event
        
    def loadAuthor(self): # find what a person has added
        
    def loadEventInfo(self): # find info about an event
        
    def eventExist(self): # check if a filename already exists
    

class discordReactions(discordUserEvents):
    '''
    Add user reactions and allow for accessing reactions from 
    Host's computer.
    Additional: Image modifications, distortions, gray scales, etc
    '''
    
    # private members to store image information and Logs
    reactions = {}
    
    def __init__(self): # load reaction images from reaction directory
        
    def postReaction(self):
        pass
        
    def addReaction(self):
        pass
        
class discordSoundBoard(discordUserEvents):
    
    def __init__(self):
        
        
        
    

class discordChat(): # handler for chat related functions

    # command
    commands = {}
    discordClient = None
    
    
    def __init__(self, discordClient = None):
        
        self.discordClient = discordClient
        
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




