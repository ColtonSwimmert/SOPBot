import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio


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
