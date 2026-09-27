# R 星游戏 Mod 安装指南（RAGE / ScriptHook / LML 篇）

> 本指南面向 PC 单机 Mod。重点覆盖《荒野大镖客 2》（RDR2）和《侠盗猎车手 V》（GTA V），并说明其他采用 Rockstar 技术体系的游戏应如何判断工具。
>
> **先记住总规则：RAGE 是游戏引擎，不是统一的 Mod 加载器。** Rockstar 游戏的 Mod 可能使用 ASI、Script Hook、Lenny’s Mod Loader、OpenIV、ScriptHookVDotNet、RagePluginHook 或游戏专用工具；安装目录必须以具体游戏、Mod 页面和工具包内 README 为准。

---

## 一、R 星游戏使用什么引擎？

Rockstar 的现代大型游戏主要使用自研的 **RAGE（Rockstar Advanced Game Engine）**。它不是 Unity，也不是 Unreal Engine。

| 游戏 | 常见技术归类 | Mod 生态示例 |
|---|---|---|
| 《侠盗猎车手 IV》 | RAGE 家族 | ASI、Script Hook、OpenIV、游戏专用插件 |
| 《荒野大镖客：救赎》 | RAGE 家族 | 以具体 PC 版本和 Mod 作者说明为准 |
| 《马克思·佩恩 3》 | RAGE 家族 | 版本相关的脚本/资源工具 |
| 《侠盗猎车手 V》 | RAGE 家族 | Script Hook V、OpenIV、ScriptHookVDotNet、RagePluginHook |
| 《荒野大镖客 2》 | RAGE 家族 | ScriptHookRDR2、ASI Loader、Lenny’s Mod Loader |
| 较早的 GTA 游戏 | 多数属于更早的技术体系 | 不要套用 GTA V 的工具和目录 |

> 引擎名称只能帮助你缩小范围，不能直接决定 Mod 的安装方法。即使两款游戏都使用 RAGE，它们的脚本接口、资源格式、加载器和 Mod 目录也可能完全不同。

---

## 二、先判断 Mod 属于哪一类

| Mod 类型 | 常见文件/特征 | 常见工具 | 典型安装位置 |
|---|---|---|---|
| ASI 脚本插件 | `.asi`，有时带 `.dll`、`.ini` | Script Hook + ASI Loader | 游戏根目录或作者指定目录 |
| RDR2 资源 Mod | `lml` 文件夹、`stream`、`replace`、`add` 等 | Lenny’s Mod Loader（LML） | RDR2 根目录的 `lml` 结构 |
| GTA V RPF 资源 Mod | 修改 `update.rpf`、`common.rpf`、`x64*.rpf` 等 | OpenIV + `mods` 镜像目录 | GTA V 根目录的 `mods` 镜像路径 |
| GTA V .NET 脚本 | `.dll`、`.cs`、`.vb` 或脚本包 | ScriptHookVDotNet | GTA V 的 `scripts` 目录，按作者要求安装 |
| GTA V RPH 插件 | RAGE Plugin Hook 插件，通常是 `.dll` | RagePluginHook | 当前 RPH 包/插件说明指定的插件目录，常见为 `C#Plugins` |
| 官方平台 Mod | 创意工坊、官方 Mod 管理器等 | 游戏官方工具 | 按官方流程，不要额外安装 Script Hook |

### 工具之间不能混为一谈

- **ScriptHookV / ScriptHookRDR2**：提供游戏原生脚本接口，并配合 ASI Loader 加载 `.asi` 插件。
- **ASI Loader**：负责让 ASI 插件被加载；常见文件名是 `dinput8.dll`，但以当前工具包为准。不要同时保留多个互相冲突的 ASI Loader；如果官方发行包要求移除旧的 `dsound.dll`，按其 README 处理。
- **Lenny’s Mod Loader**：主要用于 RDR2 的资源 Mod；LML-only Mod 不一定需要 ScriptHookRDR2。
- **OpenIV**：主要用于查看/管理 GTA V 等游戏的资源归档；它不是所有 R 星游戏通用的脚本加载器。
- **ScriptHookVDotNet**：GTA V 的 .NET 脚本插件，建立在 Script Hook V 的 ASI 插件机制之上。
- **RagePluginHook**：GTA V 的另一套插件框架，常用于警察、执法和复杂 .NET 插件生态；不要把 RPH 插件直接丢进 ScriptHookVDotNet 的 `scripts` 目录。

---

## 三、通用准备工作

### 3.1 找到游戏根目录

游戏根目录就是放着主游戏 EXE 的目录：

```text
GTA5.exe       ← GTA V
RDR2.exe       ← 荒野大镖客 2
```

查找方式：

- Steam：游戏属性 → 已安装文件 → 浏览本地文件
- Epic Games：库中游戏菜单 → 管理 → 打开安装位置
- Rockstar Games Launcher：设置或游戏菜单中的安装位置

不要把 Mod 文件放到 Steam/Rockstar/Epic 启动器目录，也不要只看快捷方式所在目录。

### 3.2 先备份和验证

1. 关闭游戏、启动器和正在运行的 Mod 管理器。
2. 记录游戏版本、Mod 版本和工具版本。
3. 安装大型资源 Mod 前先让 Steam/Epic/Rockstar 客户端验证一次原版文件。
4. 优先使用镜像目录或 Mod Loader，避免直接改写原始 RPF/游戏文件。
5. 一次只安装一个基础工具和一个 Mod，确认能启动后再继续添加。

### 3.3 单机安全边界

- Script Hook V 官方说明明确表示它不支持 GTA Online；进入多人模式时会关闭游戏。[Script Hook V 说明](https://www.dev-c.com/gtav/scripthookv/)
- Script Hook RDR2 官方说明明确表示它不支持 Red Dead Online；进入多人模式时会关闭游戏。[Script Hook RDR2 说明](https://www.dev-c.com/rdr2/scripthookrdr2/)
- 不要安装所谓 Online 解锁、Online 修改、绕过检测或绕过封禁的工具。
- 不要在 GTA Online、Red Dead Online、公共服务器、竞技环境或不明确允许 Mod 的联机环境使用注入式 Mod。
- 如果启动器发现文件被修改，先移除 Mod Loader/ASI 文件并使用官方客户端验证原版。

---

## 四、《荒野大镖客 2》Mod 安装

RDR2 的常见单机 Mod 分为两条主线：**ASI 脚本**和 **Lenny’s Mod Loader 资源 Mod**。具体 Mod 可能只需要其中一条，也可能两条都需要。

### 4.1 ScriptHookRDR2 + ASI 插件

Script Hook RDR2 官方页面给出的基本关系是：

- `ScriptHookRDR2.dll` 放到与 `RDR2.exe` 同一个根目录。
- ASI Loader 用来加载 `.asi` 插件；该发行包通常会附带 `dinput8.dll`，也可以按工具说明使用其他兼容 ASI Loader。
- `NativeTrainer.asi` 是示例训练器，不是 Script Hook 本体的必需文件。

典型目录如下，**以当前下载包内 README 为准**：

```text
Red Dead Redemption 2/
├── RDR2.exe
├── ScriptHookRDR2.dll
├── dinput8.dll              ← ASI Loader，名称以发行包为准
├── NativeTrainer.asi        ← 可选示例训练器
└── 其他作者提供的 .asi/.dll/.ini
```

安装步骤：

1. 从 Script Hook RDR2 的可信发布页确认当前版本支持的游戏补丁。
2. 关闭 RDR2 和 Rockstar Games Launcher。
3. 将工具包中要求的文件复制到 `RDR2.exe` 所在目录。
4. 需要安装 ASI 插件时，再把插件作者提供的完整文件组放到作者指定位置。
5. 启动**故事模式**，查看工具日志或 Mod 功能是否生效。

> RDR2 更新后，旧版 ScriptHookRDR2 可能失效。不要因为文件名相同就覆盖或混用不同版本的 Script Hook。

### 4.2 Lenny’s Mod Loader（LML）

LML 主要解决 RDR2 资源替换和新增资源的加载问题。它与 ScriptHookRDR2 不是同一个东西：

- 只要求 LML 的资源 Mod，不一定需要 ScriptHookRDR2。
- 需要 `.asi` 脚本的 Mod，才按该 Mod 要求安装 ScriptHookRDR2 和 ASI Loader。
- LML 安装包可能同时包含 `lml`、Mod Manager、ASI 支持文件或其他组件；不要只从压缩包里随便抽取一个文件。

常见结构示意：

```text
Red Dead Redemption 2/
├── RDR2.exe
├── lml/                     ← LML 的工作目录
│   ├── mod 名称/            ← 由 Mod 作者说明具体放法
│   └── ...
├── ModManager/              ← 某些发行包带有的管理工具，可选
└── 其他 LML 包要求的文件      ← 文件名与位置以当前 LML README 为准
```

安装流程：

1. 下载 LML 后，先阅读压缩包中的 README 和当前 Mod 页的 Requirements。
2. 按 LML 包内说明将完整的工作目录复制到 RDR2 根目录。
3. 按 Mod 页面要求把 Mod 文件夹放到 `lml` 下指定位置；不要把 LML Mod 改装成普通 `.asi`。
4. 如果使用 Mod Manager，先确认它显示的游戏根目录是放置 `RDR2.exe` 的目录。
5. 一次启用少量 Mod；多个 Mod 修改同一资源时，优先按作者说明处理冲突。

> 常见 Mod 页面会要求把完整 Mod 文件夹放进 `lml`，但不同 Mod 的目录层级和文件名可能不同。LML 的“有 `lml` 文件夹”不等于每个 Mod 都能直接丢到 `lml` 根目录。

### 4.3 RDR2 的排错顺序

1. 移走所有第三方 Mod，只保留 LML 或 Script Hook 基础组件。
2. 确认 `RDR2.exe`、`ScriptHookRDR2.dll`、ASI Loader 的位于同一正确根目录。
3. 确认工具版本支持当前 RDR2 补丁。
4. 逐个恢复 Mod；先恢复 LML 资源 Mod，再恢复 ASI 脚本。
5. 查看 Mod 作者要求的前置工具，不要把 GTA V 的 ScriptHookV 或 OpenIV 文件混进 RDR2。

---

## 五、《侠盗猎车手 V》Mod 安装

GTA V 的 Mod 常见为三类：ASI/脚本、OpenIV RPF 资源和 .NET/RPH 插件。GTA V Legacy/Enhanced、游戏版本和 Mod 目标版本可能不同，安装前一定核对 Mod 页面。

### 5.1 Script Hook V + ASI Loader

Script Hook V 的基本安装结构通常是：

```text
Grand Theft Auto V/
├── GTA5.exe
├── ScriptHookV.dll
├── dinput8.dll              ← ASI Loader，若当前发行包附带
├── NativeTrainer.asi        ← 可选
└── 其他 .asi 插件及其配置
```

Script Hook V 官方说明的关键点：

- `ScriptHookV.dll` 放在 `GTA5.exe` 所在目录。
- 要加载 ASI 插件，必须有 ASI Loader；当前发行包常带 `dinput8.dll`。
- `NativeTrainer.asi` 是可选示例插件。
- Script Hook V 不用于 GTA Online。

不要把 `ScriptHookRDR2.dll`、RDR2 的 `dinput8.dll` 配置或 LML 文件混入 GTA V。

### 5.2 OpenIV 的 `mods` 镜像目录

OpenIV 的 `mods` 目录用于让修改尽量留在副本中，而不是直接改原始 RPF。基本思路：

```text
Grand Theft Auto V/
├── GTA5.exe
├── mods/
│   ├── update/
│   │   └── update.rpf
│   ├── common.rpf
│   └── ...与原版路径对应的 RPF 副本
└── 原版 update/、x64*.rpf 等文件
```

常见步骤：

1. 安装 OpenIV 并选择正确的 GTA V 安装路径。
2. 在 OpenIV 的 ASI Manager 中按提示安装 ASI Loader 与 OpenIV.ASI；具体组件以当前 OpenIV 版本为准。
3. 在 GTA V 根目录建立小写的 `mods` 文件夹。
4. 将要修改的原始 RPF 按**相同相对路径**复制到 `mods` 中，再在 `mods` 副本上安装资源 Mod。
5. 不要直接编辑原始 RPF；修改前保留备份。

例如，原版路径是：

```text
GTA V/update/update.rpf
```

对应的 Mod 副本通常是：

```text
GTA V/mods/update/update.rpf
```

OpenIV 的 `mods` 机制和具体 RPF 路径可参考：[OpenIV mods 文件夹说明](https://openiv.com/?p=1132)。

### 5.3 ScriptHookVDotNet 脚本

ScriptHookVDotNet 是 GTA V 的 ASI 插件，可以运行 .NET 语言编写的脚本。其官方说明支持编译程序集，也支持放入 `scripts` 文件夹的 C# / VB 源脚本。[ScriptHookVDotNet 官方仓库](https://github.com/scripthookvdotnet/scripthookvdotnet) / [Getting Started](https://github.com/scripthookvdotnet/scripthookvdotnet/wiki/Getting-Started)

典型结构：

```text
Grand Theft Auto V/
├── ScriptHookV.dll
├── dinput8.dll
├── ScriptHookVDotNet.asi
├── ScriptHookVDotNet*.dll       ← 按当前发行包要求
└── scripts/
    ├── Example.dll              ← .NET 脚本示例
    ├── Example.cs               ← 作者明确支持时才放
    └── Example.ini/json         ← 按作者说明放置
```

安装原则：

- 先安装 Script Hook V 和 ASI Loader。
- ScriptHookVDotNet 官方项目还要求 Script Hook V、.NET Framework 4.8 或更高版本，以及受支持的 Microsoft Visual C++ 运行库；按当前项目 Requirements 检查这些依赖。
- 保留 ScriptHookVDotNet 发行包的完整文件，不要只复制一个 DLL；同一版本的 `.asi` 与 API DLL 应成套更新。
- Mod 作者要求放入 `scripts` 的文件才放入该目录；配置位置以作者说明为准。
- ScriptHookVDotNet 插件、RagePluginHook 插件和普通 ASI 插件不是同一种格式，不要混放。

### 5.4 RagePluginHook（RPH）

RagePluginHook 是 GTA V 的另一套插件框架，常用于 LSPDFR 等 RPH 生态。它不是 ScriptHookVDotNet，也不是 Script Hook V 的替代 DLL。

安装时：

1. 从 [RagePluginHook 官方文档](https://ragepluginhook.net/RPH2PreDoc/) 或目标插件的 Requirements 获取与游戏版本匹配的 RPH。
2. 关闭游戏，将 RPH 发行包按其 README 放到 GTA V 根目录。
3. 把 RPH 插件放到当前 RPH 文档指定的插件目录；官方文档使用过 `C#Plugins` 这一目录名称，具体以当前版本为准。
4. 先启动 RPH 或按插件作者说明启动 GTA V，再查看 RPH 日志。
5. 安装 LSPDFR 等大型插件时，优先使用其完整安装说明，不要只复制一个 DLL。

> 一个 Mod 如果明确要求 RagePluginHook，就不要用 ScriptHookVDotNet 或仅靠 Script Hook V 猜测替代；它们的 API、启动方式和插件目录不同。

---

## 六、GTA IV、L.A. Noire 和其他 R 星游戏

不要把 GTA V/RDR2 的文件直接复制到其他 R 星游戏。安装前按以下顺序确认：

1. 游戏的准确版本、平台和补丁号。
2. Mod 页面写明的加载器和前置工具。
3. 该游戏对应版本的 Script Hook/ASI Loader 是否仍被维护。
4. 资源 Mod 是修改 RPF、使用专用 Loader，还是使用官方 Mod 系统。
5. 是否明确只支持单机。

`RAGE` 只说明引擎家族，不代表 GTA V 的 ScriptHookV、RDR2 的 ScriptHookRDR2、LML 或 OpenIV 可以互换。

---

## 七、常见问题

### Q1：Mod 没有生效

- 确认安装的是正确游戏版本和正确工具。
- 确认文件放在真正的游戏根目录，而不是启动器目录。
- 检查 Mod 是否需要 Script Hook、ASI Loader、LML、OpenIV.ASI、ScriptHookVDotNet 或 RPH。
- 保留作者提供的目录层级和配套文件。
- 一次只启用一个 Mod，查看日志，再逐个添加。

### Q2：游戏启动就闪退

1. 移走所有 Mod，只保留原版，使用官方客户端验证文件。
2. 禁用或移除 ASI Loader / Script Hook，确认游戏能否原版启动。
3. 核对工具版本是否支持当前游戏补丁。
4. 检查 Mod 是否同时安装了两个互相冲突的 Loader。
5. 查看 Script Hook、LML、RPH 或 Mod 自己的日志。

### Q3：游戏更新后 Mod 全部失效

这通常是版本兼容问题：

- 等 Script Hook 或 Mod 作者发布支持当前补丁的版本。
- 不要用旧版本 DLL 强行覆盖新版本工具。
- 在等待适配期间移除第三方 Loader，使用原版游戏。

### Q4：如何恢复原版

- 关闭游戏和启动器。
- 按当前工具 README 删除或移出对应的 Loader、ASI、脚本和 Mod 文件。
- 对 GTA V，优先保留/删除 `mods` 副本，不要删除原版 RPF。
- 使用游戏平台的文件验证功能恢复被直接修改的原版文件。
- 重新启动前确认 Online 目录没有第三方 Mod 文件。

### Q5：可以装到 Online 吗？

**不要这样做。** 本指南只针对单机故事模式。Script Hook V 和 Script Hook RDR2 的官方说明都明确不支持对应 Online 模式；不要寻找绕过这一限制的补丁或工具。

---

## 八、安装流程总结

```text
① 确认游戏与版本：RDR2、GTA V、GTA IV 的工具不能混用
       ↓
② 阅读 Mod 页面 Requirements
   判断它需要 ASI、Script Hook、LML、OpenIV、ScriptHookVDotNet 还是 RPH
       ↓
③ 关闭游戏，找到真正的游戏根目录
       ↓
④ 先安装对应基础 Loader，并用日志验证
       ↓
⑤ 按 Mod 作者提供的完整目录结构安装一个 Mod
       ↓
⑥ 只在单机故事模式测试
       ↓
⑦ 游戏更新后先禁用 Mod，等待工具和 Mod 适配
```

> 核心口诀：**RAGE 不是加载器；游戏版本优先；工具不能混用；单机测试；日志排错；不要碰 Online。**

---

## 参考资料

- [Script Hook V（AB Software Development）](https://www.dev-c.com/gtav/scripthookv/)
- [Script Hook RDR2（AB Software Development）](https://www.dev-c.com/rdr2/scripthookrdr2/)
- [Lenny’s Mod Loader](https://www.lcpdfr.com/lml/index/)
- [OpenIV mods 文件夹说明](https://openiv.com/?p=1132)
- [ScriptHookVDotNet 官方仓库](https://github.com/scripthookvdotnet/scripthookvdotnet)
- [ScriptHookVDotNet Getting Started](https://github.com/scripthookvdotnet/scripthookvdotnet/wiki/Getting-Started)
- [RagePluginHook 官方文档](https://ragepluginhook.net/RPH2PreDoc/)
- [Epic：Pak 挂载 API（用于理解资源包不是统一 Mod Loader）](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/PakFile/FPakPlatformFile/Mount)

*本指南依据公开资料整理；工具版本、游戏补丁和 Mod 作者要求可能变化，实际安装以当前发行包 README 与目标 Mod 页面为准。*
