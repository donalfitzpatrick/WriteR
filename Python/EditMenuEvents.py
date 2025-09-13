# 2022.11.29 This file needs careful checking to ensure it remains totally independent of implementation
#    so that we can be sure it remains useful for WriteR and WriteQuarto

import re
import sys

try:
    import winsound
except ImportError:
    print("Winsound module not found\n")

import wx
import wx.stc  # needed for word count and go to line

import RMarkdownEvents
from BackEnd import TellUser

beep = "winsound" in sys.modules


def OnGoToLine(self, event):
    _, y = self.editor.PositionToXY(self.editor.GetInsertionPoint())
    maxLine = self.editor.GetNumberOfLines()
    dialog = wx.NumberEntryDialog(
        self,
        caption="GoToLine",
        message="Go to line",
        prompt="Line",
        value=y,
        min=0,
        max=maxLine,
    )
    if dialog.ShowModal() == wx.ID_OK:
        line = dialog.GetValue()
        line = max(0, min(self.editor.GetNumberOfLines(), line))
        self.editor.SetInsertionPoint(self.editor.XYToPosition(0, dialog.GetValue()))
    dialog.Destroy()


def OnCut(self, event):
    self.editor.Cut()


def OnCopy(self, event):
    self.editor.Copy()


def OnPaste(self, event):
    self.editor.Paste()


def OnDelete(self, event):
    frm, to = self.editor.GetSelection()
    self.editor.Remove(frm, to)


def OnSelectAll(self, event):
    self.editor.SelectAll()


def OnSettings(self, event):  # not properly implemented
    wx.MessageBox(
        "You wanted to see the settings, but this is not properly implemented yet"
    )


def OnWordCount(self, event):
    text = self.editor.GetValue()
    word_count = len(text.split())
    _, _, y = self.editor.PositionToXY(self.editor.GetInsertionPoint())
    line_count = self.editor.GetNumberOfLines()
    markdownState = RMarkdownEvents.CurrentMarkdown(self)
    TellUser(
        self,
        text=f"Line {y}/{line_count}. WordCount {word_count}. State {markdownState}",
    )


def OnShowFind(self, event):
    data = wx.FindReplaceData()
    data.SetFlags(wx.FR_DOWN)
    dlg = wx.FindReplaceDialog(self, data, "Find")
    dlg.data = data  # save a reference to it...
    dlg.Show(True)


def OnSetMark(self, event):
    self.mark = self.editor.GetInsertionPoint()
    if beep:
        winsound.Beep(1000, 250)


def F3Next(self, event):
    FindFrom(self, self.priorMatchCol, self.priorMatchRow, False)


def ShiftF3Previous(self, event):
    FindFrom(self, self.priorMatchCol, self.priorMatchRow, True)


def OnFind(self, event):
    et = event.GetEventType()
    self.regex = re.compile(ComputeFindString(self, event), ComputeReFlags(self, event))
    self.forward = event.GetFlags() & wx.FR_DOWN
    if et == wx.wxEVT_COMMAND_FIND:
        _, col, row = self.editor.PositionToXY(self.editor.GetInsertionPoint())
        FindFrom(self, col, row, False)
    elif et == wx.wxEVT_COMMAND_FIND_NEXT:
        FindFrom(self, self.priorMatchCol, self.priorMatchRow, False)
    elif et == wx.wxEVT_COMMAND_FIND_REPLACE:
        ReplaceNext(self, event)
    elif et == wx.wxEVT_COMMAND_FIND_REPLACE_ALL:
        ReplaceAll(self, event)
    else:
        self.console.write(f"unexpected eventType {et} -- {event}\n")


def ComputeFindString(self, event):
    s = event.GetFindString()
    if not s:
        return ""  # avoid None
    if event.GetFlags() & wx.FR_WHOLEWORD:
        return r"\b" + re.escape(s) + r"\b"
    return re.escape(s)


def OnFindClose(self, event):
    event.GetDialog().Destroy()


def OnShowFindReplace(self, event):
    data = wx.FindReplaceData()
    data.SetFlags(wx.FR_DOWN)
    dlg = wx.FindReplaceDialog(self, data, "Find & Replace", wx.FR_REPLACEDIALOG)
    dlg.data = data  # save a reference to it...
    dlg.Show(True)


def OnSelectToMark(self, event):
    insertionPoint = self.editor.GetInsertionPoint()
    if self.mark < insertionPoint:
        self.editor.SetSelection(self.mark, insertionPoint)
        if beep:
            winsound.Beep(750, 250)
    elif self.mark > insertionPoint:
        self.editor.SetSelection(insertionPoint, self.mark)
        if beep:
            winsound.Beep(1500, 250)


def ComputeReFlags(self, event):
    if event.GetFlags() & wx.FR_MATCHCASE:
        return 0
    return re.IGNORECASE


def ComputeReplacementString(self, event):
    return event.GetReplaceString()


def MoveTo(self, row, col):
    self.priorMatchRow = row
    self.priorMatchCol = col
    message = f"Line {row} Col {col}"
    TellUser(self, message)
    position = self.editor.XYToPosition(col, row)
    self.editor.SetInsertionPoint(position)
    self.editor.ShowPosition(position)
    if beep:
        winsound.Beep(1000, 250)


def FindFrom(self, currentColumn, currentRow, reverseDirection):
    # Special logic for checking just part of current line
    currentLine = self.editor.GetLineText(currentRow)
    searchForward = self.forward != reverseDirection
    if searchForward:
        matchObject = self.regex.search(currentLine[currentColumn + 1 :])
        if matchObject:
            MoveTo(self, currentRow, currentColumn + 1 + matchObject.start())
            return
    else:
        matchObject = self.regex.search(currentLine[:currentColumn])
        if matchObject:
            for matchObject in self.regex.finditer(currentLine[:currentColumn]):
                pass
            MoveTo(self, currentRow, matchObject.start())
            return
    # General case for checking whole lines
    if searchForward:
        lineRange = range(currentRow + 1, self.editor.GetNumberOfLines())
    else:
        lineRange = reversed(range(0, currentRow))
    for i in lineRange:
        line = self.editor.GetLineText(i)
        matchObject = self.regex.search(line)
        if matchObject:
            if not searchForward:
                for matchObject in self.regex.finditer(line):
                    pass
            MoveTo(self, i, matchObject.start())
            return
    if beep:
        winsound.Beep(500, 500)


def ReplaceNext(self, event):
    return


def ReplaceAll(self, event):
    findString = ComputeFindString(self, event)
    reFlags = ComputeReFlags(self, event)
    replaceString = ComputeReplacementString(self, event)
    oldText = self.editor.GetValue()
    newText = re.sub(findString, replaceString, oldText, flags=reFlags)
    insertionPoint = self.editor.GetInsertionPoint()
    self.editor.SetValue(newText)
    self.editor.SetInsertionPoint(insertionPoint)


# the following are not implemented yet and might be moved to different module


def duplicateline(self, e):
    self.editor.SelectionDuplicate()


def lineup(self, e):
    self.editor.MoveSelectedLinesUp()


def linedown(self, e):
    self.editor.MoveSelectedLinesDown()


def unindent(self, e):
    self.editor.BackTab()
