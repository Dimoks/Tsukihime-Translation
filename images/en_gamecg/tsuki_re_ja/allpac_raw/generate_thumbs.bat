@echo off
chcp 65001
setlocal enabledelayedexpansion

:: Main loop for processing files
for %%I in (*.jpg) do (
    echo Processing: %%~nxI
    call :toLower "%%~nI" lovername
    if errorlevel 1 (
        echo Error calling toLower function.
        pause
        exit /b 1
    )
    magick "%%I" -colorspace RGB -resize 16.69%% -colorspace sRGB "..\allpac_textures\!lovername!.png"
)

pause
goto :eof  :: End of the main script

:: Function to convert a string to lowercase and save it in another variable
:toLower
setlocal
:: strIn [in]  - value of the string to be converted
:: strOut [out] - reference to the string variable where the result will be saved
if "%~1"=="" (
    echo Error: Input string not provided.
    exit /b 1
)

set "result=%~1"  :: Get the value of the input string
if not defined result (
    echo Error: Input string is undefined.
    exit /b 1
)

:: Iterate over all uppercase characters and convert them to lowercase
for %%a in (
    "A=a" "B=b" "C=c" "D=d" "E=e" "F=f" "G=g" "H=h" "I=i"
    "J=j" "K=k" "L=l" "M=m" "N=n" "O=o" "P=p" "Q=q" "R=r"
    "S=s" "T=t" "U=u" "V=v" "W=w" "X=x" "Y=y" "Z=z"
    "А=а" "Б=б" "В=в" "Г=г" "Д=д" "Е=е" "Ё=ё" "Ж=ж" "З=з"
    "И=и" "Й=й" "К=к" "Л=л" "М=м" "Н=н" "О=о" "П=п" "Р=р"
    "С=с" "Т=т" "У=у" "Ф=ф" "Х=х" "Ц=ц" "Ч=ч" "Ш=ш" "Щ=щ"
    "Ъ=ъ" "Ы=ы" "Ь=ь" "Э=э" "Ю=ю" "Я=я"
) do (
    set "result=!result:%%~a!"
)

:: Save the result to the output variable
endlocal & set "%~2=%result%"
exit /b 0
