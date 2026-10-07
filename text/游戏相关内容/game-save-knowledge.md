
# 游戏存档领域知识库

> 修订说明：本表列出主流破解组 / 引擎的**默认**存档位置作为起点，具体游戏可能被 INI 改写或走 Windows VirtualStore 重定向。识别逻辑请遵守第 6 节"分析优先级"。
> 数据参考：[Ludusavi piracy-manifest](https://github.com/DogancanYr/ludusavi-piracy-manifest/blob/main/Piracy-manifest.yaml)、[gbe_fork README](https://github.com/Detanup01/gbe_fork/blob/dev/post_build/README.release.md)、[Goldberg emulator GitLab](https://gitlab.com/Mr_Goldberg/goldberg_emulator) 以及各破解组在流通版本里的实测路径。内容为多来源汇总改写（Content was rephrased for compliance with licensing restrictions）。

## 1. 破解组存档规则

存档实际文件通常在下表根目录之下再嵌 `{AppID}\` 或 `{AppID}\remote\`（有些游戏再嵌一层 `remote\out\`）。识别时应同时匹配这两层结构。

| 破解组 | 特征文件 | 默认存档根 | 备注 |
|:---|:---|:---|:---|
| CODEX | `codex.ini`, `steam_emu.ini` 含 `CODEX` | `Documents\Steam\CODEX\{AppID}\remote\` 或 `AppData\Roaming\Steam\CODEX\{AppID}\remote\` | 两个位置都要扫 |
| RUNE | `steam_emu.ini` 含 `RUNE` | `Documents\Steam\RUNE\{AppID}\remote\` | 目录名是 `RUNE`（或 `Rune`），不与 CODEX 共用 |
| PLAZA / DARKSiDERS / RLD! | 同 CODEX 系 ini | 同 CODEX 主路径；RLD! 常见 `Documents\Steam\RLD!\{AppID}\remote\` | 均为 CODEX 分支 |
| FLT | `flt.ini` | `AppData\Roaming\FLT\` （下面子结构因游戏而异） | 不一定有 `Steam\{AppID}` 层，别写死 |
| Goldberg（经典版） | `steam_interfaces.txt`, `steam_settings\` | `AppData\Roaming\Goldberg SteamEmu Saves\{AppID}\remote\` | Mr_Goldberg 原版 |
| Goldberg / gbe_fork / GSE Fork（新版主流） | `steam_settings\`, `configs.app.ini` 或 `configs.user.ini` | `AppData\Roaming\GSE Saves\{AppID}\remote\` | 近两年的默认路径已改名，见 gbe_fork README |
| Goldberg（`local_save_path`） | `configs.user.ini` 含 `[user::saves] local_save_path=` 或旧版 `local_save.txt` | 相对路径基准是 `steam_api(64).dll` 所在目录；**必须落在游戏目录之内**，越界不生效 | 见 gitlab issue #232 |
| EMPRESS | `empress.ini` 或 emu 目录里含 EMPRESS 特征 | `AppData\Roaming\EMPRESS\{AppID}\` 或 `EMPRESS\{AppID}\` | 很多 EMPRESS 版实际内嵌 Goldberg，最终存档可能落在 `AppData\Roaming\Goldberg SteamEmu Saves\{AppID}` 或游戏引擎自身路径（如 UE 的 `AppData\Local\{ProjectName}\`） |
| TENOKE | `tenoke.ini`, `Tenoke\` 目录 | `{GAME_DIR}\TENOKE\` 或 `{GAME_DIR}\Tenoke\` | 游戏目录内 |
| Ali213 | `ali213.ini` | `Documents\ALI213\{AppID}\Profile\` | **不在游戏目录**，是"我的文档" |
| 3DM | `3dm.ini`, `valve.ini`（3DM 常用） | `Documents\3DMGAME\` 或游戏目录 `Profile\` | 不同版本习惯不同，两处都要扫 |
| SKIDROW | `SKIDROW.ini` | `AppData\Local\SKIDROW\{AppID or GameName}\` 或 `Documents\SKIDROW\{GameName}\` | 老版走 Documents，新版走 LocalAppData |
| OnlineFix | `OnlineFix.ini`, `OnlineFix64.dll` | `Documents\OnlineFix\{AppID}\` | 近几年常见 |
| Razor1911 | `.1911` 目录, 特征 dll | `AppData\Roaming\.1911\` | 目录名以点开头 |
| SmartSteamEmu (SSE) | `SmartSteamEmu.ini` | `AppData\Roaming\SmartSteamEmu\{AppID}\` | 老工具 |
| CreamAPI | `cream_api.ini`, `steam_api64_o.dll` | `AppData\Roaming\CreamApi\` | 主要是 DLC 解锁，偶尔也承载少量存档/成就 |

**关于 GOG**：GOG 是正版发行平台而非破解组，其游戏的存档路径由游戏自身决定，常见于 `Documents\My Games\{GameName}\`、`AppData\Roaming\{GameName}\` 或 GOG Galaxy 的 `C:\ProgramData\GOG.com\Galaxy\`。识别时不要按"破解组"处理。

## 2. 引擎识别

| 引擎 | 识别特征 | 默认存档位置 |
|:---|:---|:---|
| Unreal Engine 4/5 | `Engine\` 目录, `Binaries\Win64\`, `*.uproject`, exe 后缀 `-Win64-Shipping` | `AppData\Local\{ProjectName}\Saved\SaveGames\` |
| Unity | `UnityPlayer.dll`, `*_Data\`, `boot.config` | `AppData\LocalLow\{Company}\{Product}\` |
| Godot | `.pck`, `.godotproject` 内嵌 | `AppData\Roaming\Godot\app_userdata\{ProjectName}\` |
| CryEngine | `CrySystem.dll`, `Engine\` 内含 CryEngine 特征 | 因游戏而异，通常 `Documents\My Games\{GameName}\` |
| RE Engine（Capcom） | `.pak` + `re_chunk_*.pak`, exe 常见 `re4.exe` `mhrise.exe` 等 | `AppData\Roaming\CAPCOM\{GameName}\` 或 `AppData\Local\CAPCOM\{GameName}\` |
| Creation Engine（Bethesda） | `.esm`/`.esp`, `SkyrimSE.exe` 类 | `Documents\My Games\{GameName}\Saves\` |
| REDengine（CDPR） | 巫师3/2077 特征 | `Documents\CD Projekt Red\{GameName}\`；2077 走 `Saved Games\CD Projekt Red\Cyberpunk 2077\` |
| RAGE（R\*） | GTA5/RDR2 | `Documents\Rockstar Games\{GameName}\Profiles\` |
| Source / GoldSrc（V 社） | `hl2.exe`/`hl.exe` 类, `gameinfo.txt` | `{GAME_DIR}\{mod}\SAVE\`（游戏目录内） |
| Clausewitz（P 社） | `stellaris.exe`/`hoi4.exe` 等 | `Documents\Paradox Interactive\{GameName}\save games\` |
| GameMaker | `data.win`, `runner.exe` | `AppData\Local\{GameName}\` |
| Ren'Py | `renpy\`, `game\script.rpy` | `AppData\Roaming\RenPy\{GameName}\` |
| RPG Maker XP / VX / VXAce | `Game.rgss*a`, `RGSS*.dll` | 游戏目录下 `Save01.rxdata` 等文件 |
| RPG Maker MV / MZ（NW.js） | `www\` 目录, `nw.dll`, `package.json` | 老式：`www\save\`；新式：`AppData\Local\{GameName}\User Data\Default\IndexedDB\file__0\`（NW.js IndexedDB） |
| Java（Minecraft） | `.minecraft\`, launcher | `AppData\Roaming\.minecraft\saves\` |

**UE `{ProjectName}` 说明**：通常等于 exe 主名（去掉 `-Win64-Shipping` 等后缀），例如 `ch5_pro-Win64-Shipping.exe` → `ch5_pro`。但**存在例外**：
- Hogwarts Legacy：exe 是 `HogwartsLegacy.exe`，目录是 `Hogwarts Legacy`（带空格），EMPRESS 版内部代号则是 `Phoenix`
- 加壳 / Denuvo 剥离后 exe 元信息可能被改，反推不可靠
- 严谨做法：先读 `{GAME_DIR}\{ProjectName}\Config\DefaultEngine.ini` 或 `DefaultGame.ini` 里的 `ProjectName` / `ProjectDisplayedTitle`，取不到再回退到扫描 `AppData\Local\*\Saved\SaveGames\` 反匹配

## 3. 着色器缓存路径

| 来源 | 路径 |
|:---|:---|
| UE 引擎 | `AppData\Local\{ProjectName}\Saved\` 下的 `*.upipelinecache` / `ShaderDebug\` |
| Unity 游戏运行时 | 多数不显式落盘；部分走 `AppData\LocalLow\{Company}\{Product}\` |
| Unity 编辑器构建缓存 | `AppData\Local\Unity\Caches\` |
| DirectX Shader Cache（系统） | `AppData\Local\D3DSCache\` |
| NVIDIA DX | `AppData\Local\NVIDIA\DXCache\` |
| NVIDIA GL / Vulkan | `AppData\Local\NVIDIA\GLCache\` |
| NVIDIA 系统级 | `C:\ProgramData\NVIDIA Corporation\NV_Cache\` |
| AMD DX | `AppData\Local\AMD\DxCache\` |
| AMD GL / Vulkan | `AppData\Local\AMD\GLCache\` |
| Intel GPU | `AppData\LocalLow\Intel\ShaderCache\` |

## 4. 存档文件特征

- **存档文件夹名**：`save`, `saves`, `savedata`, `savegames`, `SaveGames`, `Profile`, `Profiles`, `userdata`, `remote`, `slot0`~`slot9`
- **存档扩展名**：`.sav`, `.save`, `.dat`, `.json`, `.xml`, `.bin`, `.bak`, `.profile`, `.db`, `.sqlite`, `.rxdata` / `.rvdata` / `.rvdata2`（RPG Maker）
- **常见配置文件名**：`GameUserSettings.ini`（UE）, `Engine.ini`（UE）, `boot.config`（Unity）, `graphicsconfig.xml`（部分自研）, `config.ini`, `settings.ini`, `options.ini`, `system.cfg`（CryEngine）
- **Steam Cloud 特征**：`steam_autocloud.vdf`、路径包含 `Steam\userdata\{SteamID3}\{AppID}\remote\`

## 5. 分析优先级规则

1. **进程实际写入**（procmon / ETW 观测）> 静态推理
2. **INI 中的显式 SavePath / local_save_path** > 破解组默认规则 > 引擎默认规则 > 启发式搜索
3. **已存在且非空的路径** > 存在但为空的路径 > 推测但不存在的路径
4. **游戏目录内的存档**（若破解组明确便携化）> **外部目录**（多数正版引擎行为）
5. 出现多个候选时，比较文件 mtime 与游戏最后运行时间，取时间相近者

## 6. 常见陷阱

- **多路径共存**：同一游戏可能同时有引擎存档 + 破解组存档 + Steam Cloud 存档，不同存档相互覆盖会丢档
- **Goldberg `local_save_path` 边界**：相对路径基准是 `steam_api(64).dll` 所在目录，且解析结果必须在游戏目录之内，越界（绝对路径或跳出游戏根）会被忽略
- **UE `ProjectName` 反推陷阱**：exe 名 → 项目名并非可靠映射，Shipping 后缀、内部代号、加壳都会打断反推；优先读 UE 配置文件
- **RPG Maker MV/MZ 的 IndexedDB**：NW.js 的 IndexedDB 路径带 `file__0\` 子目录且是二进制 LevelDB 格式，用文本工具直接看不到存档内容
- **未运行过时的空态**：游戏未首次启动时，所有推断出的目录可能都不存在；不要据此判断"游戏没有存档系统"
- **32/64 位注册表**：32 位程序在 64 位系统写入注册表时会被重定向到 `HKLM\SOFTWARE\WOW6432Node\`，忽略这一点会漏读配置
- **VirtualStore 重定向**：非管理员进程写入 `Program Files\` 或 `Windows\` 会被静默重定向到 `AppData\Local\VirtualStore\...`，看似写在游戏目录，实际落到 VirtualStore
- **Windows Store / Xbox Game Pass 版**：完全不同的沙盒结构，存档在 `AppData\Local\Packages\{PackageFamilyName}\SystemAppData\wgs\` 下的容器目录，且以 `container.*` + GUID 命名，与 Steam 版不能直接互换
- **符号链接 / 目录连接**：便携整合包常见用 `mklink /J` 把 `AppData\Local\{Project}` 重定向到游戏目录，扫描时应通过 reparse point 属性识别，避免被误认为"没有引擎存档"
- **Steam Cloud vs 本地**：正版走 Steam Cloud 时本地引擎目录可能是空的，真正数据在 `Steam\userdata\{SteamID3}\{AppID}\remote\`
- **exe 加壳导致的名称漂移**：Denuvo/VMP 脱壳后可能重命名主 exe（如 `game.exe` 与 `game-Win64-Shipping.exe` 并存），要看清哪个是真入口
- **中文/空格路径**：`{ProjectName}` 可能含空格（如 `Hogwarts Legacy`），拼路径时必须整体加引号

