# Unity 游戏 Mod 安装教程（BepInEx 篇）

> 本教程基于 BepInEx 官方文档（GitHub: BepInEx/BepInEx）和官方发布页整理，适合零基础玩家。
>
> **重要**：BepInEx 5.4.x 是当前正式稳定/LTS 线；BepInEx 6 仍属于预发布 / Bleeding Edge 生态。Mono 与 IL2CPP 是重要判断条件，但**游戏和插件页面要求优先**，不要只凭后端强行选择版本。
>
> **通用性边界（必读）**：BepInEx 6 的下载渠道、文件布局、运行时目录、代理 DLL 名称和管理器部署方式会随构建变化。使用官方完整包并保留其目录结构；不要把某个游戏的文件名或管理器行为照搬到其他游戏。
>
> **安全边界**：不要在带反作弊、公共服务器、竞技或未明确允许的联机环境使用注入式插件；即使是单人模式，也应遵守游戏条款和 Mod 作者许可。
>
> 如果你用的是 MelonLoader 而不是 BepInEx，请看同目录下的《MelonLoader.md》。

---

## 一、前置知识

### 1.1 BepInEx 是什么

BepInEx（Bepis Injector Extensible）是 Unity / XNA 游戏的插件框架，和 MelonLoader 是同类产品——它注入游戏进程，提供一个"可插拔区域"，让 Mod（BepInEx 里叫**插件 Plugin**）能修改游戏行为。

和 MelonLoader 的主要区别：

| 对比项 | BepInEx | MelonLoader |
|--------|---------|-------------|
| 定位 | 插件框架，结构更规整 | 通用 Mod 加载器 |
| Mod 存放目录 | `BepInEx/plugins/` | `Mods/` |
| 配置文件位置 | `BepInEx/config/` | `UserData/` |
| 日志 | `BepInEx/LogOutput.*`（单个文件） | `MelonLoader/Logs/`（多份滚动） |
| 典型游戏 | Valheim、Risk of Rain 2、Subnautica、戴森球计划 | VRChat、漫漫长夜、BTD6 |
| IL2Cpp 的运行时 | 当前 IL2Cpp 构建通常附带所需运行时；必须完整保留官方包，具体目录以当前构建为准 | 需要系统装 .NET 6.0 Desktop Runtime |

> **选哪个由游戏社区决定**：查你要玩的游戏的 Mod 页面，看 Mod 要求的是 BepInEx 还是 MelonLoader，两个框架**不能混装**（都抢注入入口）。

### 1.2 Mono 和 IL2Cpp 是什么

Unity 游戏编译时有两种代码后端：

| 后端 | 特点 | 对 Mod 的影响 |
|------|------|--------------|
| **Mono** | 游戏代码以 C# 程序集（`.dll`）形式保存在 `游戏_Data/Managed/` 里 | 常见为 BepInEx 5.4.x LTS；最终按游戏与插件要求选择 |
| **IL2Cpp** | 游戏代码被编译成原生 C++（`GameAssembly.dll`） | 通常需要游戏社区指定的 BepInEx 6 / 预发布构建；首次启动可能生成互操作文件并耗时较长 |

**怎么判断游戏是哪种？** 打开游戏根目录：

- 根目录或 `游戏名_Data/` 里有 `GameAssembly.dll`（几十 MB 的大文件）→ **IL2Cpp**
- 没有 `GameAssembly.dll`，且 `游戏名_Data/Managed/` 里有大量 `.dll` → **Mono**

> 注意：`GameAssembly.dll` 是 Windows Unity IL2CPP 的强线索；若没有它但 `Managed/` 中有大量游戏程序集，通常是 Mono。遇到特殊启动器、改版或不确定情况时，应以游戏社区和 Mod Requirements 的后端说明为准。

### 1.3 Mod 管理器 vs 加载框架

两者不是替代关系，是**配合关系**：

```
┌────────────────────────────────────┐
│  Mod 管理器（r2modman、GMM 等）      │  ← 图形界面，帮你下载/安装/管理 Mod
├────────────────────────────────────┤
│  加载框架（BepInEx）                 │  ← 底层引擎，实际运行 Mod 代码
├────────────────────────────────────┤
│  Unity 游戏                         │  ← 游戏本体
└────────────────────────────────────┘
```

> BepInEx 生态最常用的管理器是 **r2modman / Thunderstore Mod Manager**（Valheim、Risk of Rain 2 等社区标配），GMM 也支持部分游戏。

### 1.4 BepInEx 的版本选择（5.4.x vs 6.x）

版本选择应同时看**游戏后端、Mod/插件要求和社区当前维护方案**：

| | 5.4.x（正式稳定 / LTS） | 6.x（预发布 / Bleeding Edge） |
|---|---|---|
| 常见场景 | 大量 Unity Mono 游戏社区仍使用这一正式稳定线 | IL2CPP 游戏常需要这一线；当前也存在 Mono 的预发布构建 |
| 状态 | 长期维护，以修复为主 | API、文件布局和下载方式仍可能变化 |
| 插件兼容性 | 使用为 BepInEx 5 编写的插件 | 不应假设 BepInEx 5 插件可直接运行；严格看插件要求 |
| 最终依据 | 游戏与插件的 Requirements | 游戏与插件的 Requirements、指定的 Bleeding Edge 构建 |

> 不要把“Mono 必须 5、IL2CPP 只能 6”当作脱离 Mod 生态的绝对规则。对普通用户而言，最安全的做法是使用该游戏社区明确写出的 BepInEx 版本和插件版本。


---

## 二、安装 BepInEx

### 2.1 系统要求

| 要求 | 说明 |
|------|------|
| 操作系统 | 以当前游戏、BepInEx 构建和依赖运行时的系统要求为准；建议使用仍受支持的 Windows 版本 |
| Unity 游戏 | Steam、Epic 或独立安装版均可 |
| 管理员权限 | 写入游戏目录时需要 |
| .NET 运行时 | 使用官方指定的完整构建；IL2CPP 预发布包通常会携带所需运行时/文件，实际布局以当前包为准，勿手动删减 |

### 2.2 下载

**先选对操作系统包：**

| 包名示例 | 适用环境 | 你应看到的文件类型 |
|---|---|---|
| `BepInEx_win_x64_5.4.23.5.zip` | Windows 64 位游戏 | Windows 注入文件，例如 `winhttp.dll`、`doorstop_config.ini` |
| `BepInEx_win_x86_5.4.23.5.zip` | Windows 32 位游戏 | Windows x86 对应文件 |
| `BepInEx_linux_x64_5.4.23.5.zip` | 原生 Linux、部分 Steam Deck/Proton 方案 | Linux 的 Doorstop/启动文件，不会提供 Windows 的 `winhttp.dll`；按 Linux/Proton 文档启动 |

你当前下载的 `BepInEx_linux_x64_5.4.23.5.zip` 是 Linux 包。如果你是在 Windows 上运行游戏，请改下载 `BepInEx_win_x64_5.4.23.5.zip`；不要把 Linux 包里的文件补到 Windows 包中混用。

BepInEx 通常通过解压安装，但下载来源随版本线不同：

1. **BepInEx 5.4.x（正式稳定 / LTS）**：从 [官方 Releases](https://github.com/BepInEx/BepInEx/releases) 下载与游戏位数匹配的 Windows 或 Linux 正式包。
2. **BepInEx 6 / IL2CPP / 预发布需求**：先查看 Mod/游戏社区给出的准确构建号，再从官方 **Bleeding Edge** 渠道取得对应构建；不要假设常规 Releases 页面一定提供可用的 6.x 包。
3. 选择与实际运行环境和游戏 EXE 位数相同的包；不确定是原生 Linux、Proton 还是 Windows 时，先查游戏启动方式和社区说明。

### 2.3 手动安装（以下步骤适用于 Windows 包）

如果你使用 Linux/Proton 包，请按该包内的 Linux 启动脚本和官方说明操作，不要期待 `winhttp.dll` 或 Windows 的 `doorstop_config.ini`。

1. **确保游戏已关闭**
2. 解压下载的压缩包，把**压缩包内的全部内容**复制到游戏根目录（和游戏 `.exe` 同级）
3. 复制完成后，游戏根目录应该多出这些：

| 文件/文件夹 | 作用 |
|-------------|------|
| `BepInEx/` 文件夹 | 框架本体（含 core、plugins 等子目录） |
| `winhttp.dll` | **代理 DLL**（Doorstop 注入器），游戏启动时加载它来注入 BepInEx |
| `doorstop_config.ini` | Doorstop 注入配置文件 |
| `.doorstop_version` 等零星文件 | Doorstop 版本标记，不用管 |

4. **启动一次游戏再关闭**——BepInEx 会自动补全 `config/`、`cache/` 等目录和配置文件

> **正确性自检**：解压后如果发现多套了一层文件夹（如 `游戏根目录/BepInEx_win_x64_5.4.23.5/BepInEx/...`），说明结构错了——要把里面那一层的文件**上移**到游戏根目录，让 `BepInEx/`、`winhttp.dll` 和 `游戏.exe` 并排。

### 2.4 安装后的完整目录结构

安装完成并首次启动后（标注了版本差异）：

```
游戏根目录/
├── Game.exe              ← 游戏原本就有
├── Game_Data/            ← 游戏原本就有
├── winhttp.dll           ← 新增：Doorstop 代理 DLL，负责注入（5/6 都有）
├── doorstop_config.ini   ← 新增：注入配置（5/6 都有）
├── dotnet/               ← 部分预发布 / IL2CPP 构建可能附带；以当前包实际内容为准
└── BepInEx/              ← 新增：框架主目录（全部家当都在这里面）
    ├── core/             ← 框架核心程序集（5/6 都有）
    ├── plugins/          ← 你下载的 Mod 放这里（5/6 都有）
    ├── patchers/         ← 预加载补丁，比插件更早运行（5/6 都有）
    ├── config/           ← 配置文件：BepInEx.cfg + 各插件的 .cfg（首次启动后生成）
    ├── cache/            ← 程序集元数据缓存，加速启动（自动生成）
    ├── interop/          ← IL2Cpp 生成的互操作程序集（仅 6.x IL2Cpp）
    └── LogOutput.*     ← 运行日志（排查问题看这个文件）
```

> **和 MelonLoader 的结构差异**：BepInEx 把所有东西都收进 `BepInEx/` 一个文件夹里（配置、日志、插件全在里面），不像 MelonLoader 在游戏根目录摊开好多个文件夹。更整洁，也好备份。

### 2.5 各文件/文件夹的详细作用与注入原理

**BepInEx 是怎么进游戏的（Doorstop 注入器）**：

- **DLL 代理层**：Windows 加载 EXE 时先在 EXE 所在目录找依赖 DLL，找不到才去 `System32`。Unity 游戏通常会加载系统的 `winhttp.dll`（Windows HTTP Services API），BepInEx 把 **UnityDoorstop** 伪装成 `winhttp.dll` 放到 EXE 同级目录，就会被系统优先加载。加载后 Doorstop 会自己去 `System32` 拿真正的 `winhttp.dll` 转发所有调用，游戏无感知。
- **接管 .NET 运行时启动**：Doorstop 和 MelonLoader 的关键区别在这里——它不直接跑 Mod 代码，而是在 Unity 初始化 Mono/CoreCLR 之前挂钩子。等运行时起来，Doorstop 把控制权交给 `BepInEx/core/` 里的 **BepInEx.Preloader**，让它成为进程里第一段用户级托管代码。这也是为什么 BepInEx 能在很早的阶段做 IL 修改。
- **配置文件驱动**：Doorstop 的行为由 `doorstop_config.ini` 决定——`enabled` 开关整条注入链，`target_assembly` 指向要加载的 preloader DLL。所以禁用 BepInEx 只要把 `enabled` 改为 `false`，链在 Doorstop 那一层就被自己断开了。
- **Mono vs IL2CPP 的分叉**：Mono 游戏本身跑在 Mono 运行时上，Mod DLL 可以直接和游戏程序集混在一起加载；IL2CPP 游戏没有 Mono，Doorstop 会先加载 BepInEx 自带的一份 CoreCLR/.NET 运行时（`dotnet/` 目录），再由 Il2CppInterop 生成 C# 桥接层（`BepInEx/interop/`），Mod 才能调用 IL2CPP 里的游戏函数。所以 v6/IL2CPP 构建的完整包不能删 `dotnet/` 或 `interop/`，删了就没有运行时了。

**patchers/ 和 plugins/ 是两条时机不同的加载路径**：

| 目录 | 加载时机 | 干什么 | 适用 |
|---|---|---|---|
| `BepInEx/patchers/` | **游戏程序集被 JIT 编译之前**（Preloader 阶段） | 用 Mono.Cecil 直接改写游戏 DLL 的 IL 字节码：改方法体、加字段、替换类型 | 深度补丁 Mod，作者明确要求才用 |
| `BepInEx/plugins/` | 游戏启动后、Unity 场景加载完毕（Chainloader 阶段） | 用 HarmonyX 挂运行时钩子，或调用游戏 API 改行为 | **绝大多数普通插件都在这里** |

两个目录**不能互换**：patcher 扔进 `plugins/` 会因为时机太晚失效（游戏 IL 已经编译），plugin 扔进 `patchers/` 会因为跑得太早导致游戏 API 还没准备好而崩。

**各文件夹一览**：

| 名称 | 作用 | 注意 |
|------|------|------|
| `winhttp.dll` | UnityDoorstop 代理 DLL，负责注入（见上文原理） | 文件名与机制以当前包/游戏要求为准；不要随意替换。 |
| `doorstop_config.ini` | Doorstop 注入配置 | 通过 `enabled = false` 可临时禁用整个 BepInEx；`target_assembly` 一般不改。 |
| `BepInEx/core/` | 框架核心（Preloader、Chainloader、Harmony 等） | 不要删除或混入其他版本文件。 |
| `BepInEx/plugins/` | 普通插件目录，Chainloader 阶段加载 | 按插件作者提供的结构合并，可以有子文件夹。 |
| `BepInEx/patchers/` | Preloader 阶段的 IL 补丁 | 只有作者明确要求时才使用，不要把普通插件放进来。 |
| `BepInEx/config/` | BepInEx 与插件配置 | 文件名以首次运行生成的实际文件为准。 |
| `BepInEx/cache/` | 缓存 | 出现疑难问题时可在备份后按官方/社区建议重建。 |
| `BepInEx/interop/`、运行时目录 | 预发布或 IL2CPP 构建可能包含 | 不要删减；以当前官方构建和游戏要求为准。 |
| `BepInEx/LogOutput.*` | 运行日志 | 不同版本可能是 `.txt` 或 `.log`，以实际生成文件为准。 |

### 2.6 版本差异速查表（5.4.x vs 6.x）

| 项目 | 5.4.x 正式稳定版 | 6.x 预发布 / Bleeding Edge |
|------|------------------|----------------------------|
| 常见使用场景 | 大量 Unity Mono 游戏的稳定生态 | IL2CPP 游戏常见，也存在 Mono 预发布构建 |
| 状态 | LTS，主要接收修复 | 仍可能调整 API、文件布局和下载渠道 |
| 运行时/interop | 以正式包实际内容为准 | 使用完整官方构建，不要手动删运行时或 interop 文件 |
| 首次启动 | 生成配置和日志 | IL2CPP 常需生成额外文件，耗时因游戏而异 |
| 插件兼容 | 使用 BepInEx 5 插件 | 必须看作者是否明确支持 v6，不能假设 v5 插件可用 |

> 选择版本时先看 Mod/插件 Requirements，再看游戏后端；需要 v6 时优先使用游戏社区指定的官方 Bleeding Edge 构建。

### 2.7 特殊情况：注入失败

先确认压缩包是否完整、文件是否位于真实游戏 EXE 同级目录、日志是否生成，以及游戏/社区是否要求专用代理 DLL。**只有在游戏社区或 Mod 作者明确验证某个代理 DLL 名称时**，才按其说明替换 `winhttp.dll`；每次只改一个并保留原文件备份。

### 2.8 首次启动

正常启动游戏，观察现象：

**Mono 游戏（5.4.x）：**
- 游戏正常启动，`BepInEx/config/` 里生成 `BepInEx.cfg`
- **默认不弹控制台窗口**（BepInEx 和 MelonLoader 相反，控制台默认关闭，开启方法见 4.2）
- 验证成功的标志：`BepInEx/LogOutput.*` 文件存在且内容有 `BepInEx 5.4.x.x` 加载记录

**IL2Cpp 游戏（6.x）：**
- 首次启动用 Cpp2IL 生成互操作程序集到 `BepInEx/interop/`，**可能需要几分钟**，**千万不要强制关闭**
- 只在首次启动和游戏更新后发生，之后正常

---

## 三、安装插件（Mod）

### 3.1 在哪里下载插件

- **Thunderstore**（thunderstore.io）：BepInEx 生态的主阵地（Valheim、RoR2 等）
- **Nexus Mods**（nexusmods.com）：最大的 Mod 站点
- **GitHub**：很多作者直接发布
- **各游戏贴吧/QQ 群/Discord**：中文 Mod 常在这里分享

> **安全第一**：插件是可执行代码，只从可信来源下载。
>
> **下载前先看 Requirements**：确认插件要求 BepInEx 5 还是 6，和你装的一致。

### 3.2 插件压缩包里都有什么

```
某个插件压缩包/
├── plugins/             ← 作者按 BepInEx 结构打包好的（整体拖进 BepInEx/ 即可）
│   ├── ModName.dll
│   └── ModName/         ← 插件自己的资源子文件夹
├── patchers/            ← 少数深度修改型 Mod 才有
├── README.md            ← 说明文档（先看看）
├── icon.png             ← 管理器图标（可忽略）
└── manifest.json        ← Thunderstore 管理器元数据（可忽略）
```

> BepInEx 生态的 Mod 大多按 `BepInEx/` 内部结构打包，解压后对照合并即可，比"到处捡 DLL"省心。

### 3.3 什么该放进 plugins/

**核心原则：插件运行需要的都放，说明文档类的不放。**

| 文件类型 | 放不放 | 原因 |
|----------|--------|------|
| 插件本体 `.dll` | **必须放** | BepInEx 只加载 DLL |
| 插件附带的 `.json` / `.cfg` / `.xml` | **必须放** | 插件运行时会读取 |
| 依赖的辅助 `.dll` | **必须放** | 缺了会报"找不到程序集" |
| 资源文件（`.bundle`、图片、音频、插件自己的子文件夹） | **必须放** | 按压缩包原结构保留 |
| `README`、说明 `.txt`、截图 | 不放 | 给人看的，先读一遍再决定 |
| `manifest.json`、`icon.png` | 不放 | Thunderstore 管理器元数据 |

### 3.4 和 MelonLoader 的一个重要区别：plugins/ 可以有子文件夹

| 规则 | 说明 |
|------|------|
| **BepInEx 会递归扫描 `plugins/` 的子文件夹** | 插件 DLL 放在 `plugins/某插件/` 里也能被加载 |
| 推荐做法 | 每个插件一个子文件夹（`plugins/MapTweaks/MapTweaks.dll`），整洁易管理 |
| 对比 MelonLoader | 两个加载器的扫描与目录习惯可能不同；无论使用哪个，都应保留 Mod 作者要求的结构，不要仅凭另一框架的经验强制平铺或删子目录。 |

### 3.5 手动安装步骤

**第一步：解压并阅读说明**

确认：插件支持的游戏版本、要求 BepInEx 5 还是 6、有无前置依赖插件（很多插件依赖 BepInEx 配置管理器类的公共插件）。

**第二步：按结构合并**

压缩包里有 `plugins/` → 整体合并进游戏的 `BepInEx/plugins/`
压缩包里有 `patchers/` → 整体合并进 `BepInEx/patchers/`
压缩包是散装 DLL → 在 `plugins/` 下建个以插件名命名的子文件夹，放进去

```
BepInEx/plugins/
├── ValheimPlus/
│   ├── ValheimPlus.dll
│   └── valheim_plus.cfg
└── SomeOtherMod/
    └── SomeOtherMod.dll
```

**第三步：启动游戏验证**

打开 `BepInEx/LogOutput.*`，搜索插件名：
- 出现 `Loading [插件名 x.x.x]` → 成功
- 出现 `Error` / `Skipping` → 看第五章排查

### 3.6 使用 r2modman / Thunderstore Mod Manager

对受支持游戏，管理器可创建 Profile、安装依赖并从 Profile 启动 Modded 游戏。具体目录、部署机制、是否直接写入游戏目录以及导出迁移方式，随管理器版本和游戏适配而变化。

建议流程：

1. 先确认目标游戏在当前管理器版本中受支持。
2. 创建 Profile，安装 Mod 后检查其依赖和版本要求。
3. 使用“Start Modded”启动，并通过实际 `LogOutput.*` 验证加载。
4. 迁移时优先使用管理器当前提供的 Profile 导出功能；不要在不了解其目录/链接机制时手动移动管理器维护的文件。

> GMM 或其他管理器的能力应以其当前官方说明为准，不能假定它们都会使用同一种目录或部署方式。

---

## 四、管理与配置

### 4.1 修改插件设置

插件的配置统一在 `BepInEx/config/` 下：

| 配置 | 位置 | 说明 |
|------|------|------|
| BepInEx 自身设置 | `BepInEx/config/BepInEx.cfg` | 框架级设置 |
| 各插件设置 | `BepInEx/config/插件GUID.cfg` | 插件**首次运行后自动生成**，文件名是插件的 GUID（如 `com.author.pluginname.cfg`） |

格式是 `选项名 = 值` 的 ini 风格，用记事本编辑，**重启游戏**生效。

> 很多 BepInEx 游戏会配一个"游戏内配置管理器"插件（如 ConfigurationManager），按 **F1** 呼出，可以**在游戏里实时改配置**不用重启——BepInEx 生态的一大便利。

### 4.2 开启 BepInEx 控制台（默认是关的）

编辑 `BepInEx/config/BepInEx.cfg`：

```ini
[Logging.Console]
Enabled = true        # 改为 true，启动游戏时弹出黑色控制台窗口

[Logging.Disk]
WriteUnityLog = false
```

### 4.3 卸载/禁用

| 需求 | 操作 |
|------|------|
| 卸载某个插件 | 删除 `BepInEx/plugins/` 里对应的 DLL/子文件夹，以及 `config/` 里它的 `.cfg`（可选） |
| 临时禁用整个 BepInEx | 编辑 `doorstop_config.ini`，把 `enabled = true` 改为 `false`（游戏恢复原版，改回来即恢复） |
| 完全卸载 BepInEx | 删除 `BepInEx/`、`winhttp.dll`、`doorstop_config.ini`、`.doorstop_version`（6.x 还有 `dotnet/`） |

### 4.4 更新

| 更新对象 | 方法 |
|----------|------|
| BepInEx | 先备份 `plugins`、`config` 和 Profile；按当前官方升级说明或游戏社区要求更新。跨大版本、文件异常或排错时，优先做干净安装，再逐步放回插件与配置。 |
| 插件 | 按作者更新说明替换完整文件组；保留旧 `.cfg` 前先备份并检查配置是否兼容。 |
| 游戏大版本更新后 | 插件可能失效；先禁用/移走插件验证原版，再等待明确适配。 |

---

## 五、常见问题排查

### Q1：游戏启动完全没反应，连 LogOutput.* 都没生成

注入失败。检查：
1. `winhttp.dll` 和 `doorstop_config.ini` 是否在游戏根目录（和 exe 同级，没多套一层文件夹）
2. 杀毒软件是否误删/拦截了 `winhttp.dll`，加白名单
3. 仅当该游戏社区或 Mod 作者明确验证某个代理 DLL 名称时，再按其说明调整代理 DLL；不要随机改名
4. 检查游戏位数：x64 框架配 32 位游戏会注入失败

### Q2：日志生成了，但插件没加载 / 游戏崩溃

1. 打开 `BepInEx/LogOutput.*`，搜 `Error` 和 `Skipping`
2. **检查版本线是否匹配**：BepInEx 5 的插件在 6.x 上不工作，反之亦然（日志会有明显提示）
3. 缺前置依赖：日志会写缺哪个 GUID 的插件，去 Thunderstore 搜来装上
4. 二分法排查：把 `plugins/` 里的插件移出一半，逐步定位问题插件

### Q3：插件装了但游戏里没有效果

- 看 `LogOutput.*` 确认插件真的加载了（有 `Loading [xxx]` 行）
- 很多插件要按热键呼出菜单（如 F1），看插件说明
- 检查 `config/` 里该插件的 `.cfg`，功能开关可能是默认关闭的

### Q4：日志报 "Could not load file or assembly"

缺依赖 DLL。检查插件压缩包里的辅助 DLL 是否都放进了 `plugins/`，以及是否缺某个公共前置插件。

### Q5：IL2Cpp 游戏（6.x）首次启动卡很久

正常现象，`interop/` 程序集生成需要几分钟。超过 15 分钟无变化再检查磁盘空间重启游戏。

### Q6：BepInEx 和 MelonLoader 能同时装吗？

**不建议**。两者都要抢注入入口（`winhttp.dll` / `version.dll` 会冲突），同时装大概率只有一个生效甚至都启动不了。一个游戏只选一个框架——选哪个看游戏 Mod 社区的主流。

---

## 六、流程总结

```
① 判断游戏后端、查看游戏社区与插件 Requirements
       ↓
② 选择社区明确要求的 BepInEx 版本与构建
   （常见：Mono 社区使用 5.4 LTS；IL2CPP 常使用指定的 v6 / Bleeding Edge 构建）
       ↓
③ 将官方完整包解压到真实游戏 EXE 同级目录
       ↓
④ 首次启动 → 生成 config/ 和 LogOutput.*
   （IL2CPP / 预发布构建可能需要额外生成文件）
       ↓
⑤ 按插件作者结构合并到 BepInEx/plugins/，确认前置依赖
       ↓
⑥ 启动游戏 → 查看 LogOutput.* 验证
       ↓
⑦ 调参数 → 以实际生成的 BepInEx/config 配置和插件说明为准
```

> 核心口诀：**Requirements 优先 → 使用完整官方包 → 保留插件结构 → 看日志验证。**

---

## 参考资料

- BepInEx 官方仓库：https://github.com/BepInEx/BepInEx
- BepInEx 正式发布页（5.4.x LTS）：https://github.com/BepInEx/BepInEx/releases
- BepInEx Mono 安装指南：https://docs.bepinex.dev/master/articles/user_guide/installation/unity_mono.html
- BepInEx IL2CPP 安装指南（Bleeding Edge 构建）：https://docs.bepinex.dev/master/articles/user_guide/installation/unity_il2cpp.html
- BepInEx 升级指南：https://docs.bepinex.dev/articles/user_guide/upgrading.html
- Thunderstore：https://thunderstore.io
- r2modman 管理器：https://github.com/ebkr/r2modmanPlus
