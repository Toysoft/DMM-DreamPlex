# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012

https://github.com/DonDavici/DreamPlex

Some of the code is from other plugins:
all credits to the coders :-)

DreamPlex Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

DreamPlex Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
"""
#=================================
#IMPORT
#=================================
import sys
import time

from os import system, popen
from Screens.Standby import TryQuitMainloop

from enigma import eConsoleAppContainer

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.config import config
from Components.Label import Label

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Console import Console as SConsole

from __common__ import printl2 as printl, testInetConnectivity

from __init__ import getVersion, _ # _ is translation

#===============================================================================
#
#===============================================================================
class DPS_SystemCheck(Screen):

	oeVersion = None
	check = None
	latestVersion = None

	def __init__(self, session):
		printl("", self, "S")

		Screen.__init__(self, session)
		self.session = session
		self["actions"] = ActionMap(["ColorActions", "SetupActions" ],
		{
		"ok": self.startSelection,
		"cancel": self.cancel,
		"red": self.cancel,
		}, -1)

		vlist = []

		self.oeVersion = self.getBoxArch()

		if self.oeVersion == "mipsel":
			vlist.append((_("Check for gst-plugin-fragmented"), "oe16"))

		elif self.oeVersion == "mips32el":
			vlist.append((_("Check for gst-plugins-bad-fragmented"), "oe20"))

		else:
			printl("unknown oe version", self, "W")
			vlist.append((_("Check for gst-plugin-fragmented if you are using OE16."), "oe16"))
			vlist.append((_("Check for gst-plugins-bad-fragmented if you are using OE20."), "oe20"))

		vlist.append((_("Check curl installation data."), "check_Curl"))
		vlist.append((_("Check mjpegtools intallation data."), "check_jpegTools"))
		vlist.append((_("Check python imaging installation data."), "check_Pil"))

		if config.plugins.dreamplex.showUpdateFunction.value:
			vlist.append((_("Check for update."), "check_Update"))

		self["header"] = Label()
		self["content"] = MenuList(vlist)

		self.onLayoutFinish.append(self.finishLayout)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishLayout(self):
		printl("", self, "S")

		self.setTitle(_("System - Systemcheck"))

		self["header"].setText(_("Functions List:"))

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def startSelection(self):
		printl("", self, "S")

		selection = self["content"].getCurrent()

		if selection[1] == "oe16" or selection[1] == "oe20":
			self.checkLib(selection[1])

		if selection[1] == "check_Curl":
			self.checkCurlInstallation()

		if selection[1] == "check_jpegTools":
			self.checkJpegToolsInstallation()

		if selection[1] == "check_Pil":
			self.checkPythonImagingInstallation()

		if selection[1] == "check_Update":
			self.checkForUpdate()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkForUpdate(self):
		printl("", self, "S")

		if testInetConnectivity() and self.checkCurlInstallation(True):
			printl( "Starting request", self, "D")
			curl_string = 'curl -s -k "%s"' % "https://api.github.com/repos/DonDavici/DreamPlex/tags"

			printl("curl_string: " + str(curl_string), self, "D")
			self.response = popen(curl_string).read()
			printl("response: " + str(self.response), self, "D")
			starter = 19
			closer = self.response.find('",', 0, 50)
			printl("closer: " + str(closer), self, "D")
			latestVersion = self.response[starter:closer] # is a bit dirty but better than forcing users to install simplejson
			printl("latestVersion: " + str(latestVersion), self, "D")

			installedVersion = getVersion()
			printl("InstalledVersion: " + str(installedVersion), self, "D")

			isBeta = self.checkIfBetaVersion(latestVersion)
			printl("isBeta: " + str(isBeta), self, "D")

			if config.plugins.dreamplex.updateType.value == "1" and isBeta == True: # Stable
				latestVersion = self.searchLatestStable()

			if latestVersion > installedVersion:
				self.latestVersion = latestVersion
				self.session.openWithCallback(self.startUpdate, MessageBox,_("Your current Version is " + str(installedVersion) + "\nUpdate to revision " + str(latestVersion) + " found!\n\nDo you want to update now?"), MessageBox.TYPE_YESNO)

			else:
				self.session.openWithCallback(self.close, MessageBox,_("No update available"), MessageBox.TYPE_INFO)

		else:
			self.session.openWithCallback(self.close, MessageBox,_("No internet connection available or curl is not installed!"), MessageBox.TYPE_INFO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def checkIfBetaVersion(self, foundVersion):
		printl("", self, "S")

		isBeta = foundVersion.find("beta")
		if isBeta != -1:

			printl("", self, "C")
			return True
		else:

			printl("", self, "C")
			return False

	#===========================================================================
	#
	#===========================================================================s
	def searchLatestStable(self):
		printl("", self, "S")

		isStable = False
		latestStabel = ""
		leftLimiter = 0

		while not isStable:
			starter = self.response.find('},', leftLimiter)
			printl("starter: " + str(starter), self, "D")
			end = starter + 50
			closer = self.response.find('",', starter, end)
			printl("closer: " + str(closer), self, "D")
			# is a bit dirty but better than forcing users to install simplejson
			start = (self.response.find('": "', starter, end)) + 4 # we correct the string here right away => : "1.09-beta.9 becomes 1.09.beta.9
			latestStabel = self.response[start:closer]
			printl("found version: " + str(latestStabel), self, "D")
			isBeta = self.checkIfBetaVersion(latestStabel)
			if not isBeta:
				isStable = True
			else:
				leftLimiter = closer

		printl("latestStable: " + str(latestStabel), self, "D")

		printl("", self, "C")
		return latestStabel

	#===========================================================================
	#
	#===========================================================================
	def startUpdate(self, answer):
		printl("", self, "S")

		if answer is True:
			self.updateToLatestVersion()
		else:
			self.close()

		printl("", self, "C")

	def startPluginUpdate(self):
		self.container=eConsoleAppContainer()
		self.container.appClosed.append(self.finishupdate)
		self.container.execute()

	#===========================================================================
	#
	#===========================================================================
	def updateToLatestVersion(self):
		printl("", self, "S")

		remoteUrl = "http://dl.bintray.com/dondavici/Dreambox/enigma2-plugin-extensions-dreamplex_" + str(self.latestVersion) + "_all.ipk?direct"

		cmd = "opkg install --force-overwrite --force-depends " + str(remoteUrl)

		printl("remoteUrl: " + str(remoteUrl), self, "D")
		printl("cmd: " + str(cmd), self, "D")

		self.session.open(SConsole,"Excecuting command:", [cmd] , self.finishupdate)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def finishupdate(self):
		printl("", self, "S")

		time.sleep(2)
		self.session.openWithCallback(self.e2restart, MessageBox,_("Enigma2 must be restarted!\nShould Enigma2 now restart?"), MessageBox.TYPE_YESNO)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def e2restart(self, answer):
		printl("", self, "S")

		if answer is True:
			try:
				self.session.open(TryQuitMainloop, 3)
			except Exception, ex:
				printl("Exception: " + str(ex), self, "W")
				data = "TryQuitMainLoop is not implemented in your OS.\n Please restart your box manually."
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
		else:
			self.close()

		printl("", self, "C")

	#===========================================================================
	# override is used to get bool as answer and not the plugin information
	#===========================================================================
	def checkCurlInstallation(self, override=False):
		printl("", self, "S")

		command = "opkg status curl"

		self.check = "curl"
		state = self.executeCommand(command, override)

		printl("", self, "C")
		return state

	#===========================================================================
	#
	#===========================================================================
	def checkJpegToolsInstallation(self):
		printl("", self, "S")

		command = "opkg status mjpegtools"

		self.check = "mjpegtools"
		state = self.executeCommand(command)

		printl("", self, "C")
		return state

	#===========================================================================
	#
	#===========================================================================
	def checkPythonImagingInstallation(self):
		printl("", self, "S")

		command = "opkg status python-imaging"

		self.check = "pythonImaging"
		state = self.executeCommand(command)

		printl("", self, "C")
		return state

	#===============================================================================
	#
	#===============================================================================
	def checkLib(self, arch):
		printl("", self, "S")

		command = None

		if arch == "oe16":
			command = "opkg status gst-plugin-fragmented"
			self.oeVersion = "mipsel"

		elif arch == "oe20":
			command = "opkg status gst-plugins-bad-fragmented"
			self.oeVersion = "mips32el"

		else:
			printl("someting went wrong with arch type", self, "W")

		self.check = "gst"
		self.executeCommand(command)

		printl("", self, "C")


	#===============================================================================
	#
	#===============================================================================
	def executeCommand(self, command, override=False):
		printl("", self, "S")

		pipe = popen(command)

		if pipe:
			data = pipe.read(8192)
			pipe.close()
			if data is not None and data != "":
				if override:
					return True
				# plugin is installed
				self.session.open(MessageBox, _("Information:\n") + data, MessageBox.TYPE_INFO)
			else:
				if override is False:
					return False
				# plugin is not install
				if self.check == "gst":
					self.session.openWithCallback(self.installStreamingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "curl":
					self.session.openWithCallback(self.installCurlLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "jpegTools":
					self.session.openWithCallback(self.installJpegToolsLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				elif self.check == "pythonImaging":
					self.session.openWithCallback(self.installPyhtonImagingLibs, MessageBox, _("The selected plugin is not installed!\n Do you want to proceed to install?"), MessageBox.TYPE_YESNO)

				else:
					printl("no proper value i self.check", self, "W")

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installCurlLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install curl"

			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install curl"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			if not system(command):
				# Successfully installed
				#defaultServer = plexServerConfig.getDefaultServer()
				#self.openSectionlist(defaultServer)
				pass
			else:
				# Fail, try again and report the output...
				pipe = popen(command)
				if pipe is not None:
					data = pipe.read(8192)
					if data is None:
						data = "Unknown Error"
					pipe.close()
					self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
				# Failed to install
				self.cancel()
		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installJpegToolsLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install mjpegtools"

			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install mjpegtools"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			self.executeInstallationCommand(command)
		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installPyhtonImagaingLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install python-imaging"

			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install python"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			self.executeInstallationCommand(command)

		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def installStreamingLibs(self, confirm):
		printl("", self, "S")

		command = ""

		if confirm:
			# User said 'Yes'

			if self.oeVersion == "mipsel":
				command = "opkg update; opkg install gst-plugin-fragmented"

			elif self.oeVersion == "mips32el":
				command = "opkg update; opkg install gst-plugins-bad-fragmented"

			else:
				printl("something went wrong finding out the oe-version", self, "W")

			self.executeInstallationCommand(command)

		else:
			# User said 'no'
			self.cancel()

		printl("", self, "C")

	#===============================================================================
	#
	#===============================================================================
	def executeInstallationCommand(self, command):
		printl("", self, "S")

		if not system(command):
			# Successfully installed
			#defaultServer = plexServerConfig.getDefaultServer()
			#self.openSectionlist(defaultServer)
			pass
		else:
			# Fail, try again and report the output...
			pipe = popen(command)
			if pipe is not None:
				data = pipe.read(8192)
				if data is None:
					data = "Unknown Error"
				pipe.close()
				self.session.open(MessageBox, _("Could not install "+ command + ":\n") + data, MessageBox.TYPE_ERROR)
			# Failed to install
			self.cancel()

		printl("", self, "C")

	#===================================================================
	#
	#===================================================================
	def cancel(self):
		printl("", self, "S")

		self.close(False,self.session)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getBoxArch(self):
		printl("", self, "S")

		ARCH = "unknown"

		if (2, 6, 8) > sys.version_info > (2, 6, 6):
			ARCH = "mipsel"

		if (2, 7, 4) > sys.version_info > (2, 7, 0):
			ARCH = "mips32el"

		printl("", self, "C")
		return ARCH