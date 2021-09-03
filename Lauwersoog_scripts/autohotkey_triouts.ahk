
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

;               ACP Planner: Change the program
if WinExist("ACP Observatory Control Software") != "0x0" ;Check that Main Window Exists 
;TODO: Not sure this always works as expected
    {
    if WinExist("ACP Planner") ; Closes Dialog and help window #FIXME: This probably is not needed
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
; 10micron Keypad

if WinExist("10micron Keypad") != "0x0"{ 
    Run, "C:\Users\blaau\OneDrive\Desktop\WakeMeOnLan.exe /wakeup 192.168.0.111"
    }
else 
    {
    LogError("10micron keypad was not started!")
    Run, "C:\Program Files (x86)\10micron\VirtKP2\virtkeypad.exe" ; Start and Wait until exe is started
    Sleep, 2000 ; Required to be recognized in next statement 
    
    if WinExist("10micron Keypad") {
        Run, "C:\Users\blaau\OneDrive\Desktop\WakeMeOnLan.exe /wakeup 192.168.0.111"
        }
    else
        {
        LogError("Couldn't open 10micron Keypad")
        }
    }


    ; Maxim DL  

if WinExist("MaxIm DL Pro 6") != "0x0" {
    } 
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
    } 
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
    LogError("Couldn't open ScopeDome Ardurino Dome")
    }

return


-::
if WinExist("ACP Observatory Control Software") != "0x0" ;Check that Main Window Exists 
    {
    WinActivate ; FIXME: CHeck the button names with the window spy
    ControlClick, Telescope
    ControlClick, Connect
    ControlClick, Camera
    ControlClick, Connect ;The next steps are to load the script
    ControlClick, Dropdown menu and select ACPSchedulertextfile
    ControlSetText, Control, "C:\LDST\Schedule_flat.txt" ;#TODO: Control is ClassNN
    ; Could simply create startup script and restart acp prior to observing so it always loads the script in the directory
    ControlClick start

    if WinExist("ACP Planner") != "0x0" ; test for message window in case plan has been edited in window Shouldnt happeb
        {
            Click Yes
        }
    }

















; https://www.online-tech-tips.com/computer-tips/prevent-shutdown-of-windows/


=:: ; Restart autohotkey script
Run, "C:\Users\gamep\ldst-control-systems\autohotkey_triouts.ahk"
return