# 游戏图形配置文件领域知识库（Windows）

> 适用范围：Windows PC 游戏的分辨率、窗口模式、刷新率、垂直同步、帧率上限、画质档位、渲染 API、光线追踪与超分辨率等设置。
>
> 本文给出的路径是**候选路径和识别规则**，不是所有游戏都必须遵循的标准。开发者可以自行改名、改路径、改格式，游戏更新也可能迁移配置。路径存在不等于文件正在生效；应按第 11 节的方法验证。
>
> 资料优先采用引擎和厂商官方文档，具体游戏缺乏官方说明时再采用可交叉验证的社区资料。全文为多来源归纳改写（Content was rephrased for compliance with licensing restrictions）。

## 1. 路径占位符

| 占位符 | 常见展开值 | 注意事项 |
|:---|:---|:---|
| `%LOCALAPPDATA%` | `C:\Users\<用户名>\AppData\Local` | 本机相关数据，通常不漫游 |
| `%APPDATA%` | `C:\Users\<用户名>\AppData\Roaming` | Roaming，而不是整个 AppData |
| `%USERPROFILE%` | `C:\Users\<用户名>` | 不要据此硬拼实际“文档”目录 |
| `{DOCUMENTS}` | 当前用户真实“文档”目录 | 可能被迁移到 OneDrive 或其他盘；程序应通过 Windows `FOLDERID_Documents` 获取，参见 [Microsoft Known Folders](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid) |
| `{SAVED_GAMES}` | 当前用户真实“保存的游戏”目录 | 程序应通过 `FOLDERID_SavedGames` 获取 |
| `{GAME_DIR}` | 游戏主目录 | 通常是主 exe 或启动器附近的目录 |
| `{PROJECT}` | 引擎内部项目名 | 可能不同于商店显示名和 exe 名 |
| `{COMPANY}` / `{PRODUCT}` | Unity 公司名 / 产品名 | 来自构建时 Player Settings，可能是旧名或内部名 |
| `{STEAM_DIR}` | Steam 安装目录 | 不保证在 `C:\Program Files (x86)` |
| `{STEAM_ID3}` | Steam 用户目录使用的数字 ID | 一台电脑可有多个账号目录 |
| `{APP_ID}` | Steam AppID | 同一游戏的试玩版、测试分支可能不同 |
| `{PFN}` | Microsoft Store / Xbox 包系列名 | 通常是较长的发行商与产品标识 |

## 2. 先区分五类文件

| 类型 | 示例 | 是否应优先修改 |
|:---|:---|:---|
| **当前用户配置** | `GameUserSettings.ini`, `UserSettings.json`, `settings.xml`, `options.txt` | 是；最可能承载当前图形设置 |
| **项目默认配置** | `DefaultGameUserSettings.ini`, `BaseScalability.ini`, `project.godot` | 否；通常只是首次生成或回退时的默认值 |
| **启动覆盖** | Steam 启动选项、`commandline.txt`, `autoexec.cfg` | 仅在排错或明确需要时使用；它可能覆盖用户配置 |
| **自动检测 / 硬件缓存** | benchmark 结果、GPU 指纹、`sga_*`、着色器缓存 | 通常不要改；它们不一定是用户偏好 |
| **存档 / 账号配置** | `remote\`, `SaveGames\`, `pc_settings.bin` 中非图形数据 | 不要仅凭文件名混入图形配置 |

配置优先级没有跨引擎统一标准。常见关系是“启动参数或运行时命令 > 当前用户配置 > 项目默认配置”，但游戏脚本、启动器和云同步都可能改变顺序，必须实测。

## 3. 快速定位表

| 引擎 / 游戏系列 | 主要候选位置 | 主要文件或存储 | 可靠程度 |
|:---|:---|:---|:---|
| Unreal Engine 4/5 | `%LOCALAPPDATA%\{PROJECT}\Saved\Config\{PLATFORM}\` | `GameUserSettings.ini`；可选 `Engine.ini` | 高（引擎惯例） |
| Unity | `HKCU\Software\{COMPANY}\{PRODUCT}`；`%USERPROFILE%\AppData\LocalLow\{COMPANY}\{PRODUCT}\` | PlayerPrefs 注册表值；游戏自定义 JSON/XML/二进制 | 中（位置稳定，字段不统一） |
| Godot | `%APPDATA%\Godot\app_userdata\{PROJECT}\` 或自定义 `user://` | 游戏自定义 `.cfg` / `.ini` / JSON；无统一文件名 | 中（根目录稳定，字段不统一） |
| CryEngine | `{GAME_DIR}\` 与游戏自定义用户目录 | `system.cfg`, `user.cfg`, `game.cfg` | 中低（游戏差异大） |
| Source 1 | `{GAME_DIR}\{MOD}\cfg\` 或 `{STEAM_DIR}\userdata\...\local\cfg\` | `video.txt`, `config.cfg`, `autoexec.cfg` | 中（版本 / 游戏差异） |
| Source 2 | 游戏目录 `game\{MOD}\cfg\` 或 Steam 用户目录 | `.vcfg`, `cs2_video.txt` 等 | 中低（按游戏实现） |
| Creation Engine | `{DOCUMENTS}\My Games\{GAME}\` | `{Game}Prefs.ini`, `{Game}.ini`, `{Game}Custom.ini` | 高（系列惯例） |
| Cyberpunk 2077 | `%LOCALAPPDATA%\CD Projekt Red\Cyberpunk 2077\` | `UserSettings.json` | 高（具体游戏） |
| The Witcher 3 | `{DOCUMENTS}\The Witcher 3\` | `user.settings`；次世代 DX12 版可能有 `dx12user.settings` | 高（具体游戏，版本有差异） |
| RE Engine | 多数在 `{GAME_DIR}\` | `re*_config.ini`, `config.ini`, `graphics_option.ini` 等 | 中（文件名随游戏变化） |
| GTA V | `{DOCUMENTS}\Rockstar Games\GTA V\`；同时检查官方文章使用的 `GTAV\` 拼法 | `settings.xml`；Profile 下另有 `pc_settings.bin` | 高（具体游戏，目录名有版本差异） |
| Red Dead Redemption 2 | `{DOCUMENTS}\Rockstar Games\Red Dead Redemption 2\Settings\` | `system.xml` | 高（厂商官方） |
| Clausewitz / Jomini | `{DOCUMENTS}\Paradox Interactive\{GAME}\` | `settings.txt`, `pdx_settings.txt` 或版本对应变体 | 中高（系列惯例） |
| X-Ray | `fsgame.ltx` 中 `$app_data_root$` 指向的位置 | `user.ltx` | 高（先解析重定向） |
| Minecraft Java | 当前实例的游戏目录；默认 `%APPDATA%\.minecraft\` | `options.txt`；模组另有 `config\` | 高（具体游戏） |
| Microsoft Store / Xbox | `%LOCALAPPDATA%\Packages\{PFN}\LocalState\` | 文件名由游戏决定；Unity UWP 常见 `playerprefs.dat` | 中（容器稳定，内部不统一） |

`{PLATFORM}` 对 UE 游戏应至少尝试 `Windows`、`WindowsNoEditor` 和 `WinGDK`。不要只扫描其中一个。

## 4. Unreal Engine 4/5

Epic 的 [`UGameUserSettings`](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/GameFramework/UGameUserSettings) 专门管理本机的分辨率、窗口模式、画质档位等用户设置；[Scalability Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine) 说明了 `sg.*` 质量组和 `r.*` 渲染变量的关系。

### 4.1 路径与文件

```text
%LOCALAPPDATA%\{PROJECT}\Saved\Config\Windows\GameUserSettings.ini
%LOCALAPPDATA%\{PROJECT}\Saved\Config\WindowsNoEditor\GameUserSettings.ini
%LOCALAPPDATA%\{PROJECT}\Saved\Config\WinGDK\GameUserSettings.ini
```

- `GameUserSettings.ini`：当前用户的分辨率、窗口模式、VSync、帧率上限和画质组；首选目标。
- `Engine.ini`：可能包含 `[SystemSettings]` 下的 `r.*` 覆盖，也可能为空或不存在；游戏可禁用某些 CVar。
- `Scalability.ini`：可能用于自定义档位定义，不一定保存玩家当前档位，也不保证生成。
- `{GAME_DIR}\{PROJECT}\Config\DefaultGameUserSettings.ini`：项目默认值，不是当前用户副本。
- `{GAME_DIR}\Engine\Config\BaseScalability.ini`：引擎基础档位模板，不应当作玩家配置编辑。

### 4.2 通用字段

```ini
[/Script/Engine.GameUserSettings]
bUseVSync=True
ResolutionSizeX=1920
ResolutionSizeY=1080
LastUserConfirmedResolutionSizeX=1920
LastUserConfirmedResolutionSizeY=1080
FullscreenMode=1
LastConfirmedFullscreenMode=1
FrameRateLimit=120.000000

[ScalabilityGroups]
sg.ResolutionQuality=100.000000
sg.ViewDistanceQuality=2
sg.AntiAliasingQuality=2
sg.ShadowQuality=2
sg.GlobalIlluminationQuality=2
sg.ReflectionQuality=2
sg.PostProcessQuality=2
sg.TextureQuality=2
sg.EffectsQuality=2
sg.FoliageQuality=2
sg.ShadingQuality=2
```

| 字段 | 常见语义 | 注意事项 |
|:---|:---|:---|
| `ResolutionSizeX/Y` | 输出宽度 / 高度 | 无边框模式可能按桌面分辨率运行并忽略它们 |
| `LastUserConfirmedResolutionSizeX/Y` | 最后确认的分辨率 | 手工改分辨率时通常一起改，避免游戏回退 |
| `FullscreenMode` | `0` 独占全屏、`1` 无边框全屏、`2` 窗口 | 这是 UE 的映射，不能套到其他引擎；模式含义可对照 Epic 的 [`EWindowMode`](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/ApplicationCore/GenericPlatform/EWindowMode__Type) |
| `LastConfirmedFullscreenMode` | 最后确认的窗口模式 | 通常与目标模式保持一致 |
| `bUseVSync` | 垂直同步 | `True` / `False` |
| `FrameRateLimit` | 帧率上限 | Epic API 规定 `0` 表示不由该字段限帧；驱动或游戏仍可能限帧 |
| `sg.ResolutionQuality` | 内部渲染比例 | 常见为百分比，不遵循其他 `sg.*` 的 0～4 档位 |
| 其他 `sg.*Quality` | 质量档位 | 通常 `0` 低、`1` 中、`2` 高、`3` Epic、`4` Cinematic；游戏可裁剪、重映射或不用某一组 |

不要假设 DLSS、FSR、XeSS、帧生成、光追或动态分辨率存在统一字段。这些通常是游戏扩展到 `GameUserSettings.ini` 的自定义键，应以该游戏实际生成的键和值为准。

### 4.3 排错启动参数

Epic 的[命令行参数文档](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-command-line-arguments-reference)列出了引擎可识别的参数。常见排错形式：

```text
-ResX=1280 -ResY=720 -Windowed
```

`-dx11`、`-dx12`、`-vulkan` 等参数只有游戏构建包含对应 RHI 且未被启动器拦截时才有效，不能仅凭 UE 引擎身份保证支持。

## 5. Unity

**Unity 没有规定所有游戏必须使用同一个图形配置文件。** 官方 [`PlayerPrefs`](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/PlayerPrefs.html) 只提供字符串、浮点数和整数持久化机制，字段名由游戏开发者决定。

### 5.1 两条主要存储路径

1. Windows Standalone 的 PlayerPrefs：

```text
HKEY_CURRENT_USER\Software\{COMPANY}\{PRODUCT}
```

2. 文件型用户数据候选目录：

```text
%USERPROFILE%\AppData\LocalLow\{COMPANY}\{PRODUCT}\
```

游戏可能在 LocalLow 目录中自行创建 `settings.json`、`config.xml`、`prefs`、数据库或二进制文件。**不能因为没有注册表字段就断定没有配置，也不能因为存在 LocalLow 就断定图形设置一定在文件里。**

Unity UWP 构建的 PlayerPrefs 官方位置是：

```text
%LOCALAPPDATA%\Packages\{PFN}\LocalState\playerprefs.dat
```

### 5.2 注册表识别

常见键名前缀包括：

```text
Screenmanager Resolution Width
Screenmanager Resolution Height
Screenmanager Fullscreen mode
Screenmanager Is Fullscreen mode
UnityGraphicsQuality
```

- 名称可能附带 `_h<数字>` 哈希后缀；保留完整键名。
- 不同 Unity 版本、旧版启动分辨率对话框和游戏自定义代码可能使用不同键。
- `UnityGraphicsQuality` 往往是构建时 Quality Settings 列表的索引，索引与“低/中/高”的对应由该游戏决定。
- 修改时保留原注册表数据类型（常见为 `REG_DWORD`）；先导出该游戏子键备份。

`{GAME}_Data\boot.config`、`globalgamemanagers` 等属于构建 / 启动数据，**不是通用的当前用户图形配置**，不应作为首选修改目标。

### 5.3 排错启动参数

Unity 官方的 [Player command-line arguments](https://docs.unity3d.com/6000.3/Documentation/Manual/PlayerCommandLineArguments.html) 包括：

```text
-screen-width 1280 -screen-height 720 -screen-fullscreen 0
-window-mode borderless
-screen-quality Low
```

- `-screen-fullscreen` 只接受 `0` 或 `1`。
- `-window-mode` 在 Windows 可请求 `exclusive` 或 `borderless`。
- `-screen-quality` 后面是游戏构建内的质量档位**名称**，不是固定数字。
- 游戏自己的启动脚本可能在引擎初始化后再次覆盖这些值。

## 6. Godot

Godot 官方建议把持久化设置写入 `user://`。根据[数据路径文档](https://docs.godotengine.org/en/stable/tutorials/io/data_paths.html)，Windows 默认位置为：

```text
%APPDATA%\Godot\app_userdata\{PROJECT}\
```

如果开发者启用自定义用户目录，则可能变成：

```text
%APPDATA%\{PROJECT}\
%APPDATA%\{CUSTOM_USER_DIR_NAME}\
```

### 6.1 文件与字段

- Godot 不规定玩家设置的统一文件名；常见 `settings.cfg`、`config.cfg`、INI、JSON 或自定义资源。
- 官方 [`ConfigFile`](https://docs.godotengine.org/en/stable/classes/class_configfile.html) 使用类似 INI 的 section/key 格式，但 `.cfg` 与 `.ini` 后缀本身不决定解析器。
- `project.godot` 是项目设置源；导出后通常位于 PCK 内，不是普通用户配置。
- `res://override.cfg` 可覆盖 ProjectSettings；官方 [`ProjectSettings`](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html) 说明导出项目也能读取覆盖文件。但它属于项目级覆盖，游戏脚本自行保存的图形偏好仍可能在 `user://`，两者不要混为一谈。

可搜索的 Godot 项目键包括：

```text
display/window/size/*
display/window/vsync/*
rendering/renderer/rendering_method
rendering/rendering_device/driver*
```

这些是项目设置命名空间；玩家自定义配置可能使用完全不同的键。

### 6.2 排错启动参数

Godot 官方[命令行教程](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)提供：

```text
--windowed --resolution 1280x720
--fullscreen
--rendering-method gl_compatibility
--rendering-driver <driver>
--gpu-index <index>
```

先用 `--help` 查看当前构建支持的渲染驱动，不要猜测驱动名称。

## 7. CryEngine

CRYENGINE 通过控制台变量（CVar）管理大量渲染设置，官方的 [Console Variables & Config Files](https://docs.cryengine.com/pages/viewpage.action?pageId=25535264) 说明 CVar 可在运行时、配置文件或启动参数中设置。

常见候选：

```text
{GAME_DIR}\system.cfg
{GAME_DIR}\user.cfg
{GAME_DIR}\game.cfg
```

常见键：

```ini
r_Width=1920
r_Height=1080
r_Fullscreen=1
r_VSync=1
sys_spec=3
```

- `system.cfg` 常是启动默认或发行配置；`user.cfg` 常用于用户覆盖；具体读取顺序由游戏决定。
- 部分游戏把实际用户配置写到 Documents、Saved Games 或 AppData，再由启动器生成 cfg。
- `sys_spec` 和 `r_*` 的可用范围随 CryEngine 版本及游戏裁剪变化；先从游戏自己生成的文件中采样，不要直接套用网络上的整份“优化配置”。

## 8. Source / Source 2

Valve Developer Community 对 [CFG](https://developer.valvesoftware.com/wiki/CFG) 的定义是逐行执行控制台命令的文本文件，并指出 `config.cfg` 可能在退出时由游戏重写；因此长期自定义通常更适合放入 `autoexec.cfg`，而不是把 `config.cfg` 设为只读。

### 8.1 Source 1

候选位置：

```text
{GAME_DIR}\{MOD}\cfg\video.txt
{GAME_DIR}\{MOD}\cfg\config.cfg
{GAME_DIR}\{MOD}\cfg\autoexec.cfg
{STEAM_DIR}\userdata\{STEAM_ID3}\{APP_ID}\local\cfg\
```

常见键 / 命令：

```text
setting.defaultres
setting.defaultresheight
setting.fullscreen
setting.nowindowborder
setting.mat_vsync
mat_antialias
mat_forceaniso
fps_max
```

### 8.2 Source 2

Source 2 使用 `.vcfg` 等变体；参见 Valve 的 [VCFG](https://developer.valvesoftware.com/wiki/VCFG) 说明。路径按游戏变化，例如 CS2 常见：

```text
{STEAM_DIR}\userdata\{STEAM_ID3}\730\local\cfg\cs2_video.txt
```

不要把 CS2 的 AppID、文件名或字段直接推广到所有 Source 2 游戏。

### 8.3 排错参数

常见 Source 启动参数包括：

```text
-autoconfig
-safe
-windowed -w 1280 -h 720
-fullscreen
```

不同游戏支持集不完全相同；可从 Valve 的 [Command Line Options](https://developer.valvesoftware.com/wiki/Command_Line_Options) 开始核对。

## 9. 常见商业引擎 / 游戏系列

### 9.1 Creation Engine（Bethesda）

```text
{DOCUMENTS}\My Games\Skyrim Special Edition\SkyrimPrefs.ini
{DOCUMENTS}\My Games\Fallout4\Fallout4Prefs.ini
{DOCUMENTS}\My Games\Starfield\StarfieldPrefs.ini
```

常见字段：

```ini
[Display]
iSize W=1920
iSize H=1080
bFull Screen=1
bBorderless=0
iPresentInterval=1
```

- `{Game}Prefs.ini` 通常保存启动器 / 菜单产生的显示偏好。
- `{Game}.ini` 通常有引擎和游戏设置；用户扩展更适合 `{Game}Custom.ini`（若该游戏支持）。
- 字段并非每代都一致。Bethesda 官方对 Fallout 3 的说明确认 `FalloutPrefs.ini` 位于 Documents 的 `My Games\Fallout3`，并用 `iSize W/H` 修改分辨率，参见[官方支持文章](https://help.bethesda.net/app/answers/detail/a_id/9997/)。
- 启动器可能覆盖 `Prefs.ini`；改之前退出游戏及启动器。

### 9.2 REDengine / CD PROJEKT RED

**Cyberpunk 2077**：

```text
%LOCALAPPDATA%\CD Projekt Red\Cyberpunk 2077\UserSettings.json
```

配置是带类型与当前值的嵌套 JSON，常包含分辨率、窗口模式、各画质项、光追、DLSS/FSR/XeSS 等。应只改已有字段的当前值，不要删除类型、上下限、默认值等元数据。[PCGamingWiki 的 Cyberpunk 2077 页面](https://www.pcgamingwiki.com/wiki/Cyberpunk_2077)可交叉验证 `UserSettings.json` 的路径；CDPR 的[干净安装说明](https://support.cdprojektred.com/en/cyberpunk/pc/sp-technical/issue/2233/how-do-i-perform-a-clean-install-of-the-game)也要求清理 `%LOCALAPPDATA%` 下的 `CD Projekt Red` 与 `REDEngine`，可用于确认该系列的本地配置根。

**The Witcher 3**：

```text
{DOCUMENTS}\The Witcher 3\user.settings
{DOCUMENTS}\The Witcher 3\dx12user.settings
```

`dx12user.settings` 与次世代 DX12 分支相关，是否存在取决于版本与启动的渲染分支；切换 DX11 / DX12 后要重新确认实际修改时间。文件位置与分支差异可由 [PCGamingWiki 的 The Witcher 3 页面](https://www.pcgamingwiki.com/wiki/The_Witcher_3:_Wild_Hunt)交叉验证。

### 9.3 RE Engine（Capcom）

RE Engine 没有面向所有游戏的统一公开用户配置规范，常见文件位于游戏根目录：

```text
re2_config.ini
re3_config.ini
re8_config.ini
re4_config.ini
config.ini
graphics_option.ini
graphics_option_preset.ini
```

识别建议：

- 文件名中的游戏缩写不是固定规则；先枚举 `*config*.ini`、`*graphics*.ini`。
- 内容常见 `[Render]`、`[RenderConfig]`、`Resolution`、`WindowMode`、`DisplayName`、`RefreshRate`、`VSync`、`TargetPlatform` 等，但实际键和值随作品变化。
- 不要预设 `DisplayMode=Borderless` 之类的统一 schema；必须以原文件已有值和游戏菜单前后差异为准。
- Monster Hunter: World 常见 `graphics_option.ini`；Monster Hunter Rise 常见 `config.ini`；Resident Evil 重制系列常见 `re*_config.ini`。

### 9.4 RAGE（Rockstar）

**GTA V Legacy** 常见：

```text
{DOCUMENTS}\Rockstar Games\GTA V\settings.xml
{DOCUMENTS}\Rockstar Games\GTA V\Profiles\{PROFILE}\pc_settings.bin
{DOCUMENTS}\Rockstar Games\GTAV\Profiles\{PROFILE}\pc_settings.bin
{GAME_DIR}\commandline.txt
```

- `settings.xml` 主要承载画质 / 显示项；[PCGamingWiki 的 GTA V 页面](https://www.pcgamingwiki.com/wiki/Grand_Theft_Auto_V)记录的常见目录名是 `GTA V`。
- Rockstar 的[官方重置说明](https://support.rockstargames.com/articles/4dfq6KRAlNvJgIxLLZGY4q/being-asked-to-accept-terms-of-service-and-recalibrate-settings-each-time-grand-theft-auto-v-on-pc-is-launched)把 `pc_settings.bin` 路径写作 `GTAV\Profiles\...`。不同版本 / 文档出现了 `GTA V` 与 `GTAV` 两种拼法，自动扫描应检查两者；该二进制还包含其他用户偏好，不应按 XML 或文本处理。
- Rockstar 官方允许在游戏根目录创建 `commandline.txt`，支持 `-safemode`、`-useMinimumSettings`、`-windowed`、`-fullscreen`、`-borderless`、`-width`、`-height` 等；完整列表见[官方命令行文章](https://support.rockstargames.com/articles/2VjbVziQCiTiiVhDbmnexc/full-list-of-command-line-parameters-for-grand-theft-auto-v-on-pc)。
- GTA V Enhanced 使用独立产品目录时，目录名可能是 `GTAV Enhanced`；不要与 Legacy 的文件互相覆盖。

**Red Dead Redemption 2**：

```text
{DOCUMENTS}\Rockstar Games\Red Dead Redemption 2\Settings\system.xml
```

Rockstar 的[官方故障排除](https://support.rockstargames.com/articles/2MQafAtBWiOUJrPDLx5I2U/err-gfx-init-error-when-launching-red-dead-redemption-2-on-pc)确认该路径，并说明可在 `system.xml` 中切换 Vulkan / DX12；同目录 `sga_*` 是图形 API / 着色器相关缓存，不是主要用户偏好。

### 9.5 Clausewitz / Jomini（Paradox）

```text
{DOCUMENTS}\Paradox Interactive\{GAME}\settings.txt
{DOCUMENTS}\Paradox Interactive\{GAME}\pdx_settings.txt
```

- 较老游戏常见 `settings.txt`，较新游戏常见 `pdx_settings.txt` 或同名格式变体。
- 常见概念包括 `size`（宽高）、`fullScreen`、`borderless`、`vsync`、刷新率、抗锯齿、阴影分辨率等，具体大小写与结构随游戏变化。
- Paradox 官方支持对 CK2 的排错明确提到 Documents 下的 `settings.txt`，参见[官方文章](https://support.paradoxplaza.com/hc/en-us/articles/360015902853-Crusader-Kings-2-crashing-at-Loading-Graphics)。
- Paradox Launcher 的设置不一定等于游戏进程最终使用的设置；以用户配置目录中生成文件的 mtime 和实际画面为准。

### 9.6 X-Ray（S.T.A.L.K.E.R. 系列与衍生项目）

先读取游戏根目录的 `fsgame.ltx`：

```text
$app_data_root$=...|...|<实际目录>
```

然后在解析后的 app data 根目录寻找：

```text
user.ltx
```

常见键：`vid_mode`、`rs_fullscreen`、`rs_v_sync`、`r__renderer`、`r1_*`、`r2_*`、`r3_*`、`r4_*`。原版、Steam/GOG 版、Anomaly/GAMMA 等整合版的 `$app_data_root$` 可完全不同，因此**解析 `fsgame.ltx` 比猜 Documents 路径可靠**。

### 9.7 Minecraft Java Edition

```text
{当前实例游戏目录}\options.txt
```

默认实例目录通常是：

```text
%APPDATA%\.minecraft\options.txt
```

[`options.txt`](https://minecraft.wiki/w/Options.txt) 保存游戏菜单中的设置。常见字段包括 `fullscreen`、`graphicsMode`、`renderDistance`、`simulationDistance`、`maxFps`、`enableVsync`、`fov`；字段和值会随版本迁移。

第三方启动器可为每个实例指定独立游戏目录。OptiFine、Sodium/Iris 等模组还会在 `optionsof.txt` 或 `config\*.json` 中保存额外图形项，不能只备份原版 `options.txt`。

## 10. 图形字段语义字典

字段名不存在跨游戏统一标准。程序识别时应使用“同义词组 + 原始类型 + 上下文”，不要仅按一个键名匹配。

| 设置概念 | 常见字段片段 | 典型风险 |
|:---|:---|:---|
| 输出分辨率 | `width`, `height`, `ResolutionSizeX/Y`, `iSize W/H`, `defaultres` | 无边框模式可能忽略；宽高要成对修改 |
| 窗口模式 | `fullscreen`, `borderless`, `windowMode`, `displayMode` | `0/1/2` 的含义各引擎不同，禁止跨引擎套映射 |
| 显示器 | `monitor`, `display`, `output`, `DisplayName`, `adapter` | 编号通常从 0 或 1 开始，取决于游戏 |
| 刷新率 | `refreshRate`, `numerator/denominator` | 可能采用分数表示，如 60000/1000 |
| VSync | `vsync`, `iPresentInterval`, `SyncInterval` | 有些值表示每 N 次垂直刷新，不只是布尔值 |
| 帧率上限 | `fpsLimit`, `FrameRateLimit`, `maxFps` | `0` 可能表示无限、自动或禁用，先看原值 |
| 画质预设 | `preset`, `quality`, `graphicsQuality`, `sg.*Quality` | 数字大小和档位名称不统一 |
| 内部渲染比例 | `resolutionScale`, `screenPercentage`, `viewportScale` | 可能是 0～1、小数百分比或 10～200 |
| 抗锯齿 | `AA`, `antiAliasing`, `TAA`, `MSAA`, `FXAA` | 方法与质量经常是两个字段 |
| 纹理 | `textureQuality`, `mipBias`, `streamingPool` | 主要影响显存；过高可能卡顿或贴图缺失 |
| 阴影 | `shadowQuality`, `shadowResolution`, `shadowDistance` | 通常同时影响 GPU、CPU 和显存 |
| 视距 / LOD | `viewDistance`, `lodScale`, `objectDistance` | 超范围值可能造成 CPU 瓶颈或物体闪烁 |
| 后处理 | `postProcess`, `motionBlur`, `depthOfField`, `bloom`, `filmGrain` | 常可独立关闭，不等同于总画质 |
| 环境光遮蔽 | `AO`, `SSAO`, `HBAO`, `GTAO` | 名称可能指算法，也可能指质量档位 |
| 光线追踪 | `rayTracing`, `RT`, `pathTracing` | 依赖 GPU、驱动和渲染 API；强开可能无法启动 |
| 超分辨率 | `DLSS`, `FSR`, `XeSS`, `upscaler`, `superResolution` | “模式”和“质量”通常分开；游戏可能验证硬件能力 |
| 帧生成 | `frameGeneration`, `DLSSG`, `FSRFG` | 依赖 API、驱动、硬件及低延迟设置 |
| 渲染 API | `DX11`, `DX12`, `D3D12`, `Vulkan`, `TargetPlatform`, `graphicsAPI` | 错误 API 是启动黑屏 / 崩溃的高发原因 |
| HDR | `HDR`, `paperWhite`, `peakBrightness` | 同时依赖 Windows HDR、显示器和色彩格式 |

## 11. 如何确认哪个配置真正生效

### 11.1 可靠验证流程

1. **退出游戏和启动器**，记录候选文件的大小、mtime 和哈希；注册表候选先导出。
2. 启动游戏，只改一个容易识别且低风险的设置，例如窗口模式或 `1920×1080 → 1600×900`。
3. 在游戏菜单中点“应用”，正常退出；不要直接结束进程。
4. 比较前后文件与注册表。刚发生对应变化的目标是强证据。
5. 打开目标，确认新值能与刚改的设置对应，而不是仅凭 mtime 下结论。
6. 再启动一次，检查设置是否保留；保留才说明写入与读取链路一致。

如果有条件，使用 Process Monitor 过滤游戏进程的 `CreateFile`、`WriteFile`、`RegSetValue`，这是比静态猜路径更可靠的办法。

### 11.2 自动识别程序的置信度建议

| 证据 | 建议权重 |
|:---|:---|
| 进程实际写入且字段值与菜单修改一致 | 极高 |
| 文件位于已知引擎路径，文件名和字段都匹配 | 高 |
| 仅文件名匹配，但位置和字段不匹配 | 低 |
| 仅位于游戏目录且名称含 `config` | 很低 |
| 文件是项目默认、缓存或安装包内资源 | 不应判为当前用户配置 |

候选结果至少记录：`path`、`storage_type`（file/registry）、`source`、`engine`、`evidence`、`exists`、`mtime`、`format`、`confidence`，不要只返回一个字符串路径。

## 12. 安全修改与恢复

### 12.1 修改前

1. 正常退出游戏及其启动器、模组管理器和云同步进程。
2. 复制原文件为带时间戳的 `.bak`；注册表使用“导出”保存 `.reg`。
3. 记录启动参数，因为启动参数可能持续覆盖配置文件。
4. 优先使用游戏内菜单；手工编辑只用于菜单无法启动、选项缺失或明确调优。

### 12.2 按格式修改

- **INI / CFG / LTX**：保留 section、键名大小写、编码和换行；注意重复键可能由最后一个或第一个生效。
- **JSON**：保持字段类型；标准 JSON 不允许注释和尾逗号。不要把数字改成带引号字符串。
- **XML**：保持单一根节点和成对标签；不要破坏 `<`、`>`、`&` 转义。
- **注册表**：只编辑已确认的游戏子键，保留 `REG_DWORD` / `REG_SZ` 等类型；不要删除整个 `HKCU\Software` 分支。
- **二进制**：除非有对应版本的解析器和校验规则，否则不要十六进制硬改。

不要长期把配置设为只读。只读可以用于短期诊断“是谁覆盖了设置”，但会阻止合法保存，也可能造成启动器反复校准、云同步冲突或游戏报错。

### 12.3 黑屏 / 无法启动时的恢复顺序

1. 移除最近添加的启动参数、`autoexec.cfg` 或覆盖文件。
2. 恢复备份；没有备份则把当前用户配置**重命名**为 `.bad`，让游戏重新生成，先不要永久删除。
3. 使用引擎或游戏支持的窗口化 / 安全参数：
   - UE：`-ResX=1280 -ResY=720 -Windowed`
   - Unity：`-screen-width 1280 -screen-height 720 -screen-fullscreen 0`
   - Godot：`--windowed --resolution 1280x720`
   - Source：`-autoconfig` 或 `-windowed -w 1280 -h 720`
   - GTA V：`-safemode` 或 `-useMinimumSettings`
4. 若刚切换 DX12 / Vulkan 后失败，回到此前能工作的渲染 API。
5. 最后才验证游戏文件；平台的“验证完整性”通常不会重置 AppData、Documents 或注册表中的用户配置。

## 13. 发行渠道、破解 / 便携版与云同步

- Steam、Epic、GOG 使用同一 Windows 构建时，图形配置通常相同，因为它主要由游戏引擎负责，而不是商店 API。
- 这不是绝对规则：不同商店可能发布不同分支；Xbox / WinGDK 构建可使用 `WinGDK` 或 Packages 容器；启动器也可能注入不同参数。
- Steam 模拟器通常只改变 Steam API、账号和云存档位置，不会自动改变 UE/Unity 的图形配置路径。
- 便携整合包、沙盒工具或自定义启动器可能重定向 AppData、设置 `-userdir` 类参数、创建目录连接，或把配置设为只读。
- 云同步可能同步“设置”而不只是存档，导致旧电脑的配置覆盖新电脑。排错时临时停用云同步，并保留两边备份。
- Windows 的 Documents 可被 OneDrive 重定向。程序不得假定它一定是 `%USERPROFILE%\Documents`。
- 老游戏写入 `Program Files` 失败时可能被重定向到 `%LOCALAPPDATA%\VirtualStore\...`，应把它作为回退候选。

## 14. 常见误判

- 看见 `GameUserSettings.ini` 就认定是 UE 当前配置：它也可能是游戏安装目录里的默认模板。
- 把 Unity 的 `boot.config` 当成玩家画质配置：它通常属于构建启动数据。
- 把 UE `sg.ResolutionQuality` 当作 0～4 档位：它通常是渲染百分比。
- 跨引擎复用 `FullscreenMode=0/1/2`：枚举含义不通用。
- 只改 `ResolutionSizeX/Y`，没有同步 `LastUserConfirmedResolutionSizeX/Y`，导致 UE 游戏回退。
- 只检查文件，不检查 Unity PlayerPrefs 注册表。
- 把着色器缓存、GPU benchmark、硬件指纹当成玩家偏好。
- 游戏仍在运行时编辑，退出时又被内存中的旧值覆盖。
- 用只读属性“防覆盖”，结果游戏无法保存其他合法设置。
- 直接复制别人的整份配置：其中可能包含不支持的 API、显示器编号、GPU 标识、超范围 CVar 或可执行的控制台命令。
- 看到两个配置就删除一个：DX11/DX12 分支、不同 Steam 账号或 Legacy/Enhanced 版本可能各自维护配置。

## 15. 资料来源与可信度

### A 级：引擎 / 厂商官方资料

- Epic Games：[UGameUserSettings API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/GameFramework/UGameUserSettings)、[Scalability Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine)、[Command-Line Arguments](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-command-line-arguments-reference)
- Unity：[PlayerPrefs](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/PlayerPrefs.html)、[Player command-line arguments](https://docs.unity3d.com/6000.3/Documentation/Manual/PlayerCommandLineArguments.html)、[FullScreenMode](https://docs.unity3d.com/ScriptReference/FullScreenMode.html)
- Godot：[Data paths](https://docs.godotengine.org/en/stable/tutorials/io/data_paths.html)、[ConfigFile](https://docs.godotengine.org/en/stable/classes/class_configfile.html)、[ProjectSettings](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html)、[Command line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)
- CRYENGINE：[Console Variables & Config Files](https://docs.cryengine.com/pages/viewpage.action?pageId=25535264)
- Valve Developer Community：[CFG](https://developer.valvesoftware.com/wiki/CFG)、[VCFG](https://developer.valvesoftware.com/wiki/VCFG)、[Command Line Options](https://developer.valvesoftware.com/wiki/Command_Line_Options)
- Microsoft：[KNOWNFOLDERID](https://learn.microsoft.com/en-us/windows/win32/shell/knownfolderid)、[Store and retrieve settings and app data](https://learn.microsoft.com/en-us/windows/apps/design/app-settings/store-and-retrieve-app-data)
- Bethesda：[FalloutPrefs.ini 分辨率说明](https://help.bethesda.net/app/answers/detail/a_id/9997/)
- Rockstar：[RDR2 `system.xml` 排错](https://support.rockstargames.com/articles/2MQafAtBWiOUJrPDLx5I2U/err-gfx-init-error-when-launching-red-dead-redemption-2-on-pc)、[GTA V 命令行参数](https://support.rockstargames.com/articles/2VjbVziQCiTiiVhDbmnexc/full-list-of-command-line-parameters-for-grand-theft-auto-v-on-pc)、[GTA V `pc_settings.bin` 重置](https://support.rockstargames.com/articles/4dfq6KRAlNvJgIxLLZGY4q/being-asked-to-accept-terms-of-service-and-recalibrate-settings-each-time-grand-theft-auto-v-on-pc-is-launched)
- CD PROJEKT RED：[Cyberpunk 2077 干净安装与本地目录说明](https://support.cdprojektred.com/en/cyberpunk/pc/sp-technical/issue/2233/how-do-i-perform-a-clean-install-of-the-game)
- Paradox：[CK2 `settings.txt` 排错](https://support.paradoxplaza.com/hc/en-us/articles/360015902853-Crusader-Kings-2-crashing-at-Loading-Graphics)

### B 级：维护良好的项目 Wiki / 可交叉验证资料

- Minecraft Wiki：[`options.txt`](https://minecraft.wiki/w/Options.txt)
- [PCGamingWiki](https://www.pcgamingwiki.com/)：用于核对具体游戏的版本化路径；应进入对应游戏页面复核，不把单个页面推广成整套引擎规则

### 使用原则

1. A 级来源可证明引擎机制或厂商指定路径，但仍需考虑游戏版本。
2. B 级来源适合补具体游戏路径，应至少与本机生成文件或第二来源交叉验证。
3. 论坛帖子、整合包说明和“低配优化配置”只作为线索，不直接作为规则真值。
4. 对任何准备自动修改的字段，最终证据应是“游戏菜单修改 → 文件 / 注册表发生对应变化 → 重启后仍生效”。
