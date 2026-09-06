
# 游戏存档领域知识库

## 1. 破解组存档规则

| 破解组 | 特征文件 | 默认存档位置 |
|:---|:---|:---|
| CODEX/RUNE | codex.ini, steam_emu.ini 含 CODEX/RUNE | %PUBLIC%\Documents\Steam\CODEX\{AppID} |
| FLT | flt.ini | %APPDATA%\FLT\Steam\{AppID} |
| Goldberg | steam_interfaces.txt, steam_settings/ | %APPDATA%\Goldberg SteamEmu Saves\{AppID} |
| Goldberg(local_save_path) | + configs.user.ini 含 local_save_path | 相对于 steam_api64.dll 所在目录 |
| EMPRESS | empress.ini | %LOCALAPPDATA%\EMPRESS\{AppID} |
| TENOKE | tenoke.ini | %GAME_DIR%\Tenoke |
| Ali213/3DM | ali213.ini/3dm.ini | %GAME_DIR%\Profile |
| GOG | goggame-*.info | %USERPROFILE%\Documents\My Games\{GameName} |
| SKIDROW | SKIDROW.ini | %LOCALAPPDATA%\SKIDROW\{AppID} |
| PLAZA/DARKSiDERS | 同 CODEX | 同 CODEX |
| SSE | SmartSteamEmu.ini | %APPDATA%\SmartSteamEmu\{AppID} |

## 2. 引擎识别

| 引擎 | 识别特征 | 存档位置 |
|:---|:---|:---|
| Unreal Engine 4/5 | Engine 目录, Binaries\Win64, .uproject | %LOCALAPPDATA%\{ProjectName}\Saved\SaveGames |
| Unity | UnityPlayer.dll, *_Data 目录 | %LOCALAPPDATA%Low\{Company}\{Product} |
| CryEngine | CrySystem.dll | 因游戏而异 |
| Godot | .pck 文件 | %APPDATA%\Godot\app_userdata\{ProjectName} |
| RPG Maker | www 目录, nw.dll | 游戏目录内 save 或 www/save |
| RE Engine | .bin 格式存档 (Capcom) | 因游戏而异，通常在 %APPDATA% 或游戏目录 |

UE 引擎重要：ProjectName 通常是 exe 名去掉扩展名（如 ch5_pro.exe → ch5_pro），不是游戏显示名。

## 3. 着色器缓存路径

| 来源 | 路径 |
|:---|:---|
| UE 引擎 | %LOCALAPPDATA%\{ProjectName}\Saved\*.upipelinecache |
| Unity | %LOCALAPPDATA%\Unity\cache\ |
| DirectX 系统 | %LOCALAPPDATA%\D3DSCache\ |
| NVIDIA DX | %LOCALAPPDATA%\NVIDIA\DXCache\ |
| NVIDIA GL | %LOCALAPPDATA%\NVIDIA\GLCache\ |
| AMD | %LOCALAPPDATA%\AMD\DxCache\ |

## 4. 存档文件特征

存档文件夹名：save, saves, savedata, savegames, SaveGames, Profile, Profiles, userdata, remote
存档扩展名：.sav, .save, .dat, .json, .xml, .bin, .bak, .profile, .db, .sqlite
配置文件名：GameUserSettings.ini, boot.config, config.ini, settings.ini, options.ini

## 5. 分析优先级规则

1. INI 文件中的显式 SavePath > 破解组默认规则 > 启发式搜索
2. 已验证存在的路径 > 推测路径
3. 游戏目录内的存档 > 外部目录的存档

## 6. 常见陷阱

- 同一游戏可能有多个存档位置（引擎存档 + 破解组存档）
- Goldberg 的 local_save_path 相对路径基准是 DLL 目录，不是游戏根目录
- UE 的 ProjectName 是 exe 名，不是游戏显示名
- 游戏未运行过时，所有存档目录都不存在
- 注册表路径可能因 32/64 位系统而不同（注意 WOW6432Node）
- 部分游戏使用 Windows 的 VirtualStore 机制重定向写入
