# -*- coding: latin-1 -*-
"""_vocola_main.py - Natlink support for Vocola

Contains:
   - "Built-in" voice commands
   - Autoloading of changed command files


Copyright (c) 2002-2012 by Rick Mohr.

Portions Copyright (c) 2012-2015 by Hewlett-Packard Development Company, L.P.

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#pylint:disable=W0614, W0613, C0116, C0321, W0603, R0201, W0401, C0115, C0412, W0201
#pylint:disable=E1101
import sys
import traceback
import os               # access to file information
import os.path          # to parse filenames
# import time             # print time in messages
import stat             # from   stat import *    # file statistics
import shutil
import subprocess
import re
import natlink
from natlink import natlinkutils
import VocolaUtils
import natlinkvocolastartup  # was natlinkstartup in natlinkmain...
thisDir = os.path.split(__file__)[0]

##########################################################################
#                                                                        #
# Configuration                                                           #
#                                                                        #
##########################################################################

try:
    from natlink import natlinkstatus
    Quintijn_installer = True
    status             = natlinkstatus.NatlinkStatus()
    # print('status: %s'% status)
    VocolaEnabled      = bool(status.getVocolaUserDirectory())
    print(f'VocolaEnabled: {VocolaEnabled}')
    if VocolaEnabled:
        VocolaGrammarsDirectory = status.getVocolaGrammarsDirectory()
        VocolaUserDirectory = status.getVocolaUserDirectory()
        VocolaDirectory = status.getVocolaDirectory()
    else:
        VocolaGrammarsDirectory = ""
        VocolaUserDirectory = ""
        VocolaDirectory = ""
        
    # print('VocolaEnabled: %s'% VocolaEnabled)
    language           = status.language
    if language != 'enx':
        print(f'    language: "{language}"')
    ## perform init actions:
    natlinkvocolastartup.start()
except ImportError:
    Quintijn_installer = False
    VocolaEnabled      = True
    language           = 'enx'
    traceback.print_exc()

if thisDir and os.path.isdir(thisDir):
    if VocolaEnabled:
        if VocolaDirectory.lower() != thisDir.lower():
            print(f"thisDir of _vocola_main: {thisDir} not equal to VocolaDirectory from natlinkstatus: {VocolaDirectory}")
else:
    raise OSError("no valid directory found for _vocola_main.py: {thisDir}")
    
# get location of MacroSystem folder:
VocolaGrammarsDirectory = status.getVocolaGrammarsDirectory()

VocolaFolder     = thisDir
ExecFolder       = os.path.normpath(os.path.join(thisDir, 'exec'))
OriginalExtensionsFolder = os.path.normpath(os.path.join(thisDir, 'extensions'))
ExtensionsFolder = os.path.normpath(os.path.join(VocolaUserDirectory, 'extensions'))

def checkExtensionsFolderContents(original, actual):
    """create the actual extensions folder and check the contents
    
    the actual extensionsfolder  should be a subdirectory of the VocolaUserDirectory
    and is created if not existing yet.
    
    All the python files in the original folder are copied to the thisactual folder, if needed.
    
    """
    if not os.path.isdir(actual):
        os.mkdir(actual)
    if not os.path.isdir(actual):
        raise OSError(f'Vocola2: the "actual" extensions folder {actual} could not be created')
    filesToCopyIfNewer = [f for f in os.listdir(original) if f.endswith('.py')]
    filesToCopyIfNewer.append('README.txt')
    
    for name in filesToCopyIfNewer:
        orgPy = os.path.join(original, name)
        targetPy = os.path.join(actual, name)
        orgDate = vocolaGetModTime(orgPy)
        targetDate = vocolaGetModTime(targetPy)
        if orgDate > targetDate:
            shutil.copyfile(orgPy, targetPy)

# Returns the modification time of a file or 0 if the file does not exist:
def vocolaGetModTime(file):
    try: return os.stat(file)[stat.ST_MTIME]
    except OSError: return 0        # file not found

                       
checkExtensionsFolderContents(OriginalExtensionsFolder, ExtensionsFolder)

if VocolaEnabled:
    print('_vocola_main, Vocola is Enabled, check sys.path for ExecFolder and ExtensionsFolder')
    for _f in ExecFolder, ExtensionsFolder:
        if _f not in sys.path:
            print(f'_vocola_main, add to sys.path: {_f}')
            sys.path.append(_f)
else:
    print('_vocola_main, Vocola is NOT Enabled')
    

def get_command_folder():
    global commandFolder
    commandFolder = get_top_command_folder()  ## (is global variable)
    if commandFolder: 
        uDir = os.path.join(commandFolder, language)
        if os.path.isdir(uDir):
            commandFolder = uDir
    return commandFolder

def get_top_command_folder():
    return VocolaUserDirectory
    # configured = None
    # try:
    #     from natlinkcore import natlinkstatus
    #     # Quintijn's's installer:
    #     configured = status.NatlinkStatus().getVocolaUserDirectory()
    #     # print('Vocola configured: %s'% configured)
    # except ImportError:
    #     try:
    #         import RegistryDict
    #         import win32con
    #         # Scott's installer:
    #         r = RegistryDict.RegistryDict(win32con.HKEY_CURRENT_USER,r"Software\Natlink")
    #         if r:
    #             configured = r["VocolaUserDirectory"]
    #     except ImportError:
    #         pass
    # if os.path.isdir(configured):
    #     return configured
    # 
    # systemCommandFolder = os.path.join(VocolaFolder, 'Commands')
    # if os.path.isdir(systemCommandFolder):
    #     return systemCommandFolder
    # 
    # return None

commandFolder = get_command_folder()
if VocolaEnabled and not commandFolder:
    print("Warning: no Vocola command folder found!", file=sys.stderr)

VocolaUtils.Language = language



###########################################################################
#                                                                         #
# The built-in commands                                                   #
#                                                                         #
###########################################################################

class ThisGrammar(natlinkutils.GrammarBase):

    gramSpec = """
        <NatLinkWindow>     exported = [Show] (Natlink|Vocola) Window;
        <edit>              exported = Edit [Voice] Commands;
        <editGlobal>        exported = Edit Global [Voice] Commands;
        <editMachine>       exported = Edit Machine [Voice] Commands;
        <editGlobalMachine> exported = Edit Global Machine [Voice] Commands;
        <loadAll>           exported = Load All [Voice] Commands;
        <loadCurrent>       exported = Load [Voice] Commands;
        <loadGlobal>        exported = Load Global [Voice] Commands;
        <loadExtensions>    exported = Load [Voice] Extensions;
        <discardOld>        exported = Discard Old [Voice] Commands;
    """

    if language == 'nld':
        gramSpec = """
<NatLinkWindow>     exported = Toon (Natlink|Vocola) venster;
<edit>              exported = (Eddit|Bewerk|Sjoo|Toon) [stem|vojs] (Commandoos|Commands);
<editGlobal>        exported = (Eddit|Bewerk|Sjoo|Toon) (Global|globale) [stem|vojs] (Commandoos|Commands);
<editMachine>       exported = (Eddit|Bewerk|Sjoo|Toon) Machine [stem|vojs] (Commandoos|Commands);
<editGlobalMachine> exported = (Eddit|Bewerk|Sjoo|Toon) (Global|globale) Machine [stem|vojs] (Commandoos|Commands);
<loadAll>           exported = (Laad|Lood) alle [stem|vojs] (Commandoos|Commands);
<loadCurrent>       exported = (Laad|Lood) [stem|vojs] (Commandoos|Commands);
<loadGlobal>        exported = (Laad|Lood) globale [stem|vojs] (Commandoos|Commands);
<loadExtensions>    exported = Laad [stem] extensies;
<discardOld>        exported = (Discard|Verwijder) (oude|oold) [stem|vojs] (Commandoos|Commands);
    """
    elif language == 'fra':
        gramSpec = """
<NatLinkWindow>     exported = [Afficher] Fenetre (Natlink|Vocola);
<edit>              exported = Editer Commandes [Vocales];
<editGlobal>        exported = Editer Commandes [Vocales] Globales;
<editMachine>       exported = Editer Commandes [Vocales] Machine;
<editGlobalMachine> exported = Editer Commandes [Vocales] Globales Machine;
<loadAll>           exported = Charger Toutes Les Commandes [Vocales];
<loadCurrent>       exported = Charger Commandes [Vocales];
<loadGlobal>        exported = Charger Commandes [Vocales] Globales;
<loadExtensions>    exported = Charger Extensions [Vocales];
<discardOld>        exported = Effacer Commandes [Vocales] Precedentes;
    """
    elif language == 'deu':
        gramSpec = """
<NatLinkWindow>     exported = [Zeige] (Natlink|Vocola) Fenster;
<edit>              exported = Bearbeite [Sprach] Befehle;
<editGlobal>        exported = Bearbeite globale [Sprach] Befehle;
<editMachine>       exported = Bearbeite Maschinen [Sprach] Befehle;
<editGlobalMachine> exported = Bearbeite globale Maschinen [Sprach] Befehle;
<loadAll>           exported = Lade alle [Sprach] Befehle;
<loadCurrent>       exported = Lade [Sprach] Befehle;
<loadGlobal>        exported = Lade globale [Sprach] Befehle;
<loadExtensions>    exported = Lade [Sprach] Extensions;
<discardOld>        exported = Verwerfe alte [Sprach] Befehle;
    """
    elif language == 'ita':
        gramSpec = """
<NatLinkWindow>     exported = [Mostra] Finestra Di (Natlink|Vocola);
<edit>              exported = Modifica Comandi [Vocali];
<editGlobal>        exported = Modifica Comandi [Vocali] Globali;
<editMachine>       exported = Modifica Comandi [Vocali] [del] Computer;
<editGlobalMachine> exported = Modifica Comandi [Vocali] Globali [del] Computer;
<loadAll>           exported = Carica Tutti I Comandi [Vocali];
<loadCurrent>       exported = Carica I Comandi [Vocali];
<loadGlobal>        exported = Carica Comandi [Vocali] Gliobali;
<loadExtensions>    exported = Carica Estensioni [Vocali];
<discardOld>        exported = Annulla Vecchi Comandi [Vocali];
    """
    elif language == 'esp':
        gramSpec = """
<NatLinkWindow>     exported = [Mostrar] Ventana de (Natlink|Vocola) ;
<edit>              exported = (Modificar|Editar) Comandos [de voz];
<editGlobal>        exported = (Modificar|Editar) Comandos [de voz] Globales ;
<editMachine>       exported = (Modificar|Editar) Comandos [de voz] de (este ordenador|la Computadora);
<editGlobalMachine> exported = (Modificar|Editar) Comandos [de voz] Globales de (este ordenador|la Computadora);
<loadAll>           exported = (Recargar|Cargar) Todos Los Comandos [de voz];
<loadCurrent>       exported = (Recargar|Cargar) Comandos [de voz];
<loadGlobal>        exported = (Recargar|Cargar) Comandos [de voz] Globales;
<loadExtensions>    exported = (Recargar|Cargar) Extensiones [de voz];
<discardOld>        exported = Descartar Comandos [de voz] Viejos;
    """
    elif language != 'enx':
        print("""\n\n
Vocola Warning: no language "%s" translations for the built-in Vocola
commands (e.g., commands to load voice commands) are currently
available; consider helping translate them -- inquire on
https://www.knowbrainer.com/forums/forum/categories.cfm?catid=25.  For
now the English versions, like "Edit Commands" and "Edit Global
Commands" are activated.
""" % language, file=sys.stderr)

    def initialize(self):
        if 'COMPUTERNAME' in os.environ:
            self.machine = os.environ['COMPUTERNAME'].lower()
        else: self.machine = 'local'

        self.load_extensions()
        self.loadAllFiles(False)

        self.load(self.gramSpec)
        self.activateAll()

    def gotBegin(self, moduleInfo):
        self.currentModule = moduleInfo
        # delay enabling until now to avoid Natlink clobbering our callback:
        # enable_callback()
        # here try to catch changed .vcl files and rewrite the corresponding python grammar file
        # now, there is a slowdown of one utterance, at it seems.
        # the tuning of lood_on_got_begin property in the loader class,
        # to be controlled via natlinkstatus.set_load_on_begin_utterance should be improved,
        # or simply set_load_on_begin_utterance to True, whenever a vocola command file is opened.
        # then check at each utterance!
        vocolaBeginCallback(moduleInfo)


    # Get app name by stripping folder and extension from currentModule name
    def getCurrentApplicationName(self):
        """get the current application name of the foreground window
        
        The same named function in natlinkmain returns the lowercase executable of the running
        program, but if "ApplicationFrameHost" is running (Calc, Photos), that name is returned.
        """
        #TODO: this was to prevent ApplicationHost, and redirect to calc, photo etc.
        # appName = natlinkmain.getCurrentApplicationName(self.currentModule)
        return self.currentModule


### Miscellaneous commands

    # "Show Natlink Window" -- print to output window so it appears
    def gotResults_NatLinkWindow(self, words, fullResults):
        print("This is the Natlink/Vocola output window")

    # "Load Extensions" -- scan for new/changed extensions:
    def gotResults_loadExtensions(self, words, fullResults):
        self.load_extensions(True)
        for module in list(sys.modules.keys()):
            if module.startswith("vocola_ext_"):
                del sys.modules[module]

    def load_extensions(self, verbose=False):
        #pylint:disable=C0415, E0401  # check!!!
        import scan_extensions
        arguments = ["scan_extensions", ExtensionsFolder]
        if verbose:
            arguments.insert(1, "-v")
        scan_extensions.main(arguments)


### Loading Vocola Commands

    # "Load All Commands" -- translate all Vocola files
    def gotResults_loadAll(self, words, fullResults):
        self.loadAllFiles(True)

    # "Load Commands" -- translate Vocola files for current application
    def gotResults_loadCurrent(self, words, fullResults):
        self.loadSpecificFiles(self.getCurrentApplicationName())

    # "Load Global Commands" -- translate global Vocola files
    def gotResults_loadGlobal(self, words, fullResults):
        self.loadSpecificFiles('')

    # "Discard Old [Voice] Commands" -- purge output then translate all files
    def gotResults_discardOld(self, words, fullResults):
        purgeOutput()
        self.loadAllFiles(True)

    # Load all command files
    def loadAllFiles(self, force):
        if commandFolder:
            # print('loadAllFiles: %s'% commandFolder)
            compile_Vocola(commandFolder, force)

    # Load command files for specific application
    def loadSpecificFiles(self, module):
        special = re.compile(r'([][()^$.+*?{\\])')
        pattern = "^" + special.sub(r'\\\1', module)
        pattern += "(_[^@]*)?(@" + special.sub(r'\\\1', self.machine)
        pattern += r")?\.vcl$"
        p = re.compile(pattern, re.IGNORECASE)

        targets = []
        if commandFolder:
            targets += [os.path.join(commandFolder,f)
                        for f in os.listdir(commandFolder) if p.search(f)]
        if len(targets) > 0:
            for target in targets:
                self.loadFile(target)
        else:
            print(file=sys.stderr)
            if module == "":
                print("Found no Vocola global command files [for machine '" + \
                    self.machine + "']", file=sys.stderr)
            else:
                print("Found no Vocola command files for application '" + module + "' [for machine '" + self.machine + "']", file=sys.stderr)

    # Load a specific command file, returning false if not present
    def loadFile(self, file):
        try:
            print(f"try to compile Vocola file: {file}")
            os.stat(file)
            compile_Vocola(file, False)
            return True
        except OSError:
            return False   # file not found


### Editing Vocola Command Files

    # "Edit Commands" -- open command file for current application
    def gotResults_edit(self, words, fullResults):
        # set set_load_on_begin_utterance to True
        status.set_load_on_begin_utterance = True
        app = self.getCurrentApplicationName()
        file = app + '.vcl'
        comment = 'Voice commands for ' + app
        self.openCommandFile(file, comment)

    # "Edit Machine Commands" -- open command file for current app & machine
    def gotResults_editMachine(self, words, fullResults):
        # set set_load_on_begin_utterance to True
        status.set_load_on_begin_utterance = True
        app = self.getCurrentApplicationName()
        file = app + '@' + self.machine + '.vcl'
        comment = 'Voice commands for ' + app + ' on ' + self.machine
        self.openCommandFile(file, comment)

    # "Edit Global Commands" -- open global command file
    def gotResults_editGlobal(self, words, fullResults):
        # set set_load_on_begin_utterance to True
        status.set_load_on_begin_utterance = True
        file = '_vocola.vcl'
        comment = 'Global voice commands'
        self.openCommandFile(file, comment)

    # "Edit Global Machine Commands" -- open global command file for machine
    def gotResults_editGlobalMachine(self, words, fullResults):
        file = '_vocola@' + self.machine + '.vcl'
        comment = 'Global voice commands on ' + self.machine
        self.openCommandFile(file, comment)


    def FindExistingCommandFile(self, file):
        if commandFolder:
            f = commandFolder + '\\' + file
            if os.path.isfile(f): return f

        return ""

    # Open a Vocola command file (using the application associated with ".vcl")
    def openCommandFile(self, file, comment):
        if not commandFolder:
            print("Error: Unable to create command file " + \
                "because no Vocola command folder found.", file=sys.stderr)
            return

        path = self.FindExistingCommandFile(file)
        if not path:
            path = commandFolder + '\\' + file

            new = open(path, 'w')
            new.write('# ' + comment + '\n\n')
            new.close()

        #
        # Natlink/DNS bug causes os.startfile or wpi32api.ShellExecute
        # to crash DNS if allResults is on in *any* grammer (e.g., Unimacro)
        #
        # Accordingly, use AppBringUp instead:
        #

        #try:
        #    os.startfile(path)
        #except WindowsError, e:
        #    print
        #    print "Unable to open voice command file with associated editor: " + str(e)
        #    print "Trying to open it with notepad instead."
        #    prog = os.path.join(os.getenv('WINDIR'), 'notepad.exe')
        #    os.spawnv(os.P_NOWAIT, prog, [prog, path])
        natlink.execScript("AppBringUp \"" + path + "\", \"" + path + "\"")



###########################################################################
#                                                                         #
# Compiling Vocola files                                                  #
#                                                                         #
###########################################################################

may_have_compiled = False  # has the compiler been called?
compiler_error     = False  # has a compiler error occurred?
may_have_compiled = False  #

# Run Vocola compiler, converting command files from "inputFileOrFolder"
# and writing output to Natlink/MacroSystem
def compile_Vocola(inputFileOrFolder, force):
    global may_have_compiled, compiler_error

    may_have_compiled = True

    executable = sys.prefix + r'\python.exe'
    arguments  = [VocolaFolder + r'\exec\vcl2py.py']

    arguments += ['-extensions', ExtensionsFolder + r'\extensions.csv']
    if language == "enx":
        arguments += ['-numbers',
                      'zero,one,two,three,four,five,six,seven,eight,nine']

    arguments += ["-suffix", "_vcl"]
    if force: arguments += ["-f"]
    arguments += [inputFileOrFolder, VocolaGrammarsDirectory]
    # print(f"_vocola_main calls vcl2py.py, grammars go to folder: {VocolaGrammarsDirecory}")
    # print(f"calling {arguments}")v
    hidden_call(executable, arguments)

    logName = commandFolder + r'\vcl2py_log.txt'
    if os.path.isfile(logName):
        try:
            log = open(logName, 'r')
            compiler_error = True
            print(log.read(), file=sys.stderr)
            log.close()
            os.remove(logName)
        except OSError:  # no log file means no Vocola errors
            pass

# Unload all commands, including those of files no longer existing
def purgeOutput():
    # print(f'purge output, directory: {VocolaGrammarsDirecory} {len(os.listdir(VocolaGrammarsDirecory))} files')
    # pattern = re.compile(r"_vcl\d*\.pyc?$")
    nFiles = 0
    for f in os.listdir(VocolaGrammarsDirectory):
        if f.endswith('.py'):
            nFiles += 1
            os.remove(os.path.join(VocolaGrammarsDirectory, f))
    # print('purged output, directory: {VocolaGrammarsDirecory}, {nFiles} python files')collapse
    # print('-------------------')

#
# Run program with path executable and arguments arguments.  Waits for
# the program to finish.  Runs the program in a hidden window.
#
def hidden_call(executable, arguments):
    args = [executable] + arguments
    try:
        si             = subprocess.STARTUPINFO()
        # Location of below constants seems to vary from Python
        # version to version so hardcode them:
        si.dwFlags     = 1  # subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # subprocess.SW_HIDE
        return subprocess.call(args, startupinfo=si)
    except ImportError:
        pid = os.spawnv(os.P_NOWAIT, executable, args)
        pid, exit_code = os.waitpid(pid, 0)
        exit_code = exit_code >> 8
        return exit_code


lastVocolaFileTime    = 0
lastCommandFolderTime = 0

def compile_changed():
    global lastVocolaFileTime, lastCommandFolderTime
    global compiler_error

    current = getLastVocolaFileModTime()
    if current > lastVocolaFileTime:
        compiler_error = False
        thisGrammar.loadAllFiles(False)
        if not compiler_error:
            lastVocolaFileTime = current

    source_changed = False
    if commandFolder:
        if vocolaGetModTime(commandFolder) > lastCommandFolderTime:
            lastCommandFolderTime = vocolaGetModTime(commandFolder)
            source_changed = True
    if source_changed:
        deleteOrphanFiles()

# Returns the newest modified time of any Vocola command folder file or
# 0 if none:
def getLastVocolaFileModTime():
    last = 0
    if commandFolder:
        last = max([last] +
                   [vocolaGetModTime(os.path.join(commandFolder,f))
                    for f in os.listdir(commandFolder)])
    return last

def deleteOrphanFiles():
    print("checking for orphans...")
    for f in os.listdir(VocolaGrammarsDirectory):
        if not re.search("_vcl.pyc?$", f): continue

        s = getSourceFilename(f)
        if s:
            if vocolaGetModTime(s)>0: continue

        f = os.path.join(VocolaGrammarsDirectory, f)
        print("Deleting: " + f)
        os.remove(f)

def getSourceFilename(output_filename):
    m = re.match("^(.*)_vcl.pyc?$", output_filename)
    if not m: return None                    # Not a Vocola file
    name = m.group(1)
    if not commandFolder: return None

    marker = "e_s_c_a_p_e_d__"
    m = re.match("^(.*)" + marker + "(.*)$", name)  # rightmost marker!
    if m:
        name = m.group(1)
        tail = m.group(2)
        tail = re.sub("__a_t__", "@", tail)
        tail = re.sub("___", "_", tail)
        name += tail

    name = re.sub("_@", "@", name)
    return commandFolder + "\\" + name + ".vcl"


lastNatLinkModTime = 0

# Check for changes to our output .py files and report status relative
# to last time this routine was called; return code means:
#   0: no changes
#   1: 1 or more existing .py files were modified, but no new .py files created
#   2: one or more new .py files may have been created, plus maybe existing changed
def output_changes():
    #pylint:disable=W0603
    global lastNatLinkModTime, may_have_compiled

    old_may_have_compiled = may_have_compiled
    may_have_compiled = False

    current = vocolaGetModTime(VocolaGrammarsDirectory)
    if current > lastNatLinkModTime:
        lastNatLinkModTime = current
        return 2

    if old_may_have_compiled:
        return 1
    return 0


# When speech is heard this function will be called before any others.
#
# Must return result of output_changes() so we can tell Natlink when
# files need to be loaded.
def utterance_start_callback(moduleInfo):
    compile_changed()
    return output_changes()



###########################################################################
#                                                                         #
# Callback handling                                                       #
#                                                                         #
###########################################################################

#
# With Quintijn's installer as of February 4, 2008:
#
#   _vocola_main is loaded before any other Natlink modules
#   vocolaBeginCallback is called directly by natlinkmain before any
#     other grammer's gotBegin method
#   natlinkmain now guarantees we are not called with CallbackDepth>1
#   we return the result of output_changes() directly rather than
#     massaging Natlink to deal with new .py files
#

def vocolaBeginCallback(moduleInfo):
    changes = 0
    if Quintijn_installer:    ## ??? or getCallbackDepth()<2:
        changes = utterance_start_callback(moduleInfo)
        if changes:
            # set loader to 1 time trigger_load at beginCallback:
            # slow down of one utterance. Maybe set this to True at edit command file,
            # or make it a separate command, to set this property to True or False...
            # print('_vocola_main, vocolaBeginCallback, set load_on_begin_utterance to 1')
            # status.set_load_on_begin_utterance(1)
            pass 

###########################################################################
#                                                                         #
# Startup/shutdown                                                        #
#                                                                         #
###########################################################################

thisGrammar = None

# remove previous Vocola/Python compilation output as it may be out of
# date (e.g., new compiler, source file deleted, partially written due
# to crash, new machine name, etc.):
purgeOutput()

if not VocolaEnabled:
    print("Vocola not active")
else:
    print("Vocola version 2.8.6 starting...")
    thisGrammar = ThisGrammar()
    thisGrammar.initialize()


def unload():
    global thisGrammar
    # disable_callback()
    if thisGrammar: thisGrammar.unload()
    thisGrammar = None
   