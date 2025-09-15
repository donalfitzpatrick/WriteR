# module for file menu events, created July 2023

from os.path import join
from time import asctime

import wx


def OnOpen(self, event):
    if askUserForFilename(self, style=wx.FD_OPEN, **defaultFileDialogOptions(self)):
        self.fileOpen(self.dirname, self.filename)


def OnClose(self, event):
    self.settings["filename"] = self.filename
    self.settings["lastdir"] = self.dirname
    if event.CanVeto() and self.editor.IsModified():
        hold = wx.MessageBox(
            "Would you like to save your work?",
            "Save before exit?",
            wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT,
        )
        if hold == wx.YES:
            self.OnSave(event)
            self.Destroy()
        elif hold == wx.NO:
            self.Destroy()
        else:
            event.Veto()
    else:
        self.Destroy()


def fatalError(self, message):
    dialog = wx.MessageDialog(self, message, "Fatal Error", wx.OK)
    dialog.ShowModal()
    dialog.Destroy()
    self.OnExit()


def fileOpen(self, dirname, filename):
    path = join(dirname.strip(), filename)
    try:
        with open(path, "r", encoding="utf-8") as textfile:
            content = textfile.read()
    except UnicodeDecodeError:
        # Fallback if UTF-8 fails
        with open(path, "r", encoding="latin-1") as textfile:
            content = textfile.read()
    except FileNotFoundError:
        self.fatalError(f"File not found: '{path}'")
        self.OnExit()
        return
    except PermissionError:
        self.fatalError(f"Permission denied: '{path}'")
        self.OnExit()
        return
    except OSError as error:
        # Catches other OS-related errors (e.g. IsADirectoryError, I/O error)
        self.fatalError(f"OS error with file '{path}': {error}")
        self.OnExit()
        return
    except Exception as error:  # pylint: disable=W0718
        # Last resort: shouldn't happen often, but prevents a crash
        self.fatalError(f"Unexpected error with file '{path}': {error}")
        self.OnExit()
        return

    self.editor.SetValue(content)


def OnNewFile(self, event):
    self.olddirname = self.dirname
    self.dirname = ".\\templates"
    self.OnOpen(event)
    self.dirname = self.olddirname
    if self.filename == "Blank.Rmd":
        self.editor.WriteText("% file created on " + asctime() + "\n\n")
    self.OnSaveAs(event)


def OnSaveAs(self, event):
    if askUserForFilename(
        self,
        defaultFile=self.filename,
        style=wx.FD_SAVE,
        **defaultFileDialogOptions(self),
    ):
        self.OnSave(event)


def OnSave(self, event):
    try:
        with open(join(self.dirname, self.filename), "w", encoding="utf-8") as textfile:
            textfile.write(self.editor.GetValue())
    except Exception as error:
        self.fatalError(f"An error occurred while saving the file: {error}")


def OnExit(self):
    if self.mgr:
        self.mgr.UnInit()
    self.Close()  # Close the main window.


def OnSafeExit(self, event):
    self.OnSave(event)
    self.OnExit()


def defaultFileDialogOptions(self):
    return {
        "message": "Choose a file",
        "defaultDir": self.dirname,
        "wildcard": "*.*",
    }


def askUserForFilename(self, **dialogOptions):
    dialog = wx.FileDialog(self, **dialogOptions)
    if dialog.ShowModal() == wx.ID_OK:
        userProvidedFilename = True
        self.filename = dialog.GetFilename()
        self.dirname = dialog.GetDirectory()
        self.SetTitle()  # Update the window title with the new filename
    else:
        userProvidedFilename = False
    dialog.Destroy()
    return userProvidedFilename
