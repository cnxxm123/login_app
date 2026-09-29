# Minecraft 游戏 Mod 安装指南（Java 版：Forge / Fabric / Quilt / NeoForge）

> 本指南聚焦 **Minecraft Java Edition** 的 Mod 生态。基岩版（Bedrock Edition，包括 Windows 10/11 UWP、Xbox、Switch、手机版）的 **Add-on** 走完全不同的官方规范，本文最后一节简要说明区别。
>
> **总规则**：Mod、加载器（Forge / Fabric / Quilt / NeoForge）、Minecraft 版本、Java 版本**四者必须匹配**，且**Mod 是给哪个加载器写的就只能装到哪个加载器**——同一份 Mod 一般不会同时兼容 Forge 和 Fabric，请以 Mod 页面为准。

---

## 一、先分清两个版本

| | Java 版 | 基岩版 |
|---|---|---|
| 语言 | Java | C++ |
| 平台 | Windows / macOS / Linux | Win10/11 UWP、Xbox、Switch、PS、iOS、Android |
| Mod 概念 | 加载器 + `.jar` Mod（**丰富、开放**） | **Add-on**：`.mcpack` / `.mcaddon` / `.mcworld`（官方规范，功能受限） |
| Mod 生态 | 极大：Forge、Fabric、Quilt、NeoForge | 有限：主要在 Marketplace 与社区 Add-on |
| 商店整合 | 无 | Minecraft Marketplace |
| 服务器 | 允许自建，主机随便；Bukkit/Spigot/Paper 生态成熟 | Realms / Bedrock Dedicated Server；Add-on 支持有限 |
| 版本一致性 | 每个中版本（1.20.1、1.21.1 等）Mod 都不兼容前后版本 | 由 Marketplace 统一分发，兼容性好一些 |

**Mod 生态的重量级、灵活度都是 Java 版**。想装真正意义上的「Mod」（新方块、新维度、新机器、新玩法），Java 版是唯一路径。

---

## 二、四个主要加载器

Java 版 Mod 加载器有四个，都做同一件事——挂钩 Minecraft 客户端 / 服务端，加载放在 `mods/` 里的 `.jar` Mod。但**它们的 API、Mixin 生态、事件系统各不兼容**。

| 加载器 | 起源与特点 | 主要生态 | 推荐场景 |
|---|---|---|---|
| **Forge** | 最老、最大的 Mod 平台，从 1.3.2 时代就在 | 工业/魔法/自动化大型 Mod：IC2、机械动力（Create）、Botania、Applied Energistics 2 | 玩大型综合整合包（GTNH、FTB、TerraFirmaCraft） |
| **NeoForge** | 2023 从 Forge 分叉出来的社区分支，1.20.1 之后是许多整合包的默认选择 | 与 Forge Mod 大量兼容，逐渐吸引 Mod 作者迁移 | 新版本（1.20.4 之后）玩 Forge 系 Mod |
| **Fabric** | 2018 出现，轻量、更新快、Mixin 原生集成 | 性能/画质/性能优化 Mod：Sodium、Iris、Lithium、Xaero's Map | 玩画质党整合包、纯性能优化、光影 |
| **Quilt** | 2022 从 Fabric 分叉；理论上兼容 Fabric Mod | 生态较小，Mod 数量远少于 Fabric 本体 | 特定 Quilt Mod、或想尝试更严格的模块系统 |

**怎么选**：**看 Mod 页面写的是哪个加载器就用哪个**。整合包（Modpack）会告诉你固定用哪个。不要在同一个 Minecraft 版本目录里同时装 Forge 和 Fabric——它们抢同一个 `mods/` 目录会互相报错。

**Forge / NeoForge 的关系**：现在（1.20.1+）它们是两套独立生态，Mod 作者要么二选一，要么发两个版本。**看清楚是 Forge 的 Mod 还是 NeoForge 的 Mod，不能混装**。

---

## 三、Java 版本对应关系

Minecraft 每个大版本对 Java 有强制要求，装错版本连 Minecraft 都启动不了：

| Minecraft 版本 | 需要的 Java 版本 |
|---|---|
| 1.16 及以下 | Java 8（推荐 OpenJDK 8 或 Zulu 8） |
| 1.17 – 1.20.4 | Java 17 |
| 1.20.5+（含 1.21+） | **Java 21** |

**官方启动器**（Minecraft Launcher）会**自动下载并使用对应的 Java 版本**，不需要自己管。但如果你用第三方启动器（Prism、HMCL、MultiMC）或想跑服务端，就要自己装 Java。

**推荐发行版**（都是免费开源的 OpenJDK 构建，不要用 Oracle 商用 JDK）：

- [Adoptium Temurin](https://adoptium.net/)（原 AdoptOpenJDK，最主流）
- [Azul Zulu](https://www.azul.com/downloads/?package=jdk)
- [Amazon Corretto](https://aws.amazon.com/corretto/)

---

## 四、原理：加载器和 Mod 是怎么工作的

理解下面几点，就明白为什么装 Mod 时有那么多细节要对齐：

### 4.1 Minecraft 是纯 Java 程序

- 客户端本体（`minecraft-<version>.jar`）就是一堆 `.class` 字节码 + 资源，位于 `.minecraft/versions/`。
- **原版没有任何 Mod 接口**，也没有事件系统、没有插件加载点。
- 想加 Mod，就必须在 Java 类加载或字节码层面动手脚——加载器就是干这个的。

### 4.2 加载器的注入方式

- **Forge / NeoForge**：提供了 **FML（Forge Mod Loader）** 和自家的事件总线（`@Mod`、`@SubscribeEvent`）。它启动时先接管 Minecraft 的类加载器（ClassLoader / ModLauncher），把每个 Mod 的 `.jar` 加进 classpath 并注册它的事件监听器。老版本还配合 Access Transformers 改字段/方法可见性。
- **Fabric / Quilt**：更轻量。使用 **Fabric Loader + Mixin**（Mixin 是一个字节码补丁库）。Mod 通过写 Mixin 类，用注解声明「我要给 `MinecraftClient.tick()` 前面插一段代码」；Fabric Loader 在类加载时用 Mixin 引擎重写字节码，把 Mod 的代码嵌入原版方法里。
- **Forge 后期版本也大量使用 Mixin**——现在几乎所有 Mod 都或多或少依赖 Mixin。

### 4.3 为什么每次版本更新 Mod 都要重编译

Mixin 和 AT 挂钩的是**具体类名 / 方法名 / 字段名**。Minecraft 每个版本都会经过 obfuscation（混淆）——把类名从可读的 `PlayerEntity` 变成 `ahn`、`p_35672_` 之类。Forge/Fabric 用 **mappings**（Mojang 官方的 obf-map 或社区维护的 MCP/Yarn）反向映射到人类可读名字。

版本更新时映射会变，之前指向 `PlayerEntity.attack()` 的 Mixin 可能就找不到对应方法了。所以：

- **1.20.1 的 Mod 不能装到 1.21**。
- **1.21 的 Mod 不能装到 1.21.1**（是的，小版本也可能不兼容，取决于 Mojang 那次改了什么）。

### 4.4 Fabric API / Forge 核心库

Fabric 生态里**几乎所有 Mod 都依赖 [Fabric API](https://modrinth.com/mod/fabric-api)**——它是 Fabric 官方封装的一层公共事件/工具库。装 Fabric Mod 之前先装 Fabric API 就对了。

Forge 是把公共库直接绑进加载器里，不用单独装，但很多 Mod 会有各自的前置库（`Cloth Config`、`Architectury API`、`GeckoLib` 等）。

### 4.5 Mod `.jar` 里都有什么

一个典型 Mod jar 展开：

```text
mod-1.0.0.jar
├── META-INF/
│   ├── MANIFEST.MF
│   └── mods.toml         ← Forge/NeoForge 元数据（Mod ID、版本、依赖）
├── fabric.mod.json       ← Fabric Mod 用这个替代 mods.toml
├── com/author/mod/       ← 编译后的 Mod 代码 .class
├── assets/               ← 客户端资源（贴图、模型、语言）
│   └── modid/
│       ├── textures/
│       ├── models/
│       └── lang/
├── data/                 ← 数据包：物品配方、战利品表、进度、标签
│   └── modid/
├── pack.mcmeta           ← 资源/数据包版本
└── modid.mixins.json     ← Mixin 配置（如果有）
```

游戏启动时加载器读元数据文件（`mods.toml` 或 `fabric.mod.json`），确认 Mod ID、版本、依赖是否满足，然后把类加进 classpath、把 assets / data 挂进虚拟资源包系统。

---

## 五、启动器选择

### 5.1 官方 Minecraft Launcher

Mojang 官方启动器。缺点：**没有 Mod 版本管理**——你在同一个「1.20.1」profile 里装了 Mod，切回原版就得手动改回。玩多整合包尤其麻烦。

优点：**Java 自动管理**、账号系统正规、Xbox Live 联动没问题。

### 5.2 第三方启动器（强烈推荐）

装 Mod 强烈推荐使用第三方启动器，因为它们支持「一个整合包一个实例（Instance）」——每个实例有独立的 `mods/`、配置、存档，互不干扰。

| 启动器 | 特点 | 平台 |
|---|---|---|
| **[Prism Launcher](https://prismlauncher.org/)** | MultiMC 分支、社区维护、开源；支持 CurseForge/Modrinth/FTB/Technic 一键导入整合包 | Windows / macOS / Linux |
| **[CurseForge App](https://www.curseforge.com/download/app)** | CurseForge 官方；对 CurseForge 上的整合包深度整合 | Windows / macOS |
| **[Modrinth App](https://modrinth.com/app)** | Modrinth 官方；Modrinth 生态优先 | Windows / macOS / Linux |
| **[HMCL](https://hmcl.huangyuhui.net/)** | 中文社区常用；配置直观、简中友好 | Windows / macOS / Linux |
| **[ATLauncher](https://atlauncher.com/)** | 老牌整合包启动器 | 多平台 |

**Prism Launcher 是当前最中立、最好用的选择**——不锁定任何 Mod 平台，界面清晰，能直接从 CurseForge/Modrinth 抓整合包。

---

## 六、安装步骤

### 6.1 手动安装 Fabric + 装几个 Mod

**目标**：Minecraft 1.20.1 + Fabric + Sodium（性能优化）+ Iris（光影支持）。

1. 装 [Adoptium Temurin JDK 17](https://adoptium.net/temurin/releases/?version=17) 并把 `java` 加入 PATH。
2. 用 Minecraft 官方启动器进一次 1.20.1 原版，确保 `.minecraft` 目录存在。
3. 从 [fabricmc.net/use](https://fabricmc.net/use/) 下载 **Fabric Installer**（`.jar`）。
4. 双击运行 Fabric Installer，选择 「Client」标签页，Minecraft Version = 1.20.1，Loader Version 用推荐版本，Install Location 指向 `.minecraft`，点击「Install」。
5. 装好之后官方启动器里会多一个「fabric-loader-x.y.z-1.20.1」profile，选它启动一次，确认能进主菜单（右下角显示 Fabric 版本信息）。
6. 关掉游戏，把下面文件下载好丢进 `.minecraft/mods/`：
   - [Fabric API](https://modrinth.com/mod/fabric-api)（前置，必装）
   - [Sodium](https://modrinth.com/mod/sodium)（性能优化）
   - [Iris Shaders](https://modrinth.com/mod/iris)（光影支持，含 Sodium 兼容层）
7. 用 fabric profile 再启动，主菜单 → 视频设置 里会有 Sodium 面板；世界内按 O 呼出光影管理。

### 6.2 用 Prism Launcher 装整合包（推荐）

Prism Launcher 让 1 和 2 一起完成，还提供实例隔离。

1. 装 Prism Launcher，登录 Microsoft 账号。
2. 「Add Instance」→ 从「Modrinth」或「CurseForge」标签页搜想要的整合包（例如 「Fabulously Optimized」性能整合包）。
3. 选择版本、点击「OK」，Prism 会自动下载 Minecraft、加载器、所有 Mod、依赖。
4. 实例创建好后双击启动。
5. 想在里面加自己的 Mod：右键实例 → 「Edit」→ 左侧「Mods」→ 「Add file」（本地文件）或「Download mods」（内建 Modrinth 搜索）。

### 6.3 手动安装 Forge 或 NeoForge

流程类似 Fabric，只是安装器换一个：

- Forge：从 [files.minecraftforge.net](https://files.minecraftforge.net/) 下载对应 MC 版本的 Installer。
- NeoForge：从 [neoforged.net](https://neoforged.net/) 下载。

装完启动器会多一个 forge/neoforge profile。之后同样把 `.jar` 丢进 `.minecraft/mods/`——但注意**只装 Forge/NeoForge 的 Mod**，Fabric Mod 会因为找不到 `mods.toml` 里的入口点而失败。

---

## 七、目录结构

`.minecraft` 位置：

- Windows：`%APPDATA%\.minecraft\`
- macOS：`~/Library/Application Support/minecraft/`
- Linux：`~/.minecraft/`

第三方启动器每个实例有自己的目录（Prism 是 `<Prism data>/instances/<实例名>/.minecraft/`）。

装完 Mod 后的典型结构：

```text
.minecraft/
├── versions/                    ← 每个 MC 版本的核心 jar 和 profile
│   ├── 1.20.1/
│   ├── fabric-loader-0.15.11-1.20.1/
│   └── forge-1.20.1-47.2.20/
├── mods/                        ← Mod 主目录：把 .jar 丢这里
│   ├── fabric-api-0.92.2.jar
│   ├── sodium-fabric-0.5.11.jar
│   └── iris-1.7.0.jar
├── config/                      ← Mod 配置文件（首次运行生成）
│   ├── sodium-options.json
│   └── iris.properties
├── resourcepacks/               ← 资源包（材质包、语言包）
├── shaderpacks/                 ← 光影包（.zip）
├── saves/                       ← 存档
├── logs/                        ← 客户端日志
│   ├── latest.log               ← 最近一次运行的日志
│   └── debug.log
├── crash-reports/               ← 崩溃报告
├── options.txt                  ← 客户端设置
├── launcher_profiles.json       ← 官方启动器 profile
└── assets/                      ← Minecraft 资源缓存
```

**关键约定**：

- Mod 是 `.jar`，不要解压。
- 资源包和光影包也是 `.zip` 或 `.jar`，不要解压。
- 每个 Minecraft 大版本用独立的 `.minecraft/` 或独立实例目录，别混。
- 崩溃报告在 `crash-reports/`，一份是启动崩溃时用的，一份是运行中崩溃的。

---

## 八、整合包（Modpack）

**整合包**是一份预先配好加载器 + Mod + 配置 + 材质包 + 光影的完整包。玩综合类内容强烈推荐用整合包，避免自己一个个装 100+ 个 Mod 相互冲突。

主流分发平台：

- **[CurseForge Modpacks](https://www.curseforge.com/minecraft/modpacks)**：数量最多，Prism 和 CurseForge App 都能一键导入。
- **[Modrinth Modpacks](https://modrinth.com/modpacks)**：新兴平台，UI 好，格式开放（`.mrpack`）。
- **[FTB App](https://feed-the-beast.com/ftb-app)**：老牌 FTB 系整合包。
- **[Technic Launcher](https://www.technicpack.net/)**：老玩家可能熟悉，现在生态较小。

**知名整合包**：

| 整合包 | 类型 | 加载器 |
|---|---|---|
| GTNH（GregTech: New Horizons） | 硬核工业 + 电力 + 长线数千小时 | Forge 1.7.10 |
| ATM 9（All the Mods 9） | 综合工业/魔法/科技 | Forge/NeoForge 1.20.1 |
| Better MC | 精心整合的高画质冒险 | Fabric / Forge 各版本 |
| Fabulously Optimized | 纯性能 + 画质优化 | Fabric |
| Prominence II | RPG 风格 | Fabric |
| Create: Astral | 机械动力主题 | Forge/Fabric |

---

## 九、光影 / 资源包 / 数据包

这三类**不是 Mod**，是官方原生支持的内容格式，但一般也和 Mod 一起讨论。

### 9.1 资源包（Resource Pack）

- 位置：`.minecraft/resourcepacks/<name>.zip`。
- 作用：替换贴图、模型、语言、声音；不改玩法逻辑。
- 主流站点：CurseForge、Modrinth、planetminecraft.com。

### 9.2 光影包（Shader Pack）

- 位置：`.minecraft/shaderpacks/<name>.zip`。
- 前置：Java 版需要 **OptiFine**（老选择）或 **Iris + Sodium**（新选择，Fabric 生态更主流）。
- 知名光影：BSL、Complementary、Sildur's、SEUS、Shrimple。

### 9.3 数据包（Datapack）

- 位置：**每个存档独立**，在 `saves/<存档>/datapacks/<name>.zip`。
- 作用：改配方、战利品表、进度、维度生成，官方原生支持，不需要 Mod。
- 主流站点：[vanillatweaks.net](https://vanillatweaks.net/)、Modrinth 的 Datapacks 分区。

---

## 十、常见问题排查

### Q1：启动器点了没反应 / 闪退

- 打开 `.minecraft/logs/latest.log`，最后几十行通常有原因。
- 90% 是 **Java 版本不对**。1.17+ 需要 Java 17，1.20.5+ 需要 Java 21。第三方启动器要在 Java 设置里指定。
- 显存不够：`launcher_profiles.json` 或启动器里改 JVM 参数 `-Xmx` 到 4G/6G/8G，不要给太多（超过 12G 反而变慢）。

### Q2：Mod 之间不兼容 / 版本冲突

- 看 `crash-reports/` 里最新崩溃报告，末尾有堆栈和罪魁 Mod。
- 检查每个 Mod 是否为当前 MC 大版本 + 当前加载器编写。
- 前置库缺失：崩溃日志里搜 `Missing dependency` / `requires`。
- 二分法排错：一次把 `mods/` 里一半 Mod 移出去，看还崩不崩，逐步定位。

### Q3：Fabric API 提示版本不对

Fabric API 的版本要匹配 MC 版本（`fabric-api-x.y.z+1.20.1` 里的 `+1.20.1` 就是它绑定的 MC 版本）。装错版本会启动崩溃或黑屏。

### Q4：Mod 说要 Forge，但我装了 Fabric

不能通用。要么去 Modrinth/CurseForge 搜同名 Mod 的 Fabric 版本（作者如果发了两个版本），要么切换加载器。

### Q5：整合包卡加载 / 内存不足

- 大整合包（如 GTNH）需要 8-12G 内存，改启动器的最大 RAM。
- Java 参数加 `-Xmx8G -XX:+UseG1GC`（Prism/CurseForge 有内建预设）。
- 装 Sodium / Lithium / Ferrite Core / FastLoad 之类的性能优化 Mod。
- SSD 也很关键，HDD 加载大整合包会长时间黑屏。

### Q6：光影没生效

- 检查是不是装了 OptiFine + Iris（两者冲突）。
- 确认光影包是 `.zip`，不要解压。
- 光影包里可能有多个预设，进游戏选具体的那个（不选就是默认）。

### Q7：多人服要装同样的 Mod 吗

- 大多数 Forge/Fabric Mod：**服务端和客户端都要装**，且版本严格一致。
- 纯客户端 Mod（Minimap、Sodium 之类）：**只在客户端装**。
- 纯服务端 Mod（性能优化、后台工具）：只在服务端装。
- Mod 页面通常会写清楚「Client-only」/「Server-only」/「Required on both」。

---

## 十一、卸载

- 单个 Mod：从 `mods/` 或启动器实例的 Mod 列表里删除 `.jar`。
- 加载器：在官方启动器里删除对应 profile；`.minecraft/versions/` 里删除对应文件夹。
- 完整清空：删除整个 `.minecraft/`（会同时清掉存档，先备份 `saves/`）。
- 第三方启动器：直接删实例目录。
- 装了 Mod 后创建的存档，**卸载 Mod 后无法在原版打开**——原版会因缺少方块/物品 ID 而拒绝加载或删掉未知内容。想回原版建议开新档。

---

## 十二、基岩版 Add-on 简介

基岩版没有真正意义上的 Mod。它有官方规范的 **Add-on**：

- **Behavior Pack**：修改实体、物品、方块行为，用 JSON + JavaScript API。
- **Resource Pack**：改贴图、模型、界面。
- **World Template**：世界模板。

分发格式：`.mcpack`（单包）、`.mcaddon`（多包）、`.mcworld`（世界）。双击就能被 Minecraft 基岩版直接导入。

主要来源：**Minecraft Marketplace**（官方付费/免费），社区免费的通常来自 mcpedl.com、Modrinth 的 Bedrock 分区、MCPE Universe 等。

**基岩版 Add-on 能力远不及 Java 版 Mod**——不能加新维度、不能自由改渲染、脚本 API 是官方沙盒里的白名单。想深度魔改仍然只有 Java 版一条路。

---

## 十三、流程总结

```text
① 确认要装的 Mod 面向哪个加载器（Forge / NeoForge / Fabric / Quilt）和 MC 版本
       ↓
② 装匹配 MC 版本的 Java（1.17+ 是 17，1.20.5+ 是 21）
       ↓
③ 装第三方启动器（Prism / CurseForge / Modrinth）并新建实例
       ↓
④ 在实例里装加载器（Fabric Installer / Forge Installer 或启动器一键装）
       ↓
⑤ 装前置库（Fabric API、Architectury API、Cloth Config 等）
       ↓
⑥ 把 Mod .jar 丢进实例的 mods/，不要解压
       ↓
⑦ 启动实例；崩溃就看 logs/latest.log 和 crash-reports/
       ↓
⑧ MC 版本更新前先备份实例；Mod 生态跟进后再升级
```

> 核心口诀：**加载器与 MC 版本一致 → Java 版本对得上 → 只装当前加载器的 Mod → 装前置 → 崩溃看日志。**

---

## 参考资料

- [Minecraft 官网](https://www.minecraft.net/)
- [Forge](https://files.minecraftforge.net/) / [NeoForge](https://neoforged.net/)
- [Fabric MC](https://fabricmc.net/) / [Quilt MC](https://quiltmc.org/)
- [CurseForge Minecraft](https://www.curseforge.com/minecraft)
- [Modrinth](https://modrinth.com/)
- [Prism Launcher](https://prismlauncher.org/)
- [Fabric API（Modrinth）](https://modrinth.com/mod/fabric-api)
- [Mixin GitHub（SpongePowered）](https://github.com/SpongePowered/Mixin)
- [Adoptium Temurin JDK](https://adoptium.net/)
- [Minecraft Wiki: Bedrock Add-ons](https://minecraft.fandom.com/wiki/Add-on)
