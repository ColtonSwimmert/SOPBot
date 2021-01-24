#!/usr/bin/python
import discord
import random
import threading
import time
from datetime import datetime
import os
import sys
import subprocess
import json
import asyncio
from MinecraftHandler import *
from DiscordHandler import *


class MyClient(discord.Client):
    
    # prefix members
    prefix = "$OP "
    minecraftPrefix = "$OPCRAFT "
    reactionPrefix = "~"
    soundPrefix = "!"
    
    
    # client handler dictionary
    handlers = {}
    
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        
        
        self.handlers = {
             self.prefix : discordChat(self),
             self.minecraftPrefix : Minecraft(self),
             self.reactionPrefix : discordReactions(),
             self.soundPrefix : discordSoundBoard()
            }

    async def startCleanUP(self):
        # tasks to run prior to closing the discord bot.
        
        self.handlers[self.reactionPrefix].cleanUp() # only have to do one of inherited classes
        print("SOP going offline")
        await self.logout()
        
        
    async def on_message(self, message):
        
        handler = None
        command = None

        # putting this here for now until I find a better place to put
        if message.content.startswith("`close"):
            await self.startCleanUP()


        # parse a command and send to proper handler
        for key in self.handlers:
            
            if message.content.startswith(key): 
                
                message.content = message.content.replace(key, "")              
                handler = self.handlers[key]
                command = self.getCommand(message.content)
                break

        
        if command == None: # prevents coroutine issues
            await asyncio.sleep(0)
            return


        # send command
        if command in handler.commands: # attempt to lookup function
            message.content = message.content.replace(command + " ", "")
            await handler.commands[command](message)
        elif "" in handler.commands: 
            await handler.commands[""](message) # default function
        else:
            await asyncio.sleep(0) # do nothing
        

    
    def getCommand(self,content): # obtain the command string 

        commandString = ""

        for char in content:
            if char == " ":
                break

            commandString += char

        return commandString


########################################################################
# obtain botID and initialize client

idFile = open("botID.txt","r")
botID = idFile.read().rstrip('\n') # read id and remove '\n'
idFile.close()

client = MyClient()
client.run(botID)
