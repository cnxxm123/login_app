# V 社游戏 Mod 安装指南（Source / Source 2 篇）

> 本指南面向 Valve 的两代自研引擎：**Source**（2004 起）和 **Source 2**（2015 起）的 Mod 安装。
>
> **Source 覆盖**：《半衰期 2》、《军团要塞 2》、《反恐精英：起源》、《求生之路 2》(L4D2)、《传送门》/《传送门 2》、**《Garry's Mod》**（本身就是 Mod 平台）等。
>
> **Source 2 覆盖**：《DOTA 2》、《半衰期：爱莉克斯》、**《反恐精英 2》(CS2)**、《SteamVR Home》、《Underlords》等。
>
> **CS:GO 与 CS2 的关系**：CS:GO 已在 2023 年 9 月 27 日被 CS2 完全替换（沿用同一个 Steam AppID 730），官方竞技匹配、开发维护都转到了 Source 2 的 CS2。CS:GO 目前只剩 Valve 保留的 `csgo_legacy` 分支/独立包，无官方匹配、社区服少。本文里出现的 CS:GO `custom/` 目录结构等仍适用于 legacy 分支和历史 Mod 参考，但要玩活跃 Mod 生态请对准 CS2 Workshop。
>
> **总规则**：**Steam Workshop 是主入口**——大多数 V 社游戏的 Mod 走官方 Workshop 系统，一键订阅、自动更新、跨设备同步。手动安装只在少数场景（老 Mod、私服、开发调试）需要。

---

## 一、Source vs Source 2

| | Source | Source 2 |
|---|---|---|
| 起始年份 | 2004（HL2） | 2015（DOTA 2 重制版） |
| 资源打包 | **VPK**（Valve Pak，v1/v2 版本） | VPK（v2 改良版） |
| 地图格式 | `.bsp`（编译产物），`.vmf`（源代码） | `.vpk` + 新地图工具集 |
| 关卡编辑器 | Hammer Editor（游戏 SDK 自带） | Hammer 2（新版，附带在游戏工具里） |
| 脚本语言 | Squirrel、VScript、Lua（GMod） | Lua、Panorama JS（DOTA 2 UI） |
| Mod 目录约定 | 每个游戏自己的 `<game>/custom/`，或 Steam Workshop | Steam Workshop 是主线 |
| Workshop | 部分游戏支持 | 全线原生支持 |

**从玩家安装 Mod 的角度看，Source 2 生态更规整**——所有主流游戏都用 Workshop；Source 时代有些老游戏（HL2、TF2 早期）需要更多手动操作。

---

## 二、原理：Source 引擎是怎么加载 Mod 的

### 2.1 gameinfo.txt / gameinfo.gi：搜索路径清单

- 每个 Source / Source 2 游戏的根目录下都有 `<gamename>/gameinfo.txt`（Source）或 `<gamename>/gameinfo.gi`（Source 2）。
- 这个文件里的 `SearchPaths` 段声明**引擎去哪些位置找资源**（贴图、模型、脚本、地图）。
- 加载时按 SearchPaths 里从上到下的顺序逐层查找，**先找到就用**（不是覆盖）。

CS:GO 时代（现在的 legacy 分支）的一段典型 `SearchPaths` 简化后长这样：

```text
SearchPaths
{
    Game        |all_source_engine_paths|csgo/custom/*  // 玩家 Mod
    Game        |gameinfo_path|.                        // 游戏本身
    Game        csgo
    Game        |all_source_engine_paths|csgo
    Game        |all_source_engine_paths|hl2
}
```

- `|all_source_engine_paths|csgo/custom/*` 里的 `*` 是通配符，表示 `csgo/custom/` 下**每个子目录都被扫描**——这是 CS:GO 玩家放 Mod 的标准位置。
- 通配符路径排在最上面，意味着 Mod 目录里的资源**优先于游戏原版被使用**。

### 2.2 VPK 归档

- VPK 是 V 社的资源打包格式（类似 ZIP，但优化过读取速度和随机访问）。
- 一个 Mod 可以是一个 `.vpk` 文件，也可以是一堆散装文件的目录。
- 引擎会把 VPK **虚拟挂载**——挂载后 VPK 里的所有文件看起来就像散装文件一样存在于 VPK 所在的目录中。
- Workshop 下载的 Mod 通常打包成 `.vpk`（Source 时代）或多个 `.vpk`（Source 2 分块）。

### 2.3 覆盖顺序

由于是「先找到就用」而不是「后加载覆盖」：

- Mod（放在 `custom/` 或类似目录）的资源**先于**游戏原版被找到，所以它替换了原版。
- 两个 Mod 都改了同一份资源时：**目录名字母序靠前的赢**——所以社区 Mod 有时候用 `AAA_MyMod` 或 `_MyMod` 强行排到最前。
- 这和 P 社、Skyrim 的「后加载覆盖」逻辑相反，装 Mod 时要留意。

### 2.4 Garry's Mod 的特殊之处

Garry's Mod 是「Source 引擎里的一个沙盒 Mod」，本身内建了完整的 Lua 脚本 API + Addon 加载器：

- Mod（叫 Addon）位置在 `garrysmod/addons/<addon_name>/`。
- Addon 目录里可以放 Lua 脚本（`lua/`）、模型（`models/`）、贴图（`materials/`）、地图（`maps/`），结构就是游戏内部资源路径。
- Workshop 订阅的 Mod 会存为 `.gma` 归档到 `garrysmod/addons/`，运行时被 Gmod 自动挂载。
- GMod 用 Lua 而不是 Source SDK 的 C++/Squirrel，脚本 Mod 极其活跃。

### 2.5 Source 2 的变化

- Source 2 引擎抛弃了 `gameinfo.txt` 的老写法，改用 `gameinfo.gi`（KV 格式）+ 更严格的资源规范。
- 官方工具（Hammer 2、Model Editor、Particle Editor）在 Source 2 游戏的 `game/bin/` 里，玩家可以直接进入编辑器。
- 但 **CS2 目前对 Mod 的态度趋于保守**——官方允许 Workshop 上传地图、模型、粒子，禁止一切改动会影响竞技公平性的内容（VAC 会检测）。

---

## 三、Steam Workshop：主要入口

V 社游戏的 Mod 主要通过 Steam Workshop 分发：

1. 打开 Steam，进入游戏页面，右侧「创意工坊」。
2. 找到想要的 Mod 点「订阅」。
3. Steam 自动下载到 `steamapps/workshop/content/<appid>/<workshop_id>/`。
4. 启动游戏，Mod 通常自动生效——Workshop 已被游戏 launcher 或引擎注册为 SearchPath。

**取消订阅** = 卸载。Workshop Mod 会自动更新。

### 主要游戏的 Workshop 位置

| 游戏 | Workshop | 特色 |
|---|---|---|
| Garry's Mod | 巨大——Addon、地图、模型、脚本无所不包 | 基础平台 Mod 的元祖 |
| Team Fortress 2 | 皮肤、地图、UI 皮肤；部分服务器只用 Workshop 地图 | |
| L4D2 | 巨大——地图、角色皮肤、武器、界面 | 单人和合作模式都能开 Mod |
| Portal 2 | Perpetual Testing Initiative 内置关卡编辑器发布 | |
| CS2（原 CS:GO 位置） | 皮肤在官方 Steam Market；社区 Workshop 主要是地图；CS:GO Legacy 分支仍能玩老 Mod | 竞技模式禁用大部分社区 Mod |
| DOTA 2 | 英雄皮肤、Hud、语音、Custom Games | Custom Games 是完全自建的独立玩法 |
| Half-Life: Alyx | 关卡、Mod、TC | 用 Alyx Workshop Tools 制作 |

---

## 四、手动安装（Source）

Workshop 不能满足时（老 Mod、被官方下架的 Mod、私服自定义资源），走手动路线。

### 4.1 `custom/` 目录（CS:GO、L4D2 等）

```text
Steam/steamapps/common/Counter-Strike Global Offensive/csgo/
├── gameinfo.txt
├── pak01_dir.vpk            ← 游戏原版资源
├── maps/
├── materials/
└── custom/                  ← 玩家 Mod 放这里
    ├── my_hud_mod/          ← 每个 Mod 独立子目录
    │   └── materials/
    │       └── panorama/
    ├── my_skin_mod.vpk      ← 也可以直接放 .vpk
    └── ...
```

- 每个 Mod 一个子目录或一个 `.vpk`。
- 子目录内部按游戏原始资源路径组织（`materials/`、`models/`、`sound/`、`scripts/` 等）。
- 因为 `gameinfo.txt` 里 `custom/*` 通配符最先扫描，Mod 会覆盖原版同路径资源。

### 4.2 L4D2 的 `addons/` 目录

L4D2 把玩家 Mod 都放在：

```text
Steam/steamapps/common/Left 4 Dead 2/left4dead2/addons/
├── my_map.vpk               ← 地图 Mod
├── my_survivor_reskin.vpk   ← 角色皮肤
└── mymod/                   ← 散装目录形式也可以
```

`.vpk` 双击默认由 L4D2 的 Add-on Installer 打开并自动放到这里。

### 4.3 Garry's Mod 的 `addons/`

GMod 有专门的 addons 系统：

```text
Steam/steamapps/common/GarrysMod/garrysmod/addons/
├── wire.gma                 ← Workshop 订阅的 .gma
├── wiremod/                 ← 散装 Addon
│   ├── addon.json           ← Addon 元数据
│   ├── lua/
│   ├── models/
│   └── materials/
```

- **Workshop 订阅**：自动放 `.gma` 到这里，自动挂载。
- **手动散装 Addon**：解压后放到 `addons/`，游戏启动时自动扫描。
- 制作 Addon 时用 GMod 自带的 `gmad.exe` 工具打包成 `.gma`。

### 4.4 老游戏（HL2、CSS、TF2）与 sourcemods

TF2 早期 Mod 更零碎：直接把散装文件放 `tf/` 里，或者用 `custom/` 子目录。

大型总替换 Mod（比如把 HL2 改成完全不同的游戏）走 **`sourcemods/`** 目录：

```text
Steam/steamapps/sourcemods/
├── HL2_TotalConversion/
│   ├── gameinfo.txt         ← 声明它是一个独立的 Source 游戏
│   ├── maps/
│   ├── materials/
│   └── ...
```

Steam 会自动识别 `sourcemods/` 下每个带 `gameinfo.txt` 的子目录当成独立游戏在库里显示，可以直接从 Steam 启动。这类总替换 Mod 有：**Black Mesa**（早期版本）、**Neotokyo**、**Zombie Panic! Source**、**Dystopia**、**Insurgency Mod**（早期非独立版）等。

---

## 五、手动安装（Source 2）

Source 2 目前的手动 Mod 空间比 Source 更窄——官方倾向让所有 Mod 都走 Workshop。

### 5.1 CS2 的 Workshop 与地图

CS2 玩家 Mod 主要走 Workshop 订阅 + 服务端 `-usermaps` 加载：

- 地图订阅后放在 `steamapps/workshop/content/730/<map_id>/`。
- 官方竞技匹配禁用非官方地图，只在社区服务器或本地机器上生效。

### 5.2 DOTA 2 与 Custom Games

- 英雄外观 / Hud：Workshop 订阅即用。
- Custom Games：作者用 Dota 2 Tools 开发独立 mode，玩家在游戏内的 Arcade 里搜索订阅。
- 完全自建的 Custom Game 是「跑在 Source 2 引擎上的自定义游戏」，代码用 Lua + Panorama JS。

### 5.3 Half-Life: Alyx 的 Workshop Tools

Alyx 是**首个开放完整 Workshop 制作工具的 Source 2 游戏**：

- Steam 库里选择「Half-Life: Alyx - Workshop Tools」（免费工具）。
- 自带 Hammer 2、Model Viewer、粒子编辑器。
- 制作 Add-on 后一键发布到 Workshop。
- 玩家侧：订阅 Workshop 关卡，进游戏 → Add-ons → 加载。

---

## 六、Garry's Mod 深入

GMod 是 Source 引擎最活跃的 Mod 平台，值得单独讲。

### 6.1 常见 Addon 类型

| 类型 | 特点 | 存放位置 |
|---|---|---|
| **地图（Maps）** | `.bsp` + 相关资源 | `addons/<mapname>/maps/` |
| **模型（Models / Playermodels）** | 玩家/道具的模型 + 贴图 | `addons/<name>/models/` + `materials/` |
| **武器（SWEP）** | Scripted Weapon Entity | `addons/<name>/lua/weapons/` |
| **实体（SENT）** | Scripted Entity（可放置的自定义实体） | `addons/<name>/lua/entities/` |
| **载具（SCar）** | Scripted Vehicle | `addons/<name>/lua/vehicles/` |
| **游戏模式（Gamemode）** | 完整游戏规则（TTT、DarkRP、Prophunt） | `gamemodes/<name>/` |
| **工具（Tools）** | 工具枪的自定义工具 | `addons/<name>/lua/weapons/gmod_tool/stools/` |

### 6.2 Content-only Addon

GMod 里有一大类 Addon 是**纯资源**——从其他 Source 游戏（HL2、CSS、L4D2）搬过来的模型贴图，让服务器和地图能用它们。

例：**Counter-Strike: Source Content**（提供 CS:S 的贴图、模型、音效）。装了它，需要 CS:S 资源的地图就不会显示紫黑色格子（missing texture）。

### 6.3 私人 collection 分发

- Steam Workshop 支持「Collection」——把一堆 Addon 打包成一个集合，服务器可以要求玩家先订阅这个集合才能加入。
- `resource.AddWorkshop( "<id>" )` 让服务器自动向连接的玩家推送订阅需求。

---

## 七、目录结构总结

### CS:GO / CS:S / TF2（Source 常见）

```text
<游戏根目录>/
├── <gamename>/                  ← csgo、cstrike、tf 之类
│   ├── gameinfo.txt              ← SearchPaths 定义
│   ├── pak01_*.vpk               ← 原版资源
│   ├── custom/                   ← 玩家 Mod（每个一个子目录或 .vpk）
│   └── maps/、materials/、models/ 等原版资源目录
```

### L4D2

```text
Left 4 Dead 2/left4dead2/
├── addons/                       ← 玩家 Mod 主目录
│   ├── some_map.vpk
│   └── ...
```

### Garry's Mod

```text
GarrysMod/garrysmod/
├── addons/                       ← 玩家 Addon
│   ├── xxx.gma                   ← Workshop 订阅的
│   └── xxx/                      ← 散装 Addon
├── gamemodes/                    ← 游戏模式
│   ├── sandbox/                  ← 官方沙盒
│   └── ttt/、darkrp/ 等
└── data/                         ← 玩家数据、Addon 生成的持久化数据
```

### Source 2 游戏（CS2 / DOTA 2 / Alyx）

订阅的 Workshop Mod 在 `steamapps/workshop/content/<appid>/<workshop_id>/`；官方 Addon 系统（Alyx）在 `<game>/steam_tmp/`、`<game>/game/hlvr_addons/` 之类的位置，具体因游戏而异。

---

## 八、常见问题排查

### Q1：Mod 装了但没生效

- **CS:GO / CS:S**：确认放在 `<gamename>/custom/` 而不是根目录；散装文件的话内部路径要和游戏一致（`materials/panorama/...`）。
- **L4D2**：`.vpk` 双击装的话确认它到了 `addons/` 而不是被 Steam 覆盖到别处；散装文件仍然要在 `addons/<name>/` 里保留 `materials/`、`models/` 层级。
- **GMod**：`.gma` 会被自动挂载，散装 Addon 需要有 `addon.json`。
- 通用检查：进游戏控制台（打开控制台设置：`~`），输入 `path` 命令能查看引擎当前的 SearchPath 列表；不在列表里的 Mod 加载不了。

### Q2：紫黑色 missing texture / 缺贴图

Source 游戏的经典问题：Mod 引用了 CS:S / HL2 的贴图但你没装那个游戏。

- 装原始游戏（拥有 CS:S 就是最佳解决办法）。
- 或者装社区打包的 **Content Pack**（`counter-strike-source-shared-content` 等）到 GMod addons。

### Q3：VAC 封号风险

- **CS:GO / CS2 竞技匹配**中开客户端注入类 Mod（外挂、内存 hack、部分 UI Hack）会触发 VAC。
- **Workshop 上通过审核的 Mod** 一般不会封——它们只改本地文件不上报服务器。
- **私服** / **社区服**通常不启用 VAC，可以随意开各种 Mod。
- 简单原则：**Workshop 订阅的正规 Mod 安全；来路不明的 `.dll` 注入器不要碰**。

### Q4：Mod 冲突

由于 Source 是「先找到就用」，两个 Mod 改同一个文件时字母序靠前的赢：

- 用 `_` 或 `AAA_` 前缀强行排前。
- GMod 里 Addon 优先级由文件名决定；也可以在 `data/addons.json` 里手动配置。

### Q5：服务器 Mod 强制订阅慢

GMod 或 CS 私服要求下载 500MB+ 的地图/资源包时用 `-usermaps`、`sv_downloadurl`（Fast Download）：

- 加速下载：服务器管理员设置 CDN 提供压缩过的 `.bz2` 文件。
- 玩家侧：Steam Workshop 订阅在加入前先完成，比运行时下载快得多。

### Q6：无法启动 sourcemods 里的总替换 Mod

- 检查 `sourcemods/<modname>/gameinfo.txt` 是否正确写着游戏识别信息。
- 关闭 Steam 重开，让它重新扫描 sourcemods 目录。
- 有些老 sourcemod 需要 Source SDK Base 2007/2013（Steam 免费下载）。

---

## 九、Hammer 编辑器与制作 Mod

想自己做 Mod 而不只是装 Mod：

### 9.1 Source 时代

- 安装 **Source SDK** 或对应游戏的 Authoring Tools。
- **Hammer Editor** 做地图（`.vmf` → 编译 `.bsp`）。
- **Model Viewer** / **Studiomdl** 处理 `.mdl` 模型。
- **VIDE** 或 **GCFScape** 打包 / 解包 `.vpk`。
- Squirrel、VScript、Lua（GMod）写脚本。

### 9.2 Source 2 时代

- **Alyx Workshop Tools**、**DOTA 2 Tools**、**CS2 Workshop Tools**（在 Steam 库里免费下）。
- Hammer 2 是全新的关卡编辑器，UI 现代化很多。
- 用 Panorama（HTML/CSS/JS 风格）写 UI；用 Lua 或 Panorama JS 写玩法。

制作后可以一键发布到 Workshop，Valve 会审核后上架。

---

## 十、卸载

- **Workshop 订阅的 Mod**：Steam 上取消订阅即可，本地文件会自动清理。
- **手动装的 Mod**：删除 `custom/` / `addons/` 里对应的子目录或 `.vpk`。
- **sourcemods**：删除 `steamapps/sourcemods/<modname>/`，重启 Steam。
- **完全清理游戏**：Steam「验证游戏文件完整性」把原版恢复到干净状态；对 Workshop 订阅内容无效，需要手动取消订阅。

---

## 十一、安全边界

- **VAC 保护游戏**：只装 Workshop 上审核过的 Mod；来路不明的可执行 `.dll` / `.exe` 不要装到游戏目录。
- **社区服务器可能要求特定 Mod / 客户端补丁**，加入前评估服主是否可信。
- **不要用 Mod 破解付费皮肤**——CS 系列尤其严重，会封号；DOTA 2 装皮肤客户端可视化 Mod 只影响自己视角，不影响他人。
- **Garry's Mod 的 Lua Addon 是可执行代码**：从大 Workshop 作者、审核过的 Collection 下比较安全；小服务器要求你订阅陌生 Addon 时先看内容。

---

## 十二、流程总结

```text
① 优先 Steam Workshop 订阅（一键装 + 自动更新）
       ↓
② Workshop 没有的 Mod 用手动安装：
   - CS/TF2 → <game>/custom/
   - L4D2 → left4dead2/addons/
   - GMod → garrysmod/addons/
   - Source 总替换 → steamapps/sourcemods/
       ↓
③ 检查 gameinfo.txt / gameinfo.gi 是否包含预期 SearchPath
       ↓
④ 进游戏后用控制台 path 命令核对是否被识别
       ↓
⑤ 竞技游戏（CS2、CS:GO）避开可能触发 VAC 的注入类 Mod
       ↓
⑥ 卸载：Workshop 取消订阅 / 手动装的直接删目录
```

> 核心口诀：**Workshop 是主线 → 加载顺序是"先找到就用" → 保留 Mod 内部资源路径 → 竞技游戏别乱注入 → 冲突改文件名字母序。**

---

## 参考资料

- [Valve Developer Community（VDC）](https://developer.valvesoftware.com/wiki/Main_Page)
- [Source SDK](https://developer.valvesoftware.com/wiki/Source_SDK)
- [Source 2 Documentation](https://developer.valvesoftware.com/wiki/Source_2)
- [Garry's Mod Wiki](https://wiki.facepunch.com/gmod/)
- [Steam Workshop](https://steamcommunity.com/workshop/)
- [Half-Life: Alyx Workshop Tools](https://developer.valvesoftware.com/wiki/Half-Life:_Alyx_Workshop_Tools)
- [Hammer Editor 教程（VDC）](https://developer.valvesoftware.com/wiki/Category:Level_Design)
- [GCFScape（VPK 查看工具）](https://developer.valvesoftware.com/wiki/GCFScape)
- [Source Mods on ModDB](https://www.moddb.com/engines/source)
