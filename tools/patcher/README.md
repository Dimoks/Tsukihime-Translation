# HOW TO PATCH YOUR allui.mrg OR allpac.mrg
Well hello there. This tool right here *should* help you in creating your
own nice allui.mrg + allui.hed to put into your emulator's mod folder.

## 0. Set up a linux environment

If you're on linux, great! Skip this step.

If you're on Windows, the best way is to install Windows subsystem for Linux (WSL)
https://docs.microsoft.com/en-us/windows/wsl/install

Or you can build mangetsu tools for windows and install python on it.

## 1. Download a few tools.

Install python (``sudo apt python`` or your distro equivalent)

Or [Windows installer](https://www.python.org/downloads).

You need Dimoks's fork of Ross's mangetsu toolset: https://github.com/Dimoks/mangetsu - get it and build it according
to the readme there.

Download todds: https://github.com/todds-encoder/todds/releases

The binaries need to be in your PATH system variable for it to work. To do that, edit your ``~/.bashrc``
file and add them at the end of the file, like so:

    export PATH=$PATH:/path/to/todds/folder
    export PATH=$PATH:/path/to/mangetsu/build/folder

On Windows with powershell:
```powershell
$PATH = [Environment]::GetEnvironmentVariable("PATH", "User")
$my_path1 = "C:\Path\To\todds\folder"
$my_path2 = "C:\Path\To\mangetsu\build\mangetsu\folder"
[Environment]::SetEnvironmentVariable("PATH", "$PATH;$my_path1;$my_path2", "User")
```

## 2. Move the allui
Put an unaltered allui.mrg, allui.hed and allui.nam into the **_mrgs/tsuki_re_ja** folder.

## 3. Run the patch_allui.py
``python3 patch_allui.py tsuki_re_ja``

The script needs to be where it is: in the Tsukihime-Translation/tools/patcher/ folder. It will get everything it needs
from the repository (images, texts etc.) and compile them into the allui.mrg file.

## 4. Copy to mod folder
If all went well, you should have your new allui.* files in **_new_mrgs/tsuki_re_ja**. Have fun!

## 5. Do it again
If you need to rebuild your allui.mrg again, because new stuff has been translated / changed,
just run it again! The script will check for new changes and convert stuff automatically.

All of these steps are the same for patching patch.mrg too.

# config.ini
`tsuki_re_ja` is the **short name of the game** used for the archive compilation parameters specified in config.ini. Sections formatted as [short_name_of_game_name_of_archive] contain settings for building archives, specifying which files and parameters will be used for the compile.

The **short name of the game** determines the folder containing the game files for allui and parts, as well as some individual files, while the **name of archive** specifies the folder containing the files for a specific archive from the allpac archive set.

The patch_allui and patch_parts scripts require only the short name of the game as a parameter, while the patch_allpac script requires both the short name of the game and the archive name.

Examples of compilation commands:

    python3 patch_parts.py tsuki_re_ja
    python3 patch_allpac.py tsuki_re_ja allpac
    python3 patch_allpac.py tsuki_re_ja allpaccg

You can also use bash (.sh) or batch (.bat) scripts to initiate the compilation.
