# 潜行者游戏 Mod 安装指南（X-Ray 引擎篇）

> 本指南面向 GSC Game World 用 **X-Ray 引擎** 开发的《潜行者》系列，以及在此之上生长出来的大型社区整合包。**《潜行者 2：切尔诺贝利之心》** 换到了 UE5，Mod 生态另开一条路，本文不覆盖。
>
> **主要覆盖**：
>
> - **《潜行者：切尔诺贝利的阴影》**（Shadow of Chernobyl，SoC）
> - **《潜行者：晴空》**（Clear Sky，CS）
> - **《潜行者：普里皮亚季的召唤》**（Call of Pripyat，CoP）
> - **社区整合包**：**Anomaly**、**GAMMA**、**EFP**、**Call of Chernobyl**、**Misery** 等
>
> **总规则**：**Mod 是给哪个游戏、哪个整合包写的，只能装到那个组合上**。Anomaly 的 Mod 装不进 CoP 原版，SoC 的 Mod 装不进 Anomaly——生态是分裂而不是叠加的。

---

## 一、先分清「原版三部曲」与「社区整合包」

X-Ray 生态最容易踩的坑就是分不清「我在装哪个游戏」。

### 1.1 GSC 官方原版三部曲

| 游戏 | 引擎版本 | 备注 |
|---|---|---|
| SoC（阴影） | X-Ray 1.0 | 2007，DirectX 8/9 |
| CS（晴空） | X-Ray 1.5 | 2008，DX10 支持 |
| CoP（召唤） | X-Ray 1.6 | 2009，最成熟的一代，社区整合包基本都从这里开始 |

原版三部曲现在（Steam / GOG）都能买到；引擎源码 GSC 早年泄漏后被社区接手。

### 1.2 社区大型整合包

X-Ray 生态里真正的当红作品是这些**建立在原版之上的大型社区项目**——它们本身就是修改过的引擎 + 全新剧本/系统 + 上百个 Mod 集成，玩起来更接近独立游戏。

| 整合包 | 底子 | 特色 |
|---|---|---|
| **Anomaly** | 独立引擎（基于 X-Ray Monolith 分支） | 自由沙盒模式 + Warfare + Story；免费独立发行，不需要原版 |
| **GAMMA**（G.A.M.M.A.） | Anomaly + 数百个精选 Mod | 硬核生存 + 高画质；用 Mod Organizer 2 管理，一键装 400+ Mod |
| **EFP**（Escape from Pripyat） | Anomaly + 精选 Mod | 类似 GAMMA 的重量级整合，风格更硬核战斗向 |
| **Call of Chernobyl (CoC)** | X-Ray（原版 CoP 引擎改进） | 全地图 + 自由沙盒；Anomaly 的精神前身 |
| **Call of Misery** | CoC + Misery | Misery 硬核规则的沙盒版 |
| **Misery** | CoP 之上的 Mod | 硬核难度 + 灰暗调色 + 更多物品 |
| **OGSR** | SoC 引擎的社区分支 | SoC 高画质 + 稳定性重制 |
| **Old Good STALKER Evolution** | SoC/CoP | 大型剧情扩展 |

**这里最大的分歧**：装 Mod 之前先想清楚你玩的到底是「原版 CoP + 单个 Mod」，还是「Anomaly」，还是「Anomaly 上的 GAMMA」——它们的 Mod 目录、加载方式、包管理器完全不同。

---

## 二、原理：X-Ray 是怎么加载 Mod 的

### 2.1 `.db` 归档 + `gamedata/` 松散文件

X-Ray 引擎把游戏所有资源打包成一系列 `.db*` 文件（`gamedata.db0`、`gamedata.db1` 等），装在游戏根目录下。**Mod 通常不去改这些归档，而是走「松散文件覆盖」**：

- 游戏启动时会去 `gamedata/` 目录里找散装文件。
- 找到的散装文件**优先于 `.db*` 归档里的同路径资源**——引擎读到就用，忽略归档里的原版。
- Mod 的本质就是**把 Mod 的散装文件放到 `gamedata/` 里、按照游戏内部目录结构组织**。

```text
Call of Pripyat/
├── xrEngine.exe            ← 游戏主 EXE
├── gamedata.db0            ← 原版资源归档（不要动）
├── gamedata.db1
├── ...
├── fsgame.ltx              ← 文件系统配置
└── gamedata/               ← Mod 的散装文件放这里
    ├── configs/            ← LTX 配置
    ├── scripts/            ← Lua 脚本
    ├── textures/           ← DDS 贴图
    ├── meshes/             ← OGF 模型
    ├── shaders/            ← 着色器
    ├── sounds/             ← OGG 音频
    └── ...
```

### 2.2 `fsgame.ltx`：文件系统开关

原版游戏默认关闭了 `gamedata/` 的松散文件读取——为了避免玩家意外/恶意替换资源。装 Mod 前必须先打开这个开关：

打开 `fsgame.ltx`（游戏根目录），找到这一行：

```text
$game_data$        = false | true | $fs_root$| gamedata\
```

把第一个 `false` 改成 `true`：

```text
$game_data$        = true  | true | $fs_root$| gamedata\
```

**Anomaly / GAMMA / CoC 等社区整合包默认已经开启，无需手动改**。原版三部曲要装 Mod 才需要改。

### 2.3 LTX：X-Ray 的配置文件语言

LTX（Light Text，社区俗称）是 INI 的扩展格式，用于描述几乎所有游戏内容：

- 武器、弹药、防具、物品：`configs/items/weapons/`、`configs/items/outfits/`
- NPC、突变体、派系：`configs/creatures/`、`configs/gameplay/`
- 地图 spawns：`configs/misc/`、`configs/game_maps.ltx`
- UI 定义：`configs/ui/`

LTX 语法可以**继承**（`:parent_section`），可以**覆盖单个键**，让 Mod 修改起来非常灵活。

```ltx
[wpn_ak74:wpn_ak74_original]
cost                    = 12000
inv_weight              = 3.6
fire_dispersion_base    = 0.19
```

上面 `wpn_ak74` 继承自 `wpn_ak74_original`，只覆盖了三个字段——想微调武器数值不用抄整段。

### 2.4 Lua 脚本

X-Ray 的游戏逻辑大量用 Lua 写，位于 `gamedata/scripts/`（Anomaly 上千个 `.script` 文件）。Mod 想改玩法就修改或添加对应脚本。

- 老版游戏（SoC）用 Lua 5.1。
- Anomaly 之后用 DLTX、MCM（Mod Configuration Menu）等社区扩展，允许多个 Mod 同时写自己的 LTX 而不冲突。

### 2.5 Anomaly / GAMMA 的引擎改进

社区整合包底层不是纯官方 X-Ray——它们基于 X-Ray Monolith / OpenXRay 分支：

- **修 bug、加 DirectX 11、去 32 位内存限制**（旧引擎 4GB 崩溃常见）。
- 加入 **DLTX**：让多个 Mod 修改同一段 LTX 不冲突（作者只需要写「增量」而不是覆盖整份文件）。
- 加入 **MCM**：游戏内 UI 调 Mod 参数。
- 加入 **Modded Exes**：整合包附带的 `xrEngine.exe`、`AnomalyLauncher.exe`——用整合包必须走它自带的 launcher，不是原版。

---

## 三、原版三部曲的 Mod 安装

### 3.1 通用步骤（以 Call of Pripyat 为例）

1. **备份 fsgame.ltx**。
2. 编辑 `fsgame.ltx`，把 `$game_data$` 那行第一个 `false` 改成 `true`。
3. 关闭游戏，找到 Mod 下载页（Nexus / ModDB）。
4. 解压 Mod 压缩包，Mod 内部通常是这个结构：

   ```text
   MyMod/
   ├── gamedata/
   │   ├── configs/
   │   ├── scripts/
   │   └── textures/
   └── readme.txt
   ```

5. 把 Mod 的 `gamedata/` **合并** 进游戏根目录里的 `gamedata/`（游戏根目录如果没有 gamedata 就新建）。
6. 启动游戏验证——Mod 修改的部分应该已经生效。

### 3.2 手动装多个 Mod 的冲突

原版三部曲的 Mod 是**文件级覆盖**：

- 两个 Mod 都改了 `configs/weapons/w_ak74.ltx`，谁后覆盖谁生效。
- 手动合并需要用 [Winmerge](https://winmerge.org/)、KDiff3 之类的对比工具。
- 社区通常有针对流行 Mod 组合的 **Compatibility Patch**，加载到最后覆盖冲突。

### 3.3 大型 Mod（Complete、AMK、OGSR）

原版三部曲的知名大型 Mod：

- **Complete 系列**（Complete 2009 for SoC / CS / CoP）：画质+平衡整合。
- **AMK Autumn Aurora 2**：SoC 的经典重构。
- **OGSR**：SoC 引擎社区分支（严格来说是引擎替换 + Mod）。
- **Dead Air**（CoP 之上）：Anomaly 的直接前身。
- **Lost Alpha**（GSC 前员工重制 SoC）：独立发布，几乎是新游戏。

装大型 Mod 时通常需要**从干净原版开始**——Mod 作者往往会明确要求「先卸载所有其他 Mod / 验证游戏文件 / 从原版 gamedata 开始」。

---

## 四、Anomaly：独立整合包的装法

Anomaly 是过去几年最活跃的 STALKER 生态入口，值得单独讲。

### 4.1 什么是 Anomaly

- **独立发行**，**不需要拥有原版三部曲**（引擎和资源都重新做过）。
- **免费**，官方从 [ModDB](https://www.moddb.com/mods/stalker-anomaly) 或社区镜像下载。
- 内容涵盖三部曲所有地图，加自定义 Story + Warfare 沙盒模式。
- 内建 DLTX、MCM、精细的物品/武器/派系系统。

### 4.2 安装 Anomaly

1. 从 ModDB 下载最新版 Anomaly（一般是 `Anomaly-x.x.x.zip` 或分包，约 25 GB）。
2. **解压到一个专用目录**（不要放 Program Files 或系统盘根目录）。例如 `D:\Games\Anomaly\`。
3. 目录结构完成后有 `AnomalyLauncher.exe`、`bin/`、`db/`、`gamedata/` 等。
4. 双击 `AnomalyLauncher.exe`：
   - 选渲染器（DX8 / DX9 / DX10 / DX11，DX11 最好，老显卡用 DX9）。
   - 选 Avatar、开始新剧情或 Warfare/Story 模式。

### 4.3 装 Anomaly Mod

Anomaly 的 Mod 分两类：

**① 直接放 gamedata/ 的传统 Mod**

- Mod 压缩包里是 `gamedata/`。
- 把 Anomaly 目录里的 `gamedata/` 备份一下，或者直接**在 Anomaly 目录下建 `mods/` 或让 MO2 管理**（下面 4.4 讲）。
- 合并覆盖 `gamedata/`。

**② DLTX Mod**

- 现代 Anomaly Mod 大多走 DLTX：只在 `gamedata/configs/mod_system_myfeature.ltx` 里写增量补丁，不整份覆盖原版文件。
- 装法：把 DLTX 补丁文件放进 `gamedata/configs/`。
- 多个 DLTX Mod 一般不会互相冲突（除非动同一个字段）。

### 4.4 Anomaly + Mod Organizer 2

装 20+ 个 Mod 时手动合并 `gamedata/` 极其痛苦——**强烈建议用 MO2**。Anomaly 社区甚至提供预配置的 MO2 版本。

- MO2 的 USVFS 让每个 Mod 独立目录，运行时虚拟合并——和 Bethesda 游戏是一模一样的机制。
- 装 Anomaly 版 MO2：从 Anomaly 社区（ModDB、Discord）下载配好 profile 的 MO2 压缩包。
- 把 Mod 逐个作为独立目录导入 MO2。
- 冲突可视化（左侧 Mod 顺序决定覆盖优先级，靠下的赢）。
- 装完从 MO2 里点「AnomalyLauncher.exe」启动——**必须从 MO2 启动才能应用虚拟 gamedata**。

---

## 五、GAMMA：MO2 + 400 个 Mod 的自动化整合

GAMMA 是 Anomaly 之上的**元整合包**——不是单个 Mod，而是一份 **Mod 清单 + 一键下载脚本 + 一套 MO2 profile**，把社区数百个 Mod 自动组合起来。

### 5.1 GAMMA 是怎么工作的

- 从 [GAMMA 官网](https://www.stalkergamma.com/) 或 [GitHub 仓库](https://github.com/Grokitach/Stalker_GAMMA) 拿到官方安装器（Grok's Modpack Installer / stalker-gamma-gui）。
- 安装器让你选一个空目录，把 **纯净 Anomaly + MO2 + 所有需要的 Mod** 自动下载、放到正确位置、按预设 Load Order 排好。
- Mod 从各种源拉：ModDB、GitHub、社区镜像。
- 一次完整安装耗时 30 分钟到几个小时（取决于网络）。

### 5.2 安装步骤

1. 准备至少 **150 GB 空闲磁盘**（GAMMA 官方 wiki 明确要求，装完之后可再"瘦身"，但装的过程必须先留够）。
2. 从 [GAMMA 官网](https://www.stalkergamma.com/) 或 [Stalker_GAMMA GitHub](https://github.com/Grokitach/Stalker_GAMMA) 下载官方安装器。
3. 解压到目标目录，运行 `stalker-gamma-gui.exe`（Grok's Modpack Installer）。
4. 安装器会引导：
   - 选一个**空**的目标目录（不要用已有 Anomaly 目录）。
   - 自动下载纯净 Anomaly、MO2、所有 Mod（来源包括 ModDB、GitHub、社区镜像）。
5. 装完从 GAMMA Launcher 或 MO2 启动 AnomalyLauncher。

### 5.3 装完之后

GAMMA 自带一整套预设 Mod，通常玩家只需微调：

- 在 MO2 里禁用不喜欢的 Mod。
- 在游戏内的 MCM 面板调参数。
- GAMMA 更新时用 GAMMA Launcher 一键同步 Mod 版本。

**GAMMA 的核心价值**：把「选 Mod、装 Mod、排顺序、修冲突」这套原本要手动做几十小时的工作**自动化**了。它本身不是新 Mod，而是一份精心策划的 Mod 组合方案。

**EFP（Escape from Pripyat）** 是 GAMMA 之外的另一个类似方案，风格更偏硬核战斗；两者不能同时装。

---

## 六、目录结构总览

### 原版 CoP + 单个 Mod

```text
S.T.A.L.K.E.R. - Call of Pripyat/
├── xrEngine.exe
├── fsgame.ltx                   ← 记得改 $game_data$ = true
├── gamedata.db0..dbX            ← 原版资源归档
├── gamedata/                    ← Mod 散装文件
│   ├── configs/
│   ├── scripts/
│   ├── textures/
│   ├── meshes/
│   └── shaders/
└── ...
```

### Anomaly 独立整合包

```text
Anomaly/
├── AnomalyLauncher.exe          ← 启动器
├── bin/                         ← 引擎二进制（改过的 xrEngine）
├── db/                          ← 原版资源打包
├── gamedata/                    ← Mod 散装文件（初始只有默认内容）
├── appdata/                     ← 存档、配置、日志
│   ├── savedgames/
│   ├── logs/
│   └── shaders_cache/
└── mods/                        ← 可选，MO2 或手动分目录管理
```

### Anomaly + MO2（推荐结构）

```text
MO2_Anomaly/                     ← MO2 本身
├── ModOrganizer.exe
├── mods/                        ← 每个 Mod 一个独立目录
│   ├── BAS_1.5/
│   ├── EFT_HUD/
│   ├── DrX_Questlines/
│   └── ...
├── profiles/                    ← Playset / Profile
│   └── Default/
├── overwrite/                   ← 游戏运行时新写入的文件先落这
└── downloads/

Anomaly/                         ← Anomaly 本体（保持干净）
```

### GAMMA

GAMMA 装完之后目录里是 `Anomaly + MO2 + 400 个 Mod`，还有一个 GAMMA Launcher。玩家一般不直接看这层目录，都通过 MO2 和 GAMMA Launcher 交互。

---

## 七、常见问题排查

### Q1：改了 fsgame.ltx 但 Mod 没生效

- 确认第一个 `false` 改成了 `true`，不是第二个。
- 确认改的是**游戏根目录**里那份 `fsgame.ltx`，不是压缩包里的。
- Anomaly 用户不用改这个（默认已开）。

### Q2：游戏启动就崩

- **打开日志**：`appdata/logs/xray_<用户名>.log`（Anomaly 在 `appdata/logs/`；原版三部曲通常在 `_appdata_/logs/`）。日志末尾几十行会有 `FATAL ERROR` 加详细信息。
- 常见原因：
  - `configs/` 里某个 LTX 语法错误。
  - Mod 引用了不存在的贴图、模型、脚本文件（`can't open section` / `can't find texture`）。
  - Mod 之间冲突：两份 `.script` 定义了同名函数。
- 逐个禁用 Mod 找罪魁：MO2 用户直接在左侧禁用，手动装的移出 `gamedata/`。

### Q3：日志报 `can't find section`

某个 LTX 引用了不存在的 section（比如武器引用了不存在的弹药类型）。用记事本或 VS Code 搜错误信息里的 section 名，看哪个 Mod 引入了这个引用。

### Q4：GAMMA 装到一半下载失败

- ModDB / GitHub / 社区镜像单个源挂了，GAMMA Launcher 会尝试重试。
- 网络原因（中国大陆访问 ModDB 不稳定）：挂代理或用离线包（GAMMA 社区有时候提供整合离线包）。
- 磁盘空间：GAMMA 官方要求**至少 150 GB 可用空间**（装完之后可选择瘦身，但装的过程必须先留够）。

### Q5：加入 MO2 profile 后启动器打不开

- 从 **MO2 内部**启动 `AnomalyLauncher.exe`，不是从 Windows 资源管理器双击。
- 确认 MO2 里已经把 AnomalyLauncher 添加到「Executables」下拉列表。
- Anomaly 目录里的 `bin/xrEngine.exe` 是引擎，不是启动器，正常不直接跑。

### Q6：MP 联机不同步

- Anomaly 目前只有单机 + 局域网/Roleplay 服务器；MP 生态很小。
- 联机需要**所有玩家 Mod 列表完全一致**，包括版本号；建议用 GAMMA 或 EFP 这种确定性预设。

### Q7：显卡驱动更新后画面出问题

X-Ray 老引擎对新驱动的兼容有时候崩：

- 试试切换渲染器（Anomaly Launcher 里选 DX9 / DX10 / DX11）。
- 关闭动态雾、SSAO 等高级效果。
- 装 dgVoodoo2 / dxvk 之类的兼容层（老游戏尤其 SoC 有效）。

### Q8：Mod 卸载后存档打不开

X-Ray 的存档会记录当前世界所有实体、变量、Mod 状态。装了新武器、新任务的 Mod 后，卸载 Mod 会让存档指向不存在的东西直接崩。

- **装/卸大型 Mod 建议开新档**。
- 换 Mod 组合时用 MO2 的 Profile 系统，每个组合独立存档目录。

---

## 八、卸载

### 卸载单个 Mod

- MO2 用户：左侧禁用或删除该 Mod 目录。
- 手动装的 Mod：删除 Mod 添加到 `gamedata/` 的对应文件——问题是要知道它加了什么，所以装 Mod 前**先备份 `gamedata/`**。

### 卸载 Anomaly / GAMMA

- 直接删整个 Anomaly / GAMMA 目录（存档默认在 `appdata/savedgames/` 里面，先备份）。
- 原版三部曲不受影响（它们在独立目录）。

### 回到原版三部曲干净状态

- 删掉 `gamedata/` 目录。
- Steam / GOG 里验证游戏文件完整性。
- 把 `fsgame.ltx` 的 `$game_data$` 改回 `false`（可选）。

---

## 九、安全边界

- Mod 主要是数据 + Lua 脚本，理论上不跑 native code；但 Anomaly / GAMMA 内含改造过的 `xrEngine.exe`，运行的是可执行文件——只从可信来源（GAMMA GitHub 官方仓库、Anomaly ModDB 页）下载。
- Mod 里附带的 `.exe`、`.dll` 需要警惕——通常正常 Mod 不需要这些。
- 备份 `appdata/savedgames/`（Anomaly）或 `_appdata_/savedgames/`（原版三部曲）。
- **X-Ray 生态几乎无 MP 反作弊问题**，因为主流玩法都是单机；哪怕加了硬核 Mod 也不影响其他玩家。
- 中国大陆访问 ModDB、部分社区镜像不稳定，需要挂代理；不要下载来源不明的整合包。

---

## 十、流程总结

```text
① 想清楚要玩哪个：原版 SoC/CS/CoP、Anomaly、GAMMA、EFP、其他 TC
       ↓
② 原版三部曲：改 fsgame.ltx 的 $game_data$ 为 true → 装 Mod
   Anomaly：解压独立包 → 直接玩或加 Mod
   GAMMA / EFP：用官方安装器一键部署
       ↓
③ 装 5+ 个 Mod 时上 MO2 管理，避免手动合并 gamedata/
       ↓
④ Mod 出问题看 appdata/logs/ 里的 xray 日志
       ↓
⑤ 卸载或换组合时用 MO2 Profile 隔离；大型 Mod 变化开新档
```

> 核心口诀：**分清游戏和整合包 → gamedata 覆盖 db → fsgame.ltx 开开关 → Anomaly 上 MO2 → GAMMA/EFP 一键部署 → 日志优先于猜测。**

---

## 参考资料

- [ModDB: S.T.A.L.K.E.R.](https://www.moddb.com/games/stalker) — 老 Mod 主站
- [Anomaly（ModDB 页面）](https://www.moddb.com/mods/stalker-anomaly)
- [S.T.A.L.K.E.R. Anomaly Discord & Wiki](https://www.moddb.com/mods/stalker-anomaly)
- [GAMMA 官网 stalkergamma.com](https://www.stalkergamma.com/)
- [Stalker_GAMMA GitHub 仓库](https://github.com/Grokitach/Stalker_GAMMA)
- [GAMMA Installing Wiki](https://github.com/Grokitach/Stalker_GAMMA/wiki/Installing-GAMMA)
- [EFP（Escape from Pripyat）](https://www.moddb.com/mods/escape-from-pripyat)
- [OpenXRay（开源引擎重制）](https://github.com/OpenXRay/xray-16)
- [Mod Organizer 2](https://github.com/ModOrganizer2/modorganizer)
- [DLTX（Dynamic LTX）文档](https://github.com/themrdemonized/xray-monolith)
- [Winmerge 文件比较](https://winmerge.org/)
