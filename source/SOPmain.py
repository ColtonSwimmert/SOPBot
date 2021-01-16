#!/usr/bin/python
import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import json
import asyncio
from MinecraftHandler import *
from DiscordHandler import *


class MyClient(discord.Client):
    
    # prefix members
    prefix = "$OP "
    minecraftPrefix = "$OPCRAFT "
    
    # Handlers
    #minecraftHandler = Minecraft()
    #chatHandler = discordChat()
    
    
    # client handler dictionary
    handlers = {}
    
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.handlers = {
             self.prefix : discordChat(self),
             self.minecraftPrefix : Minecraft(self)
            }


    async def on_message(self, message):
        
        # parse a command and send to proper handler
        for key in self.handlers:
            
            if message.content.startswith(key): 
                
                message.content = message.content.lstrip(key)
                await self.handlerCommands(message,key)
                return 


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



########################################################################
# obtain botID and initialize client

idFile = open("botID.txt","r")
botID = idFile.read().rstrip('\n') # read id and remove '\n'
idFile.close()


client = MyClient()
client.run(botID)
