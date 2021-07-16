
; FIXME: Assign all functionality to virtual keys that do not physically exist to ensure no double usage: Coudl use Signals?





; Force script to restart without prompt
#SingleInstance Force
; Set error handler
OnError("LogError")
; Below dynamic variable for writing to logger (I think, check link)
;%cause% := error

LogError(exception) { ;https://www.autohotkey.com/docs/commands/OnError.htm
    FileAppend % "Error on line " exception.Line ": " exception.Message "`n"
        , errorlog.txt
    return true
}

MsgError(exception) { ;https://www.autohotkey.com/docs/commands/OnError.htm
    MsgBox ,,,% "Error on line " exception.Line ": " exception.Message "`n",
    return true
}







`:: ; Performs set-up clicking

;               ACP Planner:
if WinExist("Create Plan for My Observatory") != "0x0" ;Check that Main Window Exists 
;TODO: Not sure this always works as expected
    {
    if WinExist("ACP Planner") ; Closes Dialog and help window
        {
        WinActivate
        WinClose 
        }
    }
else ;In case Application was not started in the beginning
    { 
    LogError("ACP Planner was not started!")
    Run, "C:\Program Files (x86)\ACP Obs Control\Planner\ACPPlanGen.exe" ; Start and Wait until exe is started
    Sleep, 2000 ; Required to be recognized in next statement
    if WinExist("ACP Planner") ; Closes Dialog and help window  
        {
        WinActivate
        WinClose 
        }
    }
Connected = 0
; 10micron Keypad : TODO: AutoConnect Setting in app activated, find a way to recognize if it is actually connected

if WinExist("10micron Keypad") != "0x0"{ ;TODO: Find out how to recognize if it is connected
    }
else 
    {
    LogError("10micron keypad was not started!")
    Run, "C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe" ; Start and Wait until exe is started
    Sleep, 2000 ; Required to be recognized in next statement 
    
    if WinExist("10micron Keypad") {
        }
    else
        {
        LogError("Couldn't open 10micron Keypad")
        }
    }


; Maxim DL  
/*
TODO: Make it start other applications? Or auto start on boot? Prob latter as there is a difference between started and wanted
TODO : Check cloud watcher
Opens several Windows, the main Window has ahk_class
However in case there is an issue with the weather station, we get a window with the same name but ahk_class #32770

Access in order:
MountType
 - Wait!
MaxIm DL Pro 6: Error (if present of course) ahk_class #32770
Camera Control
Obser

*/
if WinExist("MaxIm DL Pro 6") != "0x0" {
    } ;TODO: Figure out what needs to be done  
else ;In case Application was not started in the beginning
    { 
    LogError("MaxIm DL 6 was not started!")
    Run, "C:\Program Files (x86)\Diffraction Limited\MaxIm DL 6\MaxIm_DL" ; Start and Wait until exe is started
    Sleep, 2000 ; Required to be recognized in next statement 
    
    if WinExist("MaxIm DL Pro 6") {
        }
    else
        {
        LogError("Couldn't open MaxIm DL Pro 6")
        }
    }

; DomeScope

if WinExist(" | ScopeDome Arduino Dome v10 f13") != "0x0" {
    } ;TODO: Figure out what needs to be done  
else  ;In case Application was not started in the beginning
    { 
    LogError("ScopeDome was not started!")
    Run, "C:\ScopeDome\Driver_LS\ASCOM.ScopeDomeUSBDome.exe" ; Start and Wait until exe is started
    Sleep, 2000 ; Required to be recognized in next statement
    }
    if WinExist(" | ScopeDome Arduino Dome v10 f13") {
        }
    else
    {
    LogError("Couldn't open MaxIm DL Pro 6")
    }

return



; https://www.online-tech-tips.com/computer-tips/prevent-shutdown-of-windows/



=:: ; Restart autohotkey script
Run, "C:\Users\gamep\ldst-control-systems\autohotkey_triouts.ahk"
return