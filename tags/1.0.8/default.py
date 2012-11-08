# Copyright (C) 2012 Malte Loepmann (maloep@googlemail.com)
#
# This program is free software; you can redistribute it and/or modify it under the terms 
# of the GNU General Public License as published by the Free Software Foundation; 
# either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program; 
# if not, see <http://www.gnu.org/licenses/>.


# I have built this script from scratch but you will find some lines or ideas that are taken 
# from other xbmc scripts. Some basic ideas are taken from Redsandros "Arcade Browser" and I often 
# had a look at Nuka1195's "Apple Movie Trailers" script while implementing this one. Thanks for your work!



import os
import sys
import re

import xbmcaddon

# Shared resources
addonPath = ''
addon = xbmcaddon.Addon(id='script.games.rom.collection.browser')
addonPath = addon.getAddonInfo('path')

		
BASE_RESOURCE_PATH = os.path.join(addonPath, "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "pyparsing" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib", "pyscraper" ) )


# append the proper platforms folder to our path, xbox is the same as win32
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]

# Check to see if using a 64bit version of Linux
if re.match("Linux", env):
	try:
		import platform
		env2 = platform.machine()
		if(env2 == "x86_64"):
			env = "Linux64"
	except:
		pass

sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )



print 'sys.argv = ' +str(sys.argv)
for arg in sys.argv:
	param = str(arg)
	print 'param = ' +param
	if param == '' or param == 'script.games.rom.collection.browser':
		# Start the main gui
		if __name__ == "__main__":
			import gui
			
	#provide data that skins can show on home screen
	elif 'limit=' in param:
		
		import util, helper
		from gamedatabase import *
		from config import *
		gdb = GameDataBase(util.getAddonDataPath())
		gdb.connect()
				
		#cache lookup tables
		yearDict = helper.cacheYears(gdb)
		publisherDict = helper.cachePublishers(gdb)
		developerDict = helper.cacheDevelopers(gdb)
		reviewerDict = helper.cacheReviewers(gdb)
		genreDict = helper.cacheGenres(gdb)
				
		limit = int(param.replace('limit=', ''))
		games = Game(gdb).getMostPlayedGames(limit)
		
		config = Config()
		statusOk, errorMsg = config.readXml()
		
		settings = util.getSettings()
		
		import xbmcgui
		count = 0
		for gameRow in games:
		
			count += 1
			try:
				romCollection = config.romCollections[str(gameRow[util.GAME_romCollectionId])]				
		
				#get artwork that is chosen to be shown in gamelist
				files = File(gdb).getFilesByParentIds(gameRow[util.ROW_ID], gameRow[util.GAME_romCollectionId], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId])
				fileDict = helper.cacheFiles(files)
				files = helper.getFilesByControl_Cached(gdb, romCollection.imagePlacingMain.fileTypesForGameList, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict)		
				if(files != None and len(files) != 0):
					thumb = files[0]
				else:
					thumb = ""
					
				files = helper.getFilesByControl_Cached(gdb, romCollection.imagePlacingMain.fileTypesForMainViewBackground, gameRow[util.ROW_ID], gameRow[util.GAME_publisherId], gameRow[util.GAME_developerId], gameRow[util.GAME_romCollectionId], fileDict)		
				if(files != None and len(files) != 0):
					fanart = files[0]
				else:
					fanart = ""
				
				description = gameRow[util.GAME_description]
				if(description == None):
					description = ""
				
				year = helper.getPropertyFromCache(gameRow, yearDict, util.GAME_yearId, util.ROW_NAME)
				publisher = helper.getPropertyFromCache(gameRow, publisherDict, util.GAME_publisherId, util.ROW_NAME)
				developer = helper.getPropertyFromCache(gameRow, developerDict, util.GAME_developerId, util.ROW_NAME)
				genre = genreDict[gameRow[util.ROW_ID]]
				
				maxplayers = helper.saveReadString(gameRow[util.GAME_maxPlayers])
				rating = helper.saveReadString(gameRow[util.GAME_rating])
				votes = helper.saveReadString(gameRow[util.GAME_numVotes])
				url = helper.saveReadString(gameRow[util.GAME_url])
				region = helper.saveReadString(gameRow[util.GAME_region])
				media = helper.saveReadString(gameRow[util.GAME_media])				
				perspective = helper.saveReadString(gameRow[util.GAME_perspective])
				controllertype = helper.saveReadString(gameRow[util.GAME_controllerType])
				originaltitle = helper.saveReadString(gameRow[util.GAME_originalTitle])
				alternatetitle = helper.saveReadString(gameRow[util.GAME_alternateTitle])
				translatedby = helper.saveReadString(gameRow[util.GAME_translatedBy])
				version = helper.saveReadString(gameRow[util.GAME_version])
				playcount = helper.saveReadString(gameRow[util.GAME_launchCount])
				
				
				#get launch command
				filenameRows = File(gdb).getRomsByGameId(gameRow[util.ROW_ID])
				
				env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
				import launcher
				cmd, precmd, postcmd = launcher.buildCmd(filenameRows, romCollection, gameRow, False, True)
				
				if (romCollection.useEmuSolo):
					settings.setSetting(util.SETTING_RCB_LAUNCHONSTARTUP, 'true')
					
					#invoke batch file that kills xbmc before launching the emulator							
					if(env == "win32"):
						#There is a problem with quotes passed as argument to windows command shell. This only works with "call"
						cmd = 'call \"' +os.path.join(util.RCBHOME, 'applaunch.bat') +'\" ' +cmd						
					else:
						cmd = os.path.join(re.escape(util.RCBHOME), 'applaunch.sh ') +cmd
				else:
					#use call to support paths with whitespaces
					if(env == "win32" and not (os.environ.get( "OS", "xbox" ) == "xbox")):
						cmd = 'call ' +cmd
				
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Console" %count, romCollection.name)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Title" %count, gameRow[util.ROW_NAME])
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Thumb" %count, thumb)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Fanart" %count, fanart)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Plot" %count, description)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Year" %count, year)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Publisher" %count, publisher)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Developer" %count, developer)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Genre" %count, genre)
				
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Maxplayers" %count, maxplayers)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Region" %count, region)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Media" %count, media)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Perspective" %count, perspective)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Controllertype" %count, controllertype)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Playcount" %count, playcount)				
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Rating" %count, rating)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Votes" %count, votes)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Url" %count, url)				
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Originaltitle" %count, originaltitle)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Alternatetitle" %count, alternatetitle)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Translatedby" %count, translatedby)
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.Version" %count, version)				
				
				xbmcgui.Window(10000).setProperty("MostPlayedROM.%d.LaunchCommand" %count, cmd)
								
			except Exception, (exc):
				print 'RCB: Error while getting most played games: ' +str(exc)
		
		gdb.close()
	
	
		