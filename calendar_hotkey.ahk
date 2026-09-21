#Requires AutoHotkey v2.0
#SingleInstance Force

; Ctrl + Alt + G
^!g::
{
    static running := false
    if running
    {
        TrayTip("処理中です。完了してから再実行してください。", "Google Calendar")
        return
    }
    running := true
    try
    {
    text := A_Clipboard

    if (Trim(text) = "")
    {
        TrayTip(
            "先に予定が書かれた文章をコピーしてください。",
            "Google Calendar"
        )
        return
    }

    ; 一時ファイル名
    id := A_TickCount

    inputFile := A_Temp "\gcal_input_" id ".txt"
    resultFile := A_Temp "\gcal_result_" id ".txt"

    try FileDelete(inputFile)
    try FileDelete(resultFile)

    ; クリップボードをUTF-8で保存
    FileAppend(
        text,
        inputFile,
        "UTF-8"
    )

    ; Pythonファイル
    script := A_ScriptDir "\add_calendar.py"

    if !FileExist(script)
    {
        MsgBox(
            "add_calendar.py が見つかりません。`n`n" script,
            "Google Calendar エラー"
        )
        return
    }

    ; コマンド作成
    q := Chr(34)

    python := ""
    for candidate in [A_ScriptDir "\.venv\Scripts\pythonw.exe", "pyw.exe", "pythonw.exe"]
    {
        if (InStr(candidate, "\") && FileExist(candidate)) || !InStr(candidate, "\")
        {
            python := candidate
            break
        }
    }
    command := q python q " " q script q " " q inputFile q " " q resultFile q

    try
    {
        exitCode := RunWait(
            command,
            A_ScriptDir
        )
    }
    catch as err
    {
        MsgBox(
            "Pythonを起動できませんでした。`n`n" err.Message,
            "Google Calendar エラー"
        )
        return
    }

    ; Pythonの結果を読む
    if FileExist(resultFile)
    {
        result := FileRead(
            resultFile,
            "UTF-8"
        )
    }
    else
    {
        result := "Pythonから結果が返りませんでした。"
    }

    ; 成功
    if (exitCode = 0)
    {
        TrayTip(
            result,
            "Google Calendar"
        )
    }
    else
    {
        MsgBox(
            result,
            "Google Calendar 登録エラー"
        )
    }

    ; 一時ファイル削除
    try FileDelete(inputFile)
    try FileDelete(resultFile)
    }
    finally
    {
        running := false
    }
}
