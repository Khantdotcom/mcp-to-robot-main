*** Settings ***
Library    Browser

*** Test Cases ***
SCN_LOGIN_POS_00001
    New Browser    chromium
    New Page    https://automationplayground.github.io/playground/login.html
    Fill Text    id=inp_username    username
    Fill Text    id=inp_password    P@ssw0rd
    Click    text=Sign In
    Wait For Elements State    text=Personal Profile    visible
    Fill Text    id=first-name    John
    Fill Text    id=last-name    Doe
    Close Browser

SCN_LOGIN_NEG_00001
    New Browser    chromium
    New Page    https://automationplayground.github.io/playground/login.html
    Fill Text    id=inp_username    username
    Fill Text    id=inp_password    WrongP@ss
    Click    text=Sign In
    Get Text    text=Invalid Login
    Close Browser
