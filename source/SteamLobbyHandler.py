
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
            "host" : self.hostLobby,
            "embed" : self.embedLobby,
            "openlobbies" : self.displayOpenLobbies,
            "link" : self.linkAccount
        }

        # helper vars
        self.client = discordClient
        self.steamURL = "https://store.steampowered.com/app/"
        self.lookUpUrl = "https://steamid.io/lookup/"
        self.profileLookUp = "http://steamcommunity.com/profiles/"
        self.lobbies = {} #key creatorID, value steamLobby Class

    def cleanUp(self):
        # dump newly acquired information to json files
        # dump discord/steam account links
        accountsFile = open("steamUsers.json", "w")            
        json.dump(self.accountLinks,accountsFile,indent=4)
        accountsFile.close()
        
        # dump steam games information
        steamGamesFile = open("steamGames.json", "w")
        json.dump(self.gamesList,steamGamesFile,indent=4)
        steamGamesFile.close()

    async def retreiveGameDetails(self,steamID):
        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text).group(0).rstrip("\" ")
        if lobbyLink != None:
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send("Error getting link")
            return

        appID = re.split("[/]+", lobbyLink)[2]
        lobbyID = re.split("[/]+", lobbyLink)[3]

        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error id")
                return

    async def createLobby(self, message):

        host = message.author
        hostID = str(host.id)
        
        # retreive user from steam links
        steamID = self.accountLinks.get(hostID,None)
        if steamID == None:
            await message.channel.send(host.mention + " Your account is not linked! Use !link <steam url> to link your account.")
            return

        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            await message.channel.send(host.mention + " Unable to retreive lobby information.")
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text)
        if lobbyLink != None:
            # need to update later
            lobbyLink = lobbyLink.group(0).rstrip("\" ")
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send(host.mention + " Could not retreive lobby, ensure that the lobby is joinable or you are not set to private.")
            return
        
        # retreive appID
        appID = re.split("[/]+", lobbyLink)[2]

        # check if games data is already stored
        game = self.gamesList.get(appID,None)
        if game == None:
            if not self.addGame(appID):
                print("Unable to add game data to SOPBot")
                return
        
        #lobbyMessage = host.name + "'s " + game["Name"] + " lobby: " + lobbyLink
        embeddedMessage = self.generateEmbedMessage(appID, host, lobbyLink)
        await message.channel.send(embed=embeddedMessage)


    async def hostLobby(self, message):
        
        # check if this user already has a lobby open

        host = message.author
        hostID = str(host.id)
        steamID = self.accountLinks[str(hostID)]
        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            await message.channel.send("Error Code")
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text).group(0).rstrip("\" ")
        if lobbyLink != None:
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send("Error getting link")
            return

        appID = re.split("[/]+", lobbyLink)[2]
        lobbyID = re.split("[/]+", lobbyLink)[3]

        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error id")
                return
        
        embeddedMessage = self.generateEmbedMessage(appID, host, lobbyLink)
        newMessage = await message.channel.send(embed=embeddedMessage)
        
        self.lobbies[hostID] = steamLobby(str(hostID),host.name,appID,self.gamesList[appID]["Name"], newMessage, embeddedMessage, steamID, lobbyID, self)
        await self.lobbies[hostID].updatePlayers()

    async def embedLobby(self, message): # DONE
        # Dont track users in this lobby but make an embedded message for the lobby
        # STEAM://JOINLOBBY/<APPID>/<STEAMLOBBYID>/steamID>

        host = message.author
        splitMessage = re.split("[/]+", message.content)

        if splitMessage[0] != "steam:" and splitMessage[1] != "joinlobby":
            # most likely an invalid lobby
            await message.channel.send("Could not retreive steam lobby")
            return
        
        appID = splitMessage[2]
        
        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                print("Unable to add game data to SOPBot")
                return

        embeddedMessage = self.generateEmbedMessage(appID, host, message.content)
        await message.channel.send(embed=embeddedMessage)

    def generateEmbedMessage(self, appID, host, lobbyLink): #DONE exception of updates
        game = self.gamesList[appID]
        embeddedMessage = discord.Embed(title = game["Name"])
        embeddedMessage.set_thumbnail(url=str(game["Images"][0]))
        embeddedMessage.set_author(name= host.name + "'s Lobby", icon_url=host.avatar_url)
        embeddedMessage.add_field(name="Lobby Link", value=lobbyLink, inline=False)
        return embeddedMessage

    def addGame(self,appID): #DONE

        # game is not in list, retreive data from steam
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

        # store game image inside respective folder, if game folder doesnt exist, then create it
        gameDirectory = "../Game_Files/" + nameResult + "/"
        if os.path.isdir(gameDirectory) == False: # directory doesnt exist 
            print("Creating directory for " + nameResult)
            os.mkdir(gameDirectory)

        gameIcon = requests.get(iconResult)
        if gameIcon.status_code == 200:
            gameImage = open(gameDirectory + "gameIcon.jpg", "wb")
            gameImage.write(gameIcon.content)
        return True
    
    async def addImage(self,message):
        pass

    async def linkAccount(self, message):
        # Retreive users steam account information and save
        try:
            content = message.content.split("/")
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
        self.accountLinks[str(message.author.id)] = steamID64 
        await message.channel.send("Successful link!")

    async def displayOpenLobbies(self,message):
        lobbyEmbed = discord.Embed(title = "Open Lobbies")
        lobbyEmbed.thumbnail(url="attachment://steamicon.png")
        lobbyEmbed.set_footer(text=str(len(self.lobbies)))
        for lobby in self.lobbies:
            gameName = "***" + self.lobbies[lobby].gameName + "***  "
            hostName = "Host: " + self.lobbies[lobby].hostName
            lobbyEmbed.add_field(name=gameName, value=hostName,inline=False)

        await message.channel.send(embed=lobbyEmbed)

    def closeLobby(self, message):
        # delete lobby from list
        pass



class steamLobby():
    # Handle updating players and retreiving if lobby is still open
    REQUEST_KEY = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&"
    TEST_STRING = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&format=json&steamids=76561198240844888,76561198051944687"
    
    def __init__(self, hostID, hostName, appID, gameName, messageID, embeddedMessage, steamID, lobbyID, lobbyHandler):
        self.hostID = hostID
        self.hostName = hostName
        self.appID = None
        self.gameName = None
        self.players = {}
        self.originalMessage = messageID
        self.lobbyID = lobbyID
        self.playerCount = 1
        self.messageEmbed = embeddedMessage
        # add the host as the first person in the message
        self.messageEmbed.add_field(name="Player#" + str(self.playerCount), value=self.hostName)
        self.terminateFlag = False
        self.players[steamID] = [0, self.hostName] # format lobby position, name
        self.lobbyHandler = lobbyHandler
        self.thumbsUP = "👍"

    def cleanUp():
        self.terminateFlag = True
    
    def getMessageID(self):
        return self.originalMessage.id
    
    def addPlayer(self, steamID, name):
        # add this player to the track list for this steam lobby

        self.players[steamID] = [-1, name] # set to -1 for index
        return True

    async def updatePlayers(self):
        # check status of players and ensure that they're in the lobby
        # https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=<keyhere>&steamids=<csv steamid64 keys>
        # 5355C4BC38BDD5BE29B4CE3DA2495936
        thumbsUP = self.thumbsUP
        await self.originalMessage.edit(embed=self.messageEmbed)
        await self.originalMessage.add_reaction(thumbsUP)

        while(True):      
            print("Updating " + self.hostName + "'s Lobby!")
            # add users who are interested in joining the lobby to the users list
            #cachedMessage = await self.originalMessage.channel.fetch_message(self.messageEmbed.id)
            #reactors = await cachedMessage.reactions[0].users().flatten()

            # for user in reactors:
            #     if self.players.get(user.id,None) == None: # check if user is currently not in the steam ID list
            #         # retreive steam ID and link their name/position to the lobby embed
            #         steamID = self.accountLinks[user.id]
            #         self.players[steamID] = [self.playerCount, user.name]
            #         self.playerCount += 1            

            print("Tracking players " + str(self.players))
            requestPackage = steamLobby.REQUEST_KEY + "steamids=" + str(self.players)
            response = requests.get(requestPackage)
            response = response.json()
        
            playerList = response['response']['players']

            for player in playerList:
                steamid = player['steamid']
                lobbyID = player.get('lobbysteamid',-1) # set to -1 if not in a lobby

                if lobbyID != self.lobbyID and self.players[steamid][0] != -1:
                    # user is not in the lobby
                    if steamid in self.players:
                        if len(self.players) > 1:
                            # remove this player and shift other players down one position
                            playerIndex = self.players[steamid][0]
                            fieldList = self.messageEmbed.fields
                            for index in range(playerIndex,len(fieldList), 1):
                                shiftIndex = index + 1
                                name = fieldList[shiftIndex].name
                                value = fieldList[shiftIndex].value
                                self.messageEmbed.insert_field_at(index,name=name,value=value,inline=False)

                            self.messageEmbed.remove_field(self.playerCount)
                            self.players[steamid][0] = -1
                            self.playerCount -= 1
                        else:
                            # was the last player, close the lobby
                            print("close lobby")
                            # TODO insert destructor commands after
                            self.playerCount = 0
                            self.messageEmbed.remove_field(1)
                            self.messageEmbed.add_field(name="Lobby Status:", value="Closed", inline=True)
                            #self.messageEmbed.insert_field_at(1,name="Lobby Closed!",value="",inline=True)
                            await self.originalMessage.edit(embed=self.messageEmbed)
                            return
                else:
                    # user is in the lobby
                    if self.players[steamid][0] == -1:
                        # add them to the list, otherwise ignore
                        self.players[steamid] = [self.playerCount, name] # set their index and their name
                        self.messageEmbed.add_field(name="Player#" + str(playerCount + 1), value = name)
                        await message.edit(embed=self.messageEmbed)
                        self.playerCount += 1
                    

            print(self.playerCount)

            if self.playerCount == 0:
                # no players remain, close lobby
                return

            await asyncio.sleep(15) # wait 15 seconds before updating again


        def selectNewHost(self):
            # if the host leaves the lobby and lobby remains open(I think some games allow this)
            pass