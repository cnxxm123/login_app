# 贝塞斯达游戏 Mod 安装指南（Creation Engine 篇）

> 本指南面向贝塞斯达（Bethesda Game Studios）自研引擎的单机 RPG，覆盖：
>
> - **《上古卷轴 4：湮灭》** 及《上古卷轴 4：湮灭 重制版》
> - **《辐射 3》《辐射：新维加斯》** 
> - **《上古卷轴 5：天际》**（LE / SE / AE / VR）
> - **《辐射 4》**（含 Next-Gen 更新）
> - **《辐射 76》**
> - **《星空》**
>
> **重要**：这几款游戏底层的引擎虽然一脉相承，但**每一代都不是二进制兼容**——Skyrim LE 的 Mod 不能直接给 SE 用，SE 的 Mod 不能直接给 AE 用，更不能塞进 Starfield。工具（SKSE、F4SE、SFSE）、脚本扩展、BSA/BA2 归档版本都是**每代一套**。
>
> **总规则**：Mod 页面 Requirements 优先；游戏版本、脚本扩展版本、Mod 管理器 Profile 必须一起匹配。

---

## 一、先分清引擎世代

贝塞斯达的引擎是长期迭代的，社区口径通常这么分：

| 世代 | 游戏 | 引擎名称 | 插件格式 | 归档格式 | 脚本扩展 |
|---|---|---|---|---|---|
| Gamebryo 家族 | 《湮灭》《辐射 3》《新维加斯》 | Gamebryo / NetImmerse | `.esp` / `.esm` | `.bsa`（老版） | OBSE / FOSE / NVSE |
| Creation Engine 1 | 《上古卷轴 5》《辐射 4》《辐射 76》 | Creation Engine | `.esp` / `.esm` / `.esl`（SE+） | `.bsa`（Skyrim）/ `.ba2`（FO4+） | SKSE / SKSE64 / F4SE |
| Creation Engine 2 | 《星空》 | Creation Engine 2 | `.esm` + Plugins.txt | `.ba2` | SFSE |

《上古卷轴 4：湮灭 重制版》比较特殊：**它是 UE5 前端 + 原版 Gamebryo 后端跑数据**，Mod 生态仍然围绕原版 `.esp/.bsa` 和 OBSE 打转，UE5 只负责渲染。

---

## 二、前置知识

### 2.1 Plugin：`.esm` / `.esp` / `.esl` 的区别

Plugin 是贝塞斯达游戏的核心 Mod 单元——一份小型数据库，记录你要新增/修改/删除的记录（NPC、物品、任务、脚本）。

| 后缀 | 意思 | 加载顺序 | ID 空间 |
|---|---|---|---|
| `.esm`（Master File） | 主文件，游戏本体和大型 DLC 用；其他插件可以“依赖”它 | **最先加载** | 完整 24 位 FormID |
| `.esp`（Plugin） | 普通 Mod 插件 | 在所有 `.esm` 之后 | 完整 24 位，占一个 load order 位置 |
| `.esl`（Light Plugin，SE 之后） | 轻量插件（新版最多 4096 条新记录，Skyrim SE 1.6.1130 之前只能用 0x800-0xFFF 范围，实际上限 2048 条） | 排在 `.esm` 附近或专有位置 | 只占 12 位，多个 `.esl` 共享同一个 load order slot |

**Load Order（加载顺序）** 是这些插件加载的先后：**后加载的插件覆盖先加载的同名记录**。所以两个 Mod 都改了同一件铁匠铺武器时，谁排在后面谁生效——除非你手动做兼容 patch。

### 2.2 BSA / BA2：资源归档

- **BSA**（Bethesda Softworks Archive）：Skyrim 及之前用的归档格式，装贴图、模型、声音、脚本源码等散装资源。
- **BA2**（Bethesda Archive 2）：Fallout 4 引入，比 BSA 压缩更好、加载更快；Starfield 沿用。
- 命名规则：**BSA/BA2 会跟着同名的 `.esp/.esm` 一起加载**。例如 `MyMod.esp` + `MyMod - Textures.ba2` 一起放进 `Data/`，游戏加载插件时会自动挂载对应归档。
- 也可以走**散装文件**：把资源直接铺在 `Data/textures/`、`Data/meshes/` 之类目录，散装文件默认覆盖 BSA/BA2 里的同路径资源（前提是游戏的 `sResourceDataDirsFinal` 等设置允许，Skyrim SE 默认允许，Starfield 需要额外解锁）。

### 2.3 Data/ 目录

所有 Mod 最终都要落到游戏根目录下的 `Data/`：

```text
游戏根目录/
├── SkyrimSE.exe        （或 Fallout4.exe / Starfield.exe）
├── Data/
│   ├── Skyrim.esm       ← 游戏本体
│   ├── Update.esm
│   ├── SomeMod.esp      ← 你装的 Mod 插件
│   ├── SomeMod.bsa      ← 对应资源包
│   ├── textures/        ← 散装贴图
│   ├── meshes/          ← 散装模型
│   └── SKSE/            ← SKSE 插件（子目录）
└── SKSE64_loader.exe    ← 脚本扩展启动器（如果用 SKSE）
```

Mod 管理器（MO2）能做到「虚拟 Data 目录」——游戏看到 Data 里有 Mod，但硬盘上其实还是干净的原版。这是它比 Vortex 的核心优势之一，后面 4.1 讲。

---

## 三、原理：贝塞斯达 Mod 是怎么加载的

理清下面几层，后面所有安装步骤就都能对上号了：

```text
① 游戏 EXE 启动
     │
     │  可选：由 SKSE64_loader.exe / F4SE_loader.exe 之类的 loader 启动
     │        （loader 通过 CreateProcess + DLL Injection 把脚本扩展 DLL 注入进游戏进程）
     ▼
② 引擎读 Plugins.txt 决定要加载哪些插件、顺序如何
     │
     │  Plugins.txt 位于 %LocalAppData%\Skyrim Special Edition\Plugins.txt 之类的位置
     ▼
③ 按 Load Order 顺序加载 .esm → .esp → .esl
     │
     │  每加载一个插件，同名 BSA/BA2 也一起挂载
     ▼
④ 引擎构建最终的记录表：后加载覆盖先加载（Rule of One）
     │
     │  Data/ 里的散装文件通常覆盖归档里的同路径资源
     ▼
⑤ SKSE/F4SE/SFSE 插件（.dll）在游戏主循环启动时加载
     │
     ▼
⑥ Papyrus 脚本（编译后的 .pex）在游戏事件触发时执行
```

**关键点**：

- **Rule of One**：多个插件改同一条记录时，只有**最后加载的那一个**生效——不是合并，是覆盖。冲突要用 xEdit 手动做 patch。
- **Master 依赖**：一个 `.esp` 引用了另一个 `.esm/.esp` 的记录，就必须把后者列为 Master。缺 Master 时启动会崩，Vortex/MO2 通常会提前警告。
- **加载顺序既是覆盖顺序也是引用顺序**：`.esm` 必须在依赖它的 `.esp` 之前加载，否则引用链断掉。
- **散装文件 > BSA/BA2**：贴图/模型冲突时，散装文件默认赢；两个 Mod 都是散装时，取决于 Mod 管理器的 conflict resolution（MO2 是左侧列表顺序）。

---

## 四、Mod 管理器：MO2 / Vortex / Wrye Bash

### 4.1 Mod Organizer 2（MO2，推荐）

**核心机制**：**USVFS（User-Space Virtual File System）虚拟文件系统**。MO2 把每个 Mod 装在自己的独立文件夹里（`mods\<ModName>\`），启动游戏时**在内存中虚拟出一个合并后的 Data 目录**，让游戏以为 Data 里全是 Mod 文件——但硬盘上原版 Data 是完全干净的。

优点：

- 每个 Mod 独立目录，卸载/禁用/切换零污染。
- Profile 系统：多套配置切换（不同角色/不同存档用不同 Mod 列表）。
- 左侧 Mod 排序 + 右侧插件排序分离；冲突可视化明确。
- 官方支持 Skyrim SE/AE/VR、Fallout 4、Fallout NV、Oblivion、Starfield 等。

**必须用 MO2 内部启动游戏**，直接跑 `SkyrimSE.exe` 就绕过虚拟目录了，游戏看不到 Mod。

### 4.2 Vortex

Nexus 官方管理器。走的是**符号链接 / 硬链接**方案：Mod 装在中央仓库，通过链接部署到真实 Data 目录。

优点：

- Nexus 一键下载深度集成。
- 界面对新手更友好，向导多。
- 支持的游戏面更广（不局限于贝塞斯达）。

缺点：

- 部署会真的写文件到 Data 里，卸载不当会残留。
- 冲突处理不如 MO2 直观。
- 多 Profile 支持较弱。

### 4.3 Wrye Bash

老牌工具，主要用来做 **Bashed Patch**——把多个 Mod 的物品栏/leveled list 冲突合并成一个 patch 插件，避免装了 50 个物品 Mod 结果商人只卖最后一个 Mod 加进去的东西。

现在通常搭配 MO2 使用，负责 patch 生成，不单独当管理器。

---

## 五、脚本扩展：SKSE / F4SE / SFSE / OBSE / NVSE

**脚本扩展是干什么的**：贝塞斯达游戏自带的 Papyrus 脚本语言功能有限（不能读写内存、不能改渲染、没法访问许多游戏内部对象）。脚本扩展是一个 DLL loader，把自己注入游戏进程，暴露一堆额外的原生函数给 Papyrus 脚本调用——很多深度 Mod 都建立在这层上。

| 扩展 | 对应游戏 |
|---|---|
| OBSE | 《湮灭》 |
| xOBSE | 《湮灭》社区版 |
| NVSE | 《新维加斯》 |
| SKSE | Skyrim LE（老版 32 位） |
| SKSE64 | Skyrim SE / AE / VR |
| F4SE | Fallout 4 |
| SFSE | Starfield |

**版本要严格匹配游戏版本**——脚本扩展是靠固定内存地址挂钩的，游戏一升级地址就变，SKSE64 就得同步出新版。Skyrim 的「Anniversary Edition」大更新之所以让整个 Mod 社区炸锅，就是因为地址表全变了，SKSE64 不得不重来。

### 安装脚本扩展的关键

1. 解压到**游戏根目录**（和游戏 EXE 同级），不是 Data/。
2. 复制包内的 `skse64_loader.exe` 或 `sfse_loader.exe`——**以后启动游戏必须走这个 loader**，Steam 图标启动会绕过。
3. 包里的 `Data/SKSE/` 或 `Data/SFSE/` 复制到游戏的 `Data/` 下。
4. Steam 用户可以在 Steam 里改「启动选项」或直接把 `SKSE64_loader.exe` 加为非 Steam 游戏。
5. MO2 用户在 MO2 里把 loader 加为可执行项，从 MO2 内部启动它。

### 脚本扩展插件（`.dll`）

Mod 页面写「Requires SKSE」时，你装的其实是两部分：脚本扩展本体 + Mod 提供的 SKSE 插件 DLL。DLL 通常放在：

```text
Data/SKSE/Plugins/       ← Skyrim
Data/F4SE/Plugins/       ← Fallout 4
Data/SFSE/Plugins/       ← Starfield
```

SKSE 插件 DLL **必须匹配当前游戏版本 + 当前 SKSE 版本**——版本不对轻则不加载，重则闪退。所以 Mod 页面通常会分「For 1.5.97 / 1.6.353 / 1.6.640 / 1.6.1170」几个版本包。

---

## 六、Load Order 与 LOOT

装 5 个以下 Mod 时手动排序还行；装 50 个以上就需要工具。

**LOOT（Load Order Optimisation Tool）** 是社区标准的自动排序工具：

- 用官方维护的 masterlist 决定每个 Mod 的合理位置。
- 一键排序 + 冲突/缺 Master/脏编辑警告。
- MO2、Vortex 都内建集成。

**排序的基本原则**：

1. `.esm`（含官方 DLC）在最前。
2. 大型内容/世界改动 Mod 靠前。
3. 修复补丁（USSEP、USLEEP 等 Unofficial Patch）紧跟本体。
4. 游戏系统/UI/技能改动在中段。
5. **纯 patch Mod、覆盖类 Mod、Bashed Patch 排最后**。
6. 冲突时靠后的赢；想让 A 覆盖 B，就把 A 排在 B 后面。

---

## 七、xEdit：冲突检查和 Patch 制作

xEdit 是同一套工具的多个前端：**SSEdit**（Skyrim SE）、**FO4Edit**、**SF1Edit** 等。它的作用：

- **查看插件内部记录**：这个 Mod 到底改了什么。
- **可视化冲突**：多个插件改了同一条记录时，用颜色区分谁赢、赢什么。
- **手动做兼容 patch**：写一个空插件把多个 Mod 的改动合并起来。
- **清理脏编辑**（Dirty Edits）：贝塞斯达官方 DLC 里有一些非故意的记录改动，xEdit 可以清掉。
- **自动化脚本**：批量修改，例如把所有武器伤害翻倍。

安装很大 Mod 前先用 xEdit 扫一遍，能规避大量启动崩溃。

---

## 八、安装步骤（以 Skyrim SE + MO2 为例）

以下是最主流的组合。其他游戏、其他管理器思路一致，只是文件名不同。

### 8.1 准备工作

1. 确认 Skyrim SE 已通过 Steam 完成安装并至少启动过一次。
2. 记录当前游戏版本（Steam → 游戏属性 → 更新页尾），比如 `1.6.1170`。
3. **把游戏装在非 `C:\Program Files\` 目录**——UAC 会拦截 Mod 管理器写入，很多问题都源于此。
4. 关闭 Windows Defender 对游戏目录和 MO2 目录的实时监控（或加白名单）。

### 8.2 装 MO2

1. 从 [MO2 GitHub Releases](https://github.com/ModOrganizer2/modorganizer/releases) 下载「便携版」压缩包。
2. 解压到一个**非 Program Files** 的独立目录，例如 `D:\ModOrganizer2\`。
3. 首次运行选择 Skyrim SE，让它自动检测游戏路径。
4. 创建一个 Profile（默认的就行）。

### 8.3 装 SKSE64

1. 从 [SKSE 官网](https://skse.silverlock.org/) 下载对应游戏版本的 SKSE64。
2. 打开压缩包，把 `skse64_1_x_xxx.dll`、`skse64_loader.exe`、`skse64_steam_loader.dll` 复制到**游戏根目录**（`Skyrim Special Edition\`）。
3. 把压缩包里的 `Data/SKSE/` 整个夹子复制到游戏的 `Data/` 下。
4. 在 MO2 顶部工具栏「Executables」里添加 `skse64_loader.exe`，勾选「Force load libraries」如需要。
5. 从 MO2 里点它启动一次，进主菜单按 `~` 打开控制台，输入 `getskseversion`，返回版本号即成功。

### 8.4 装第一个 Mod

以 [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) 为例（一个 SKSE 前置的 UI Mod）：

1. 在 Nexus 页面下载压缩包（`.7z` 或 `.zip`）。
2. MO2 左上角「Install a new mod from an archive」，选压缩包。
3. Mod 出现在左侧列表；勾选启用。
4. 右侧插件列表里 `SkyUI_SE.esp` 会自动出现，勾选启用。
5. 用 MO2 里的 LOOT 排一下。
6. 从 MO2 启动 SKSE Loader 进游戏，主菜单出现 SkyUI 标志。

### 8.5 Star Sky Starfield 特别说明

Starfield 的 Mod 生态相比 Skyrim 还年轻，但**已经稳定**：

- 使用 SFSE + Mod 管理器（MO2 v2.5+ 或 Vortex）。
- Starfield 需要在 `Documents\My Games\Starfield\StarfieldCustom.ini` 里加 `[Archive] sResourceDataDirsFinal=` 一行才能读散装 Mod 文件（早期需要，2024 之后的官方补丁已经放宽）。
- 官方 Creations 平台（付费/免费）走 `Data/` 一样的加载路径，Mod 管理器可以和它共存但要注意冲突。

---

## 九、常见 Mod 类型速览

| 类型 | 例子 | 装法 |
|---|---|---|
| Plugin + 资源 | 新任务、新武器、新地区 | 走 Mod 管理器；有 `.esp` 和 BSA/BA2 或散装 |
| 纯资源替换 | 高清贴图、Mesh 替换 | 无插件，只有 `textures/` `meshes/` |
| SKSE/F4SE 插件 | SkyUI、Address Library、EngineFixes、SmoothCam | 需要 SKSE，DLL 走 `Data/SKSE/Plugins/` |
| Papyrus 脚本 Mod | 大量任务/系统 Mod | 走 Mod 管理器；`.pex` 在 BSA 里或散装 `Data/scripts/` |
| Body/Skin | CBBE、UNP、BHUNP、3BA | 需要 BodySlide + OutfitStudio 生成 |
| ENB 光照 | ENB Series + 各家预设 | 装 ENB Series 二进制到游戏根目录 + 预设覆盖 |
| Reshade | 通用后处理 | 装 Reshade 到游戏根目录 |

---

## 十、常见问题排查

### Q1：CTD（Crash to Desktop）无提示闪退

- 装 **Crash Logger**（Skyrim SE 有 CrashLoggerSSE，Starfield 有对应版本），能在 CTD 时输出堆栈日志到 `Documents\My Games\...\SKSE\`。
- 用 [Crash Log Auto Analyzer](https://github.com/GuidanceOfGrace/Buffout4-CLAS) 之类的自动分析工具解读日志，能定位到具体 Mod。
- 常见原因：Mesh 引用了缺失贴图、缺 Master、SKSE 插件版本对不上、脏编辑没清、显存爆了。

### Q2：启动报「Cannot find master file XXX.esp」

Load Order 里某个 `.esp` 依赖了没启用/没安装的 Master。用 xEdit 或 Mod 管理器的错误面板看是哪个 Mod 缺哪个 Master，装上或禁用调用它的 Mod。

### Q3：装了 SKSE 插件 DLL 但没生效

- 检查游戏版本、SKSE 版本、DLL 支持的版本三者是否严格一致。
- 装 **Address Library for SKSE Plugins** 前置。它把不同游戏版本的关键地址映射成稳定 ID，让 SKSE 插件不用每次游戏更新都重新编译。
- 打开 `Documents\My Games\Skyrim Special Edition\SKSE\SKSE.log`，看具体哪个插件报什么错。

### Q4：贴图 Mod 装了但游戏里没变化

- Mod 管理器左侧列表里，覆盖别人的 Mod 要排在**下面**。
- 确认 `Data/textures/` 里的路径和游戏内部路径一致（不要多套一层 `textures/textures/`）。
- BSA 里的贴图如果没被散装文件覆盖，需要 `sResourceDataDirsFinal` 配置允许散装。

### Q5：游戏（Skyrim SE）自动更新后所有 Mod 都失效

Bethesda/Steam 会不打招呼地推送游戏更新，让 SKSE 版本失配。

- 装 **Steam Update Blocker** 或改 Steam 「仅在启动时更新」设置。
- 已经更新了：只能等 SKSE、Address Library、你用的所有 SKSE 插件依次出新版；期间保留旧版备份可以回退到旧 EXE。
- Steam 上有玩家维护 downgrade patcher（比如 `SSE Downgrader`）可以回滚游戏版本。

### Q6：Mod 数量到上限打不开游戏

Skyrim SE 的 `.esp` load order 上限是 **255 个**（`.esl` 不占 slot）。超了游戏就崩。

- 把体积小的 Mod 转成 `.esl`（用 xEdit 加 ESL Flag 或 SSEEdit 转换）。
- Bashed Patch 合并 leveled list 类冲突。
- Merge Plugins（xEdit 4.x 内置或独立工具）把多个小 Mod 合并成一个。

---

## 十一、卸载

### 卸载单个 Mod（MO2）

在左侧列表禁用或右键删除；虚拟 Data 系统会自动把这个 Mod 从游戏里移除。**游戏内已经用过这个 Mod 的存档可能出现「脚本残留」**——存档里保留了对已删除脚本的引用，某些情况下会导致慢速泄漏或 CTD。深度依赖脚本的 Mod 建议开新档卸载。

### 卸载 SKSE / SFSE

删除游戏根目录里的 loader 和 DLL，删除 `Data/SKSE/` 或 `Data/SFSE/`；从 Steam 直接启动游戏即可回到原版。

### 完全清理

1. MO2：直接删掉 MO2 目录（Mod 都在里面）。
2. 游戏 Data：如果没走 MO2 而是手动覆盖过，只能靠 Steam「验证游戏文件完整性」把 Data 恢复到原版。
3. 存档/配置：`Documents\My Games\<游戏>\` 里的 `.ess` 存档、`.ini`、`Plugins.txt`、`Loadorder.txt` 都可能残留旧引用，需要时手动清。

---

## 十二、安全边界

- **只从 Nexus、Bethesda.net Creations 等可信来源下载** Mod；SKSE 插件是可执行 DLL，来源不明的直接不装。
- **不要给 Fallout 76 装单机注入式 Mod**——它是网游，会封号。目前 FO76 只允许纯客户端外观 Mod（贴图、Mesh、UI）且风险自担。
- 《辐射 3》《新维加斯》等老游戏对 4GB Patch、xLive 修复、Windows 10 兼容层有较多社区补丁需求；装之前先看游戏对应的「Fear and Loathing」「Viva New Vegas」等社区安装向导。
- 备份 `Documents\My Games\<游戏>\Saves\` 存档；Mod 卸载/切换、Load Order 变化都可能破坏存档。
- 大型 Mod（LL、色情类）不要跨社区搬运；某些国家/平台条款禁止分发。

---

## 十三、流程总结

```text
① 确认游戏世代（Gamebryo / CE1 / CE2）和精确版本号
       ↓
② 装 MO2 或 Vortex（推荐 MO2）
       ↓
③ 装脚本扩展（SKSE / F4SE / SFSE），从 MO2 里配好 loader
       ↓
④ 装 Address Library、USSEP 等基础前置
       ↓
⑤ 按 Mod 页面 Requirements 装 Mod（Plugin + BSA/BA2 + SKSE DLL）
       ↓
⑥ 用 LOOT 排序、xEdit 检查冲突、必要时做 Bashed Patch
       ↓
⑦ 从 Mod 管理器里启动 SKSE loader 进游戏验证
       ↓
⑧ 游戏更新前先禁用 Mod / 阻止更新；更新后等 SKSE 生态适配
```

> 核心口诀：**版本严格匹配 → Mod 管理器不要绕开 → 装 SKSE 前先想清楚 → LOOT + xEdit 排队 → 存档常备份。**

---

## 参考资料

- [Nexus Mods](https://www.nexusmods.com/) — Mod 主站
- [Mod Organizer 2 GitHub](https://github.com/ModOrganizer2/modorganizer)
- [Vortex Mod Manager](https://www.nexusmods.com/site/mods/1)
- [SKSE 官网](https://skse.silverlock.org/)
- [F4SE 官网](https://f4se.silverlock.org/)
- [SFSE GitHub](https://github.com/ianpatt/sfse)
- [LOOT](https://loot.github.io/)
- [SSEEdit / xEdit GitHub](https://github.com/TES5Edit/TES5Edit)
- [Address Library for SKSE Plugins（Nexus）](https://www.nexusmods.com/skyrimspecialedition/mods/32444)
- [Unofficial Skyrim Special Edition Patch（USSEP）](https://www.nexusmods.com/skyrimspecialedition/mods/266)
- [Skyrim SE 稳定安装向导：STEP](https://stepmodifications.org/wiki/Guide:Skyrim_SE)
- [Fallout NV 稳定安装向导：Viva New Vegas](https://vivanewvegas.moddinglinked.com/)
