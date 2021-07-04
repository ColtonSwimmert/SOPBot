
import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio
import json
import re
import requests


class SteamLobbyHandler():

    def __init__(self,discordClient = None):        
        # Create Dictionary for Games that this Server will usually play
        
        try:    
            self.gamesFile = open("steamGames.json", "r")
            self.gamesList = json.load(self.gamesFile)
            self.gamesFile.close()

            self.accountLinksFile = open("steamUsers.json", "r")
            self.accountLinks = json.load(self.accountLinksFile)
            self.accountLinksFile.close()

        except (IOError,ValueError) as e:

            print("Warning Json File containing steam games is not found!")
            print("Creating new json file \"steamGames.json\"")
            steamGamesFile = open("steamGames.json", "w")
            self.gamesList = {}
            steamGamesFile.write(str(self.gamesList))
            steamGamesFile.close()

            accountsFile = open("steamUsers.json", "w")
            self.accountLinks = {}
            accountsFile.write(str(self.accountLinks))
            accountsFile.close()

        # Handler commands
        self.commands = {
            "lobby" : self.createLobby,
            "embed" : self.embedLobby,
            "openlobbies" : self.displayOpenLobbies,
            "link" : self.linkAccount
        }


        # helper vars
        self.steamURL = "https://store.steampowered.com/app/"
        self.lookUpUrl = "https://steamid.io/lookup/"
        self.profileLookUp = "http://steamcommunity.com/profiles/"
        self.lobbies = {} #key creatorID, value steamLobby Class

    def cleanUp(self):
        pass #do nothing for now

    async def createLobby(self, message):
        host = message.author
        # splitMessage = re.split("[/]+", message.content)

        # if splitMessage[0] != "steam:" and splitMessage[1] != "joinlobby":
        #     # most likely an invalid lobby
        #     await message.channel.send("Invalid Lobby URL")
        #     return
        
        # appID = splitMessage[2]
        steamID = self.accountLinks[host.id]
        print("link: " + self.profileLookUp + str(steamID))
        profileResponse = requests.get(self.profileLookUp + str(steamID))
        print(profileResponse)
        if profileResponse.status_code != 200:
            # error
            await message.channel.send("Error Code")
            return


        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)",profileResponse.text).group(0)
        if lobbyLink != None:
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send("Error getting link")
            return

        appID = re.split("[/]+", lobbyLink)[2]

        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error id")
                return
        
        
        
        embeddedMessage = self.generateEmbedMessage(appID, host, lobbyLink)
        newMessage = await message.channel.send(embed=embeddedMessage)
        self.lobbies[host.id] = steamLobby(host.id,host.name,appID,self.gamesList[appID]["Name"], newMessage, embeddedMessage)
        await self.lobbies[host.id].updatePlayers()

    async def embedLobby(self, message): # DONE
        # Dont track users in this lobby but make an embedded message for the lobby
        # STEAM://JOINLOBBY/<APPID>/<STEAMLOBBYID>/steamID>

        host = message.author
        splitMessage = re.split("[/]+", message.content)

        if splitMessage[0] != "steam:" and splitMessage[1] != "joinlobby":
            # most likely an invalid lobby
            await message.channel.send("Invalid Lobby URL")
            return
        
        appID = splitMessage[2]
        
        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error")
                return

        embeddedMessage = self.generateEmbedMessage(appID, host, message.content)
        await message.channel.send(embed=embeddedMessage)

    def generateEmbedMessage(self, appID, host, lobbyLink): #DONE exception of updates
        game = self.gamesList[appID]
        embeddedMessage = discord.Embed(title = game["Name"])
        #embeddedMessage.set_image(url="https://cdn.discordapp.com/embed/avatars/0.png")
        embeddedMessage.set_thumbnail(url=str(game["Images"][0]))
        embeddedMessage.set_author(name= host.name + "'s Lobby", icon_url=host.avatar_url)
        embeddedMessage.add_field(name="Lobby Link", value=lobbyLink, inline=False)
        return embeddedMessage

    def addGame(self,appID): #DONE
        # if game not within gameList, add from steamdb

        # game is not in list, retreive data from steamdb
        response = requests.get(self.steamURL  + appID + "/")
        if response.status_code != 200:
            # error retreiving game
            return False
        
        # parse data from response
        nameResult = re.search("apphub_AppName\">(.+)<", response.text)
        # use default steam icon
        iconResult = "https://cdn.akamai.steamstatic.com/steam/apps/"
        iconResult += appID 
        iconResult += "/header.jpg"

        # will need improvement
        nameResult = nameResult.group(0).split(">")[1].rstrip("<")

        # add basic information to steam gamesList
        self.gamesList[appID] = {}
        self.gamesList[appID]["Name"] = nameResult
        self.gamesList[appID]["Images"] = []
        self.gamesList[appID]["Images"].append(iconResult)
        return True

    async def linkAccount(self, message):
        # Retreive users steam account information and save
        try:
            content = message.content.split("/")
            print(content)
            steamURL = content[4]
        except IndexError:
            await message.channel.send("Error parsing steam URL. Ensure link is valid.")
            return

        url_response = requests.get(self.lookUpUrl + steamURL)
        if url_response.status_code != 200:
            # if we dont get a valid response
            await message.channel.send("Error linking account!")
            return

        match = re.search("data-steamid64=\"\d+", url_response.text).group(0)
        steamID64 = match.split("\"")[1]
        # add steamID64 to json of users linked to the lobby system
        self.accountLinks[message.author.id] = steamID64 

    async def displayOpenLobbies(self,message):
        lobbyEmbed = discord.Embed(title = "Open Lobbies")
        lobbyEmbed.thumbnail(url="attachment://steamicon.png")
        lobbyEmbed.set_footer(text=str(len(self.lobbies)))
        for lobby in self.lobbies:
            gameName = "***" + self.lobbies[lobby].gameName + "***  "
            hostName = "Host: " + self.lobbies[lobby].hostName
            lobbyEmbed.add_field(name=gameName, value=hostName,inline=False)

        await message.channel.send(embed=lobbyEmbed)


class steamLobby():
    # Handle updating players and retreiving if lobby is still open
    REQUEST_KEY = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&"
    TEST_STRING = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&format=json&steamids=76561198240844888,76561198051944687"
    def __init__(self, hostID, hostName, appID, gameName, messageID, embeddedMessage):
        self.hostID = None
        self.hostName = hostName
        self.appID = None
        self.gameName = None
        self.players = {}
        self.originalMessage = messageID
        self.lobbyID = None
        self.playerCount = 1
        self.messageEmbed = embeddedMessage
        # add the host as the first person in the message
        self.messageEmbed.add_field(name="Player#" + str(self.playerCount), value=self.hostName)
        
        self.terminateFlag = False

    def cleanUp():
        self.terminateFlag = True


    async def updatePlayers(self):
        # check status of players and ensure that they're in the lobby
        # https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=<keyhere>&steamids=<csv steamid64 keys>
        # 5355C4BC38BDD5BE29B4CE3DA2495936
        
        await self.originalMessage.edit(embed=self.messageEmbed)
        
        while(True):
            if self.terminateFlag:
                return

            requestPackage = steamLobby.REQUEST_KEY + "steamids=" + str(self.players)
            response = requests.get(requestPackage)
            print(response)
            response = response.json()

            # go through list of users and determine if their steamlobbyid matches with the id of this lobby
            playerList = response['response']['players']

            for player in playerList:
                steamid = player['steamid']
                lobbyID = player.get('lobbysteamid',-1) # set to -1 if not in a lobby

                if lobbyID != self.lobbyID:
                    # user is not in the lobby
                    if steamid in self.players:
                        # remove this player and shift other players down one position
                        playerIndex = self.players[steamid]
                        fieldList = self.messageEmbed.fields

                        for index in range(playerIndex,len(fieldList), 1):
                            shiftIndex = index + 1
                            name = fieldList[shiftIndex].name
                            value = fieldList[shiftIndex].value
                            self.messageEmbed.insert_field_at(index,name=name,value=value,inline=False)

                        self.messageEmbed.remove_field(self.playerCount)
                        self.playerCount -= 1

                else:
                    # user is in the lobby
                    if steamid not in self.players:
                        # add them to the list, otherwise ignore
                        name = player['personname']
                        self.players[steamid] = [self.playerCount, name] # set their index and their name
                        self.messageEmbed.add_field(name="Player#" + str(playerCount + 1), value = name)
                        await message.edit(embed=self.messageEmbed)
                        self.playerCount += 1

            await asyncio.sleep(15)