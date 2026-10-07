# Unity 游戏 Mod 安装教程

> 本教程基于 MelonLoader 官方文档（GitHub: LavaGang/MelonLoader）和官方 Wiki（melonwiki.xyz）整理，适合零基础玩家。
>
> **重要**：MelonLoader 有旧版 0.5.x 与当前 0.6/0.7 系列，目录和依赖会随版本变化；最终应以**游戏社区、Mod 下载页与当前发布包**要求为准，不是越新越好。
>
> **通用性边界（必读）**：`Mods/`、`Plugins/`、`UserData/`、`UserLibs/` 的具体内容、配置文件位置、代理 DLL 名称和管理器部署方式都可能因版本、游戏与 Mod 而不同。保留作者压缩包的运行时目录结构；不要只抽取 DLL，也不要把其他游戏的路径照搬。
>
> **平台说明**：本指南的 `version.dll`、`dobby.dll` 和 Windows 游戏目录示例针对 Windows 包。MelonLoader 也有 Linux/Proton 等构建，但其启动文件和运行方式不同；使用 Linux 包时按当前发布包和官方文档操作，不要期待 Windows 文件一定存在。

---

## 一、前置知识

### 1.1 Mod 加载框架是什么

Mod 加载框架是一个"中间人"，它注入到游戏进程中，负责加载玩家写的 Mod 代码，让 Mod 能修改游戏行为。没有它，你下载的 Mod 无法生效。

Unity 游戏最主流的两个框架：

| 框架 | 特点 |
|------|------|
| **MelonLoader** | 通用型加载器，同时支持 Mono 和 IL2Cpp 两种 Unity 后端，社区活跃 |
| **BepInEx** | 另一套常见插件框架，许多游戏社区指定使用它 |

本教程以 **MelonLoader** 为例，因为它是目前最广泛使用的方案。

### 1.2 Mono 和 IL2Cpp 是什么

Unity 游戏编译时有两种代码后端，决定了 Mod 的安装难度：

| 后端 | 特点 | 对 Mod 的影响 |
|------|------|--------------|
| **Mono** | 游戏代码以 C# 程序集（`.dll`）形式保存在 `游戏_Data/Managed/` 里 | 安装简单，Mod 直接可用 |
| **IL2Cpp** | 游戏代码被编译成原生 C++（`GameAssembly.dll`），看不到 C# 文件 | 需要 MelonLoader 首次启动时"还原"出 C# 接口，耗时较长，且需要安装 .NET 6.0 Desktop Runtime |

**IL2Cpp 为什么要"还原"？** Unity 的 IL2Cpp 编译器把 C# 源码全部转成 C++ 再编译成原生代码，塞进 `GameAssembly.dll`；运行时靠一份元数据（`global-metadata.dat`）在这堆 C++ 里定位类和方法。Mod 用 C# 写，想调用游戏函数就得反着从元数据推断出对应的 C# 类型和方法签名，生成一份"代理程序集"给 Mod 引用——首次启动的那几分钟就是在做这件事。新版 MelonLoader 用 Il2CppInterop、旧版用 UnhollowerBaseLib 完成这一步，也是它需要 .NET 6 Desktop Runtime 的原因。

**怎么判断游戏是哪种？** 打开游戏根目录：

- 根目录或 `游戏名_Data/` 里有 `GameAssembly.dll`（通常是较大的文件）→ **Windows Unity IL2Cpp 的强线索**
- 没有 `GameAssembly.dll`，且 `游戏名_Data/Managed/` 里有大量游戏程序集 → **通常是 Mono**

> 遇到特殊启动器、改版或不确定情况时，以游戏社区和 Mod Requirements 的后端说明为准。

### 1.3 Mod 管理器 vs 加载框架

两者不是替代关系，是**配合关系**：

```
┌────────────────────────────────────┐
│  Mod 管理器（GMM、r2modman 等）      │  ← 图形界面，帮你下载/安装/管理 Mod
├────────────────────────────────────┤
│  加载框架（MelonLoader）             │  ← 底层引擎，实际运行 Mod 代码
├────────────────────────────────────┤
│  Unity 游戏                         │  ← 游戏本体
└────────────────────────────────────┘
```

- 你用管理器装 Mod → 管理器帮你配置好底层框架 + 把 Mod 文件放到正确位置
- 你手动装 Mod → 需要自己装框架 + 自己放文件

### 1.4 MelonLoader 的版本选择（新版 vs 旧版）

MelonLoader 分两个时代，**用哪个版本由游戏社区决定，不是越新越好**：

| | 旧版 0.5.x | 新版 0.6 / 0.7 |
|---|---|---|
| 状态 | 老游戏的 Mod 生态多基于此（如《漫漫长夜》社区用 0.5.7） | 当前官方最新线 |
| Mod 兼容性 | 只兼容为它编写的 Mod | 只兼容为它编写的 Mod |
| 判断依据 | Mod 下载页的 "Requirements" 会写明 | 同左 |

> **选错版本的后果**：可能导致 Mod 无法加载或报错。安装前先看 Mod 页面要求；若使用 GMM 等管理器，也要在部署后核对它实际安装的加载器版本。

---

## 二、安装 MelonLoader

### 2.1 系统要求

| 要求 | 说明 |
|------|------|
| 操作系统 | 以当前游戏、MelonLoader 发布包和 .NET Runtime 的系统要求为准；建议使用仍受支持的 Windows 版本 |
| Unity 游戏 | Steam、Epic 或独立安装版均可 |
| 管理员权限 | 写入游戏目录时需要 |
| **.NET 6.0 Desktop Runtime** | **仅 IL2Cpp 游戏需要**（Windows 上安装器会自动帮你装） |

### 2.2 方法一：自动安装（推荐）

1. 从 GitHub 发布页（`github.com/LavaGang/MelonLoader/releases`）下载 `MelonLoader.Installer.exe`
2. 双击运行，点击 **SELECT**，找到游戏的 `.exe` 文件（比如 `Game.exe`）
3. 选择版本后点击 **INSTALL**（**版本按游戏社区要求选**，见 1.4；无特殊要求就选最新稳定版）
4. 等待进度条跑完，提示成功即可关闭

> **注意区分 x86 和 x64**：32 位游戏使用 x86 包，64 位游戏使用 x64 包。即使安装器显示自动检测结果，也应在安装前核对游戏社区或安装器显示的目标架构。

> **关于 .NET 6.0 Desktop Runtime**：Windows 上 Installer 检测到 IL2Cpp 游戏时会**自动下载安装**，无需手动操作；仅当自动下载失败（网络问题）时，才需要去微软官网手动装。Mono 游戏则完全不需要它。

### 2.3 方法二：手动安装

适合安装器失效或想完全掌控的情况：

1. **确保游戏已关闭**
2. 从 GitHub 发布页下载对应位数的压缩包（`MelonLoader.x64.zip` 或 `MelonLoader.x86.zip`）
3. 解压压缩包，把以下内容复制到游戏根目录（**新旧版不一样**）：

| 文件 | 旧版 0.5.x | 新版 0.6/0.7 |
|------|-----------|--------------|
| `MelonLoader/` 文件夹 | 复制 | 复制 |
| `version.dll` | 复制 | 复制 |
| `dobby.dll` | 压缩包里没有，不需要 | **必须复制**（漏了会启动失败） |

4. IL2Cpp 游戏：确认已安装 .NET 6.0 Desktop Runtime

> **为什么压缩包里没有 Mods/、Plugins/ 这些文件夹？**
> 压缩包只包含"让加载器跑起来的最小集"，其余目录是首次启动游戏时自动创建的（空文件夹），也可以自己手动建。按版本区分：
>
> | 目录 | 旧版 0.5.x | 新版 0.6/0.7 |
> |------|-----------|--------------|
> | `Mods/` | 自动创建 | 自动创建 |
> | `UserData/` | 自动创建 | 自动创建 |
> | `Plugins/` | 用到时才创建 | 自动创建 |
> | `UserLibs/` | 无此概念 | 自动创建 |
>
> 所以手动安装的完整流程是：复制文件 → 启动一次游戏 → 目录自动出现 → 再往 `Mods/` 里放 Mod。

### 2.4 安装后的完整目录结构

安装完成并首次启动后，游戏根目录是这样的（标注了新旧版差异）：

```
游戏根目录/
├── Game.exe              ← 游戏原本就有
├── Game_Data/            ← 游戏原本就有
├── version.dll           ← 新增：代理 DLL，负责注入 MelonLoader（新旧版都有）
├── dobby.dll             ← 新增：底层 Hook 库（仅新版，旧版没有）
├── MelonLoader/          ← 新增：加载器核心文件 + 日志
│   ├── Dependencies/     ← 加载器的依赖库
│   ├── Logs/             ← 运行日志（排查问题看这里）
│   └── Il2CppAssemblies/ ← IL2Cpp 生成的程序集（旧版 0.5.x 叫法；部分新版在 Managed/，也有版本直接整合进 net6/ 不单独生成此目录）
├── Plugins/              ← 新增：插件目录（新版自动建；旧版用到才建）
├── Mods/                 ← 新增：Mod 目录（放你下载的 Mod，新旧版都有）
├── UserLibs/             ← 新增：多个 Mod 共享的依赖库（仅新版）
└── UserData/             ← 新增：配置文件目录
    ├── Loader.cfg          ← MelonLoader 主配置（新版主用）
    └── MelonPreferences.cfg ← MelonLoader 主配置（旧版主用，新版也可能有）
```

### 2.5 各文件夹的详细作用与注入原理

**MelonLoader 是怎么进入游戏进程的（DLL 代理注入）**：

- **Windows 的 DLL 搜索顺序**：加载 EXE 时会按固定顺序找依赖 DLL——先在 EXE 所在目录里查，找不到再去 `System32` 之类的系统目录。绝大多数 Unity 游戏启动时都会加载系统的 `version.dll`（Windows 版本 API 的一部分）；MelonLoader 把自己伪装成 `version.dll` 放到 EXE 同级目录，就会被系统优先加载，游戏还以为拿到的是真的系统 DLL。
- **加载后转发调用**：MelonLoader 拿到执行权后再自己去 `System32` 加载真正的 `version.dll`，把游戏发来的所有 API 调用透传过去。游戏在完全正常运行的同时，MelonLoader 已经完成了框架注入，并开始扫 `Mods/`、`Plugins/`、`UserLibs/`。
- **位置敏感**：由于依赖 EXE 目录的搜索顺序，MelonLoader 必须放**真实游戏 EXE 同级**目录；放到启动器 EXE 目录、快捷方式所在目录或错误的 `Binaries` 上级都不生效——这是 Q1 排错时首先要核对的事。
- **换代理 DLL 名的本质**：2.7 里让你把 `version.dll` 改名为 `winhttp.dll`、`winmm.dll` 等，不是玄学，只是换一个游戏一定会加载的系统 DLL 当伪装身份。不同游戏依赖的系统 DLL 不同，所以要按社区/日志实际情况挑一个。
- **`dobby.dll`（新版）**：新版 MelonLoader 需要在游戏运行中动态改写函数入口（inline hook）来接管 Unity 内部方法，Dobby 就是负责改机器码的底层 hook 库。旧版 0.5.x 用的是另一套方案，所以没有这个文件。

**各文件夹一览**：

| 名称 | 作用 | 版本 | 你能做什么 |
|------|------|------|-----------|
| `version.dll` | 代理 DLL，负责 MelonLoader 注入（见上文原理） | 新旧都有 | 个别游戏需要改名为 `winhttp.dll` 等才能注入（见 2.7） |
| `dobby.dll` | 底层 Hook 库，MelonLoader 修改游戏函数靠它 | 仅新版 | 不要动 |
| `MelonLoader/` | 加载器本体、依赖库 | 新旧都有 | 不要动 |
| `MelonLoader/Logs/` | 每次启动的日志 | 新旧都有 | 出问题时打开最新的 `.log` 文件找错误信息 |
| `Plugins/` | **插件目录**，加载时机比 Mod 早 | 新旧都有（旧版用到才建） | 标注"Plugin"的 Mod 放这里（普通玩家很少用到） |
| `Mods/` | **Mod 目录**，在插件之后加载 | 新旧都有 | 下载的 Mod 放这里（重点，第三章详讲） |
| `UserLibs/` | **共享依赖库**，多个 Mod 共用的第三方 DLL | 仅新版 | Mod 说明里明确要求时才放 |
| `UserData/` | 所有配置文件的存放处 | 新旧都有 | 修改 Mod 参数调这里 |

### 2.6 版本差异速查表（旧版 0.5.x vs 新版 0.6/0.7）

汇总前文所有差异，方便对照自己的游戏目录：

| 项目 | 旧版 0.5.x | 新版 0.6/0.7 |
|------|-----------|--------------|
| `dobby.dll` | 没有（不需要） | 必需 |
| `UserLibs/` | 没有这个概念 | 有 |
| `Plugins/` | 用到时才创建 | 自动创建 |
| 主配置文件 | `UserData/MelonPreferences.cfg` | `UserData/Loader.cfg` |
| `MelonLoader/` 内部 | `Il2CppAssemblies/`、`net35/`、`net6/` | `Managed/` 等；部分版本只保留 `net35/`、`net6/` 等运行时目录，无独立程序集文件夹 |
| 典型游戏 | 《漫漫长夜》（社区用 0.5.7） | 多数新 Mod 生态 |

> 再强调一次：**版本由游戏社区与 Mod Requirements 决定**。管理器可能提供版本选择或部署功能，但不要假定它会自动匹配所有游戏和 Mod；安装后应查看实际版本与日志。

### 2.7 特殊情况：游戏不识别 version.dll

绝大多数游戏用默认的 `version.dll` 就能注入。个别游戏需要在启动时优先加载其他系统 DLL，这时把 `version.dll` **重命名**为以下任一名称即可：

```
winhttp.dll  winmm.dll  dinput.dll  dinput8.dll  dsound.dll
d3d8.dll  d3d9.dll  d3d11.dll  d3d12.dll  ddraw.dll  msacm32.dll
```

> 一般只有游戏完全无反应（控制台都不弹）时才需要尝试改名。逐个试，每次改完启动一次游戏。

### 2.8 首次启动

正常启动游戏，观察现象：

**Mono 游戏：**
- 弹出 MelonLoader 控制台窗口（黑色命令行窗口）→ 安装成功
- 首次启动略慢，生成 `UserData/` 下的配置文件（新版是 `Loader.cfg`，旧版是 `MelonPreferences.cfg`）

**IL2Cpp 游戏：**
- 首次启动会进行**程序集生成**（Assembly Generation），把游戏的 C++ 代码"还原"成 C# 接口
- 生成的文件位置：旧版 0.5.x 在 `MelonLoader/Il2CppAssemblies/`，新版通常在 `MelonLoader/Managed/` 等位置；**部分新版（如 0.6.x）可能不生成独立文件夹**，程序集直接整合进 `MelonLoader/net6/` 等运行时目录——找不到这两个文件夹是正常的，不影响功能
- 这个过程**可能需要几分钟**，启动画面会显示进度，**千万不要强制关闭**
- 只在首次启动和游戏更新后发生，之后就正常了

---

## 三、安装 Mod

### 3.1 在哪里下载 Mod

- **Nexus Mods**（nexusmods.com）：最大的 Mod 站点
- **Thunderstore**（thunderstore.io）：以 Unity 游戏 Mod 为主
- **GitHub**：很多 Mod 作者直接在 GitHub 发布
- **各游戏贴吧/QQ 群/Discord**：中文 Mod 常在这里分享

> **安全第一**：Mod 是可执行代码，只从可信来源下载。警惕"免费解锁付费内容"类 Mod，往往夹带恶意代码。
>
> **下载前先看 Requirements**：确认 Mod 要求的 MelonLoader 版本（0.5.x 还是 0.6+）和你装的一致。

### 3.2 Mod 压缩包里都有什么

下载的 Mod 压缩包通常包含这些东西：

```
某个Mod压缩包/
├── ModName.dll        ← Mod 本体（必需）
├── ModName.json       ← Mod 的配置文件（如果作者提供了，必需）
├── SomeLibrary.dll    ← Mod 依赖的辅助库（如果有，必需）
├── icon.png           ← 图标（管理器用，可忽略）
├── README.md          ← 说明文档（先看看，可能有特殊安装要求）
└── manifest.json      ← 管理器元数据（GMM/r2modman 用，可忽略）
```

### 3.3 什么该放进 `Mods/`

**核心原则：保留 Mod 作者提供的运行时文件和目录结构，README/发布页优先。** 通常 DLL 是入口文件，但资源、依赖和配置位置不一定都固定在 DLL 同级。

| 文件类型 | 常见处理方式 |
|----------|-------------|
| Mod 本体 `.dll` | 按作者要求放入 `Mods/` 或 `Plugins/`。 |
| 依赖 DLL、资源文件、子目录 | 通常需要保留；不要只抽取主 DLL。 |
| `.json` / `.cfg` / `.xml` | 有些 Mod 在同目录读取，有些会在 `UserData/` 或自身目录生成；保留作者提供的布局并看说明。 |
| `README`、说明、截图 | 先阅读；一般不影响运行，但不要据此擅自丢弃作者明确标记为必需的文件。 |
| `manifest.json`、图标 | 常为管理器元数据；若使用管理器导入，优先让管理器按其格式处理。 |

> 不要把“配置一定和 DLL 同目录”写成通用规则。对于不清楚的压缩包，最安全的做法是保留完整运行时结构，并按 Mod 作者的安装说明放置。

### 3.4 特殊目录的用法

| 情况 | 放哪 | 版本限制 |
|------|------|---------|
| Mod 页面明确写着 "This is a **Plugin**" 或 "put in Plugins folder" | `Plugins/` | 新旧版均可（旧版需先手动建文件夹） |
| Mod 说明写着 "put in **UserLibs**"（多个 Mod 共用的基础库） | `UserLibs/` | 仅新版，旧版没有这个概念（旧版把共享库也放 `Mods/`） |
| 其他一切普通 Mod | `Mods/` | 新旧版均可 |

> 不确定就查 Mod 的说明文档。**90% 的 Mod 都是放 `Mods/`。**

### 3.5 手动安装步骤

以解压 `BetterUI.zip` 为例：

**第一步：解压并阅读说明**

解压后先看看有没有 README/说明文档，确认：
- Mod 支持的游戏版本
- Mod 要求的 MelonLoader 版本（0.5.x 还是 0.6+）
- 有无前置依赖 Mod
- 放 `Mods/` 还是 `Plugins/`

**第二步：识别需要的文件**

```
解压结果/
├── BetterUI/
│   ├── BetterUI.dll       ← 放
│   ├── BetterUI.json      ← 放（配置文件）
│   └── 使用说明.txt        ← 不放
└── AnotherMod.dll         ← 放
```

**第三步：复制到 Mods/**

```
游戏根目录/Mods/
├── BetterUI.dll
├── BetterUI.json
└── AnotherMod.dll
```

> **重要**：不要在没有 Mod 作者说明时，强制把所有文件平铺到 `Mods/` 根目录或删除子文件夹。先保留压缩包的运行时结构；如果作者明确要求平铺，再平铺。安装后以 `MelonLoader/Logs/` 的加载或报错信息为准。

**第四步：启动游戏验证**

看 MelonLoader 控制台窗口：
- 出现 `[BetterUI] v1.2.3 loaded` 之类 → 成功
- 出现红色报错 → 看第五章排查

### 3.6 使用 Mod 管理器（以 GMM 为例）

管理器的功能、支持的游戏、部署目录和版本匹配策略会随产品版本变化，**不能把自动匹配或自动识别当作保证**。使用前先确认该游戏在 GMM 中是否被明确支持，并阅读其当前说明。

通常流程：

1. 添加或选择目标游戏的正确 `.exe`。
2. 若管理器提供 MelonLoader 安装选项，先核对它选择的版本是否符合 Mod 页面要求。
3. 导入 Mod 后，检查管理器显示的文件结构、前置依赖和部署状态。
4. 启动游戏后仍以 `MelonLoader/Logs/` 为准验证；失败时优先用管理器的导出/日志功能排查。

> 管理器与手动安装可以并存，但不要在不了解其 Profile、链接或独立目录机制时手动移动管理器维护的文件。

---

## 四、管理与配置

### 4.1 修改 Mod 设置

Mod 的配置有两个可能的位置：

| 位置 | 常见情况 |
|------|----------|
| Mod 自己的目录或作者指定的资源目录 | 有些 Mod 随包附带 JSON/资源并在运行时读取；保持作者结构。 |
| `UserData/` 或 Mod 首次生成的目录 | 许多 Mod 会生成 `.cfg`、偏好或数据文件；实际位置以日志和作者说明为准。 |

修改后是否需要重启、是否支持热重载，取决于 Mod 本身。

示例（MapTweaks.json）：

```json
{
  "overrideDrawingRange": true,
  "drawingRange": 10000,
  "autodrawEnabled": true,
  "autodrawDelay": 20
}
```

### 4.2 修改 MelonLoader 自身设置

配置文件在 `UserData/` 下，**文件名因版本而异**（需至少启动过一次游戏才会生成）：

| 版本 | 主配置文件 |
|------|-----------|
| 新版 0.6/0.7 | `UserData/Loader.cfg` |
| 旧版 0.5.x | `UserData/MelonPreferences.cfg` |

常见配置项（以新版 `Loader.cfg` 为例）：

```toml
[loader]
disable = false            # true = 完全禁用 MelonLoader（等于 --no-mods）
debug_mode = false         # 调试模式，开发 Mod 时才开

[console]
hide_console = false       # true = 不显示黑色控制台窗口
console_on_top = false     # 控制台窗口置顶

[logs]
max_logs = 10              # 日志文件保留数量
```

### 4.3 卸载/禁用 Mod

| 需求 | 操作 |
|------|------|
| 彻底卸载某个 Mod | 删除 `Mods/` 里对应的 `.dll` 及其配套 `.json` |
| 临时不加载所有 Mod | 游戏启动参数加 `--no-mods` |
| 完全卸载 MelonLoader（新版） | 删除 `version.dll`、`dobby.dll`、`MelonLoader/`；想清干净再删 `Mods/`、`Plugins/`、`UserData/`、`UserLibs/` |
| 完全卸载 MelonLoader（旧版） | 删除 `version.dll`、`MelonLoader/`（没有 `dobby.dll` 和 `UserLibs/`）；想清干净再删 `Mods/`、`Plugins/`、`UserData/` |

### 4.4 常用启动参数

在 Steam 游戏属性 → 启动选项，或游戏快捷方式的目标后面添加：

| 参数 | 作用 |
|------|------|
| `--no-mods` | 不加载任何 Mod（排查是不是 Mod 导致的问题） |
| `--melonloader.hideconsole` | 隐藏控制台窗口 |
| `--melonloader.debug` | 输出详细调试日志 |
| `--quitfix` | 修复某些游戏退出后进程残留的问题 |

### 4.5 更新

| 更新对象 | 方法 |
|----------|------|
| MelonLoader | 先备份 `Mods/`、`Plugins/`、`UserData/` 与日志；使用安装器或当前发布说明推荐的更新方式。跨 0.5.x 与 0.6/0.7 时，先确认所有 Mod 兼容性，必要时做干净安装。 |
| Mod | 按作者更新说明替换完整文件组，不要只覆盖 DLL；保留配置前先备份。 |
| 游戏大版本更新后 | Mod 可能失效；先用 `--no-mods` 验证原版，再等待 Mod 作者明确适配。 |

---

## 五、常见问题排查

### Q1：游戏启动没反应/闪退，控制台都不弹

1. 检查 `version.dll` 是否在（**新版**还要检查 `dobby.dll`，旧版没有这个文件）
2. IL2Cpp 游戏：确认装了 .NET 6.0 Desktop Runtime
3. 杀毒软件可能误删了 DLL，把游戏目录加入杀软白名单后重装
4. 只有游戏/Mod 社区明确验证该代理名时，才尝试把 `version.dll` 改为其他兼容代理 DLL 名称；每次只改一个并保留备份

### Q2：控制台弹了，但游戏崩溃

1. 启动参数加 `--no-mods`，能正常进游戏 → 某个 Mod 的问题
2. 二分法排查：把 `Mods/` 里的文件移出一半，逐个排除
3. 打开 `MelonLoader/Logs/` 里最新的日志，搜索 `Error` 或 `Exception`，能看到具体是哪个 Mod 报错
4. **检查 MelonLoader 版本是否和 Mod 要求一致**（0.5.x 的 Mod 在 0.6+ 上会报错，反之亦然）

### Q3：Mod 装了但没效果

- 确认作者要求的目录结构、DLL、资源和配置文件都完整保留；不要仅凭“必须在根目录”自行平铺
- 确认 Mod 版本支持当前游戏版本和 MelonLoader 版本
- 有些 Mod 需要按热键呼出菜单，看 Mod 说明和日志

### Q4：日志里报 "Could not load file or assembly"

缺少依赖。检查：
- Mod 的辅助 DLL 是否也放进 `Mods/` 了
- Mod 说明里是否要求某个前置 Mod（比如很多 Mod 依赖某个"Mod Helper"）
- **新版**：是否要求把共享库放进 `UserLibs/`（旧版没有 UserLibs，共享库放 `Mods/` 即可）

### Q5：IL2Cpp 游戏首次启动卡很久

正常现象。程序集生成需要几分钟，启动画面有进度条。如果超过 15 分钟无变化，检查磁盘空间后重启游戏重试。

### Q6：使用 GMM 还是手动安装？

- **想减少重复操作**：可使用受该游戏支持的管理器，但仍要核对加载器版本、Profile、依赖和日志。
- **需要深入排错**：手动安装更容易理解每个文件的位置与来源。

两种方式可以共存，但不要在不了解管理器 Profile、部署目录或链接机制时，手动移动它维护的文件。

---

## 六、流程总结

```
① 判断游戏后端（Mono / IL2Cpp）并查看游戏社区、Mod 页面要求的 MelonLoader 版本
       ↓
② 使用当前发布包/安装器按说明安装
   （手动安装时保留包内要求的 `MelonLoader/`、代理 DLL 与依赖文件）
       ↓
③ 首次启动游戏 → 查看 `MelonLoader/Logs/` 验证加载
   （IL2Cpp 首次可能需要生成程序集）
       ↓
④ 下载 Mod 压缩包，先看说明、版本与前置依赖
       ↓
⑤ 保留作者提供的运行时目录结构，按要求放入 `Mods/`、`Plugins/` 或其他指定目录
       ↓
⑥ 启动游戏 → 通过日志确认 Mod 已加载
       ↓
⑦ 调参数 → 以实际生成的 `UserData/` 配置与 Mod 说明为准
```

> 核心口诀：**Requirements 优先 → 使用完整发布包 → 保留 Mod 结构 → 用日志验证。**

---

## 参考资料

- MelonLoader 官方仓库：https://github.com/LavaGang/MelonLoader
- 官方 Wiki：https://melonwiki.xyz
- MelonLoader 安装器：https://github.com/LavaGang/MelonLoader.Installer
- .NET 6.0 Desktop Runtime 下载：https://dotnet.microsoft.com/download/dotnet/6.0
