#!/usr/bin/python
import discord
import os
import json
import asyncio
from MinecraftHandler import *
from DiscordHandler import *


class MyClient(discord.Client):
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        
        # prefix members
        self.prefix = "$OP "
        self.minecraftPrefix = "$OPCRAFT "
        self.reactionPrefix = "~"
        self.soundPrefix = "$"

        # handlers 
        self.handlers = {
             self.prefix : discordChat(self),
             self.minecraftPrefix : Minecraft(self),
             self.reactionPrefix : discordReactions(),
             self.soundPrefix : discordSoundBoard()
            }

    async def startCleanUP(self):
        # clean up all handlers prior to exit
        
        for key in self.handlers: 

            self.handlers[key].cleanUp()

        print("SOP going offline")
        await self.logout()
        
        
    async def on_message(self, message):
        
        handler = None
        command = None

        # putting this here for now until I find a better place to put
        if message.content.startswith("`close"):
            await self.startCleanUP()
            return


        # parse a command and send to proper handler
        for key in self.handlers:
            
            if message.content.startswith(key): 
                
                message.content = message.content.replace(key, "")              
                handler = self.handlers[key]
                command = self.getCommand(message.content)
                break
            
        if command == None: # if no command, do nothing
            await asyncio.sleep(0)
            return

        # send command
        if handler.commands.get(command,None) != None: # attempt to lookup function
            message.content = message.content.replace(command + " ", "")
            await handler.commands[command](message)
        elif handler.commands.get("",None) != None: 
            await handler.commands[""](message) # run default function
        else:
            await asyncio.sleep(0) # do nothing
        

    # CLIENT HELPER FUNCTIONS
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