# RE Engine 游戏 Mod 安装指南

> 本指南整理 RE Engine 游戏的通用 Mod 安装流程，适合 Resident Evil、Devil May Cry、Monster Hunter Rise、Street Fighter 6 等部分支持 REFramework 或 Fluffy Mod Manager 的游戏。
>
> **重要：RE Engine 是引擎，不是统一的 Mod 安装器。** 不同游戏的资源路径、角色编号、版本兼容性和工具支持范围可能不同。本文讲的是通用工作流，实际安装始终以“目标游戏 + 目标 Mod”的 README 和 Requirements 为准。

---

## 一、先确认适用范围

### 1. RE Engine 不等于所有卡普空游戏

卡普空有多套引擎和游戏专用技术。下面这些游戏或系列经常出现在 RE Engine Mod 生态中：

- 《生化危机 2 重制版》
- 《生化危机 3 重制版》
- 《生化危机 4 重制版》
- 《生化危机 7》
- 《生化危机 8：村庄》
- 《鬼泣 5》
- 《怪物猎人：崛起》
- 《街头霸王 6》
- 《龙之信条 2》

这不是完整兼容列表。即使两款游戏都使用 RE Engine，也不能直接互换 Mod。

### 2. 先看 Mod 指向哪款游戏

安装前确认 Mod 页面写的是：

```text
Resident Evil 4 Remake
Resident Evil 2 Remake
Devil May Cry 5
Monster Hunter Rise
```

不要把 RE4 的 `Natives`、Lua、插件或配置复制到其他游戏。

---

## 二、通用安装流程

RE Engine Mod 的大方向通常是：

```text
① 确认目标游戏和 Mod 版本
        ↓
② 安装该游戏支持的 REFramework 或其他前置
        ↓
③ 判断 Mod 类型：reframework/、Natives/ 或专用资源包
        ↓
④ 按 Mod 说明合并到游戏根目录，或交给 Fluffy 管理
        ↓
⑤ 一次只启用一个 Mod 测试
        ↓
⑥ 如果冲突，检查是否修改了相同资源路径
        ↓
⑦ 游戏更新后重新检查框架和 Mod 兼容性
```

“游戏根目录”指放着游戏主 EXE 的目录，例如：

```text
RE4 Remake/
├── re4.exe
└── ...
```

---

## 三、先安装 REFramework

### 3.1 原理：REFramework 是怎么被加载的

REFramework 用「DLL 代理注入」进入 RE Engine 游戏进程：

- **Windows 的 DLL 搜索顺序**：加载 EXE 时会先在 EXE 所在目录查找依赖 DLL，找不到才去 `System32`。RE Engine 游戏本来就会加载系统的 `dinput8.dll`（DirectInput 8 API 的一部分），REFramework 把自己伪装成 `dinput8.dll` 放到 EXE 同级目录，就会被系统优先加载。
- **加载后转发调用**：REFramework 进内存后再把真正的系统 `dinput8.dll` 加载起来，并把游戏发来的所有 DirectInput 调用转发过去。游戏完全感知不到，同时框架已经完成了注入。
- **位置敏感**：由于依赖 Windows 的 DLL 搜索顺序，REFramework 的 `dinput8.dll` **必须放在真实游戏 EXE 同级目录**。放到启动器 EXE 目录、`Binaries` 上级或错误的 `Win64/Win32` 目录都不生效。

框架注入成功后，REFramework 会去 `reframework/` 里加载三类 Mod：

| 目录 | 内容 | 说明 |
|---|---|---|
| `reframework/plugins/` | C++ 原生插件（`.dll`） | 框架初始化时加载；可深度改动游戏内部逻辑（例如 FirstNatives 就是这类插件） |
| `reframework/autorun/` | Lua 脚本（`.lua`） | 游戏进入主循环时按文件名字母序执行，可访问游戏对象、函数与事件 |
| `reframework/data/` | 插件和 Lua 的持久化数据 | 存配置、状态；一般不手动改 |

所以后续教程里“`dinput8.dll` 放游戏根目录”“Lua 放 `autorun/`”“插件放 `plugins/`”本质上是这一条注入链的三段：DLL 代理 → 框架初始化 → 加载 Mod。

### 3.2 安装步骤

如果 Mod 页面写着 `Requires REFramework`，先安装 REFramework：

1. 从 [REFramework 官方仓库](https://github.com/praydog/REFramework) 获取与目标游戏匹配的版本。
2. 关闭游戏。
3. 将对应的 `dinput8.dll` 放到与游戏 EXE 同级的根目录。
4. 启动一次游戏，确认 REFramework 能打开。
5. 常见默认菜单键是 `Insert`，但具体按键可由配置或游戏 Mod 改变。

典型结构：

```text
目标游戏根目录/
├── 游戏.exe
├── dinput8.dll
└── reframework/
    ├── autorun/
    ├── plugins/
    └── data/
```

> REFramework 的安装目录、文件名和兼容版本可能随游戏变化。不要把一个游戏的 `dinput8.dll`、配置或 `reframework` 文件夹复制到另一个游戏。

### 3.3 `reframework/` 文件夹什么时候出现？

安装 REFramework 后，先把正确的 `dinput8.dll` 放到与游戏 EXE 同级的根目录，再启动一次游戏。REFramework 成功加载后，通常会自动创建或使用：

```text
reframework/
├── autorun/     ← Lua Mod 常用目录
├── plugins/     ← REFramework 插件目录
├── data/        ← 设置和 Mod 数据
└── fonts/       ← 部分界面资源
```

并不是所有子目录都会在第一次启动时同时出现；有些目录会在安装对应 Mod 或使用相关功能后才生成。

如果游戏启动后完全没有 `reframework/`，也没有 REFramework 日志，优先检查：

- `dinput8.dll` 是否和游戏 EXE 同级；
- 是否使用了与当前游戏匹配的 REFramework 版本；
- 是否有其他 Mod 的 `dinput8.dll` 冲突；
- 是否把文件复制到了启动器目录而不是实际游戏根目录。

如果 Mod 压缩包本身带有 `reframework/`，应将它**合并到游戏根目录**，不要等待自动生成，也不要套成：

```text
游戏根目录/reframework/reframework/
```

如果压缩包只有 `Natives/` 和 `modinfo.ini`，它是资源 Mod，不一定自带 `reframework/`；通常交给 Fluffy 管理，或按作者说明使用 Loose File Loader。

---

## 四、Mod 类型分类

RE Engine Mod 压缩包大致分三类，先按压缩包里的目录结构判断，再决定用 Fluffy 管理器还是手动放。

### 4.1 类型 A：`reframework/` Mod

压缩包里通常有：

```text
reframework/
├── autorun/
├── plugins/
└── data/
```

这类 Mod 走 REFramework 的插件/Lua 加载链（参考 3.1）。安装方法：把整个 `reframework` 文件夹合并到目标游戏根目录：

```text
目标游戏根目录/
└── reframework/
    ├── autorun/
    ├── plugins/
    └── data/
```

不要把它放进：

```text
reframework/autorun/reframework/
reframework/plugins/reframework/
```

除非 Mod 作者明确要求额外的子目录。

### 4.2 类型 B：`Natives/ + modinfo.ini` 资源 Mod

压缩包常见结构：

```text
Natives/
├── STM/
│   └── ...
modinfo.ini
screenshot.png
```

**目录名含义**：

- `Natives/` 是 RE Engine 的“散装资源根目录”，游戏在开启松散加载后会从这里读单个资源文件，覆盖 pak 归档里的同路径资源（详见第六章）。
- `STM/` 是发行渠道标识（Steam），主机版会对应 `MSG`（微软）、`PS4`/`PS5` 等；PC 玩家几乎都是 `STM`。
- 里面再按游戏内部资源路径镜像组织，例如 `natives/STM/_Chainsaw/Character/...` 就是 RE4R 内部的角色资源相对路径。
- `modinfo.ini` 和 `screenshot.png` 是给 **Fluffy Mod Manager** 用的元数据（识别名称、依赖、预览），不参与游戏加载。

常见用途：

- 服装
- 角色模型
- 贴图
- 武器外观
- 场景资源
- 声音或其他游戏资源

### 4.3 类型 C：其他专用资源包

如果压缩包里有：

```text
.pak
.arc
.dll
.lua
```

但没有清晰的 `reframework/` 或 `Natives/` 结构，不能凭文件名猜安装位置。`.pak` 可能是与 REFramework 无关的游戏专用补丁包，`.arc` 是 RE Engine 前身 MT Framework 的归档格式，未必被当前游戏支持。先查看 README、发布页和 Requirements。

---

## 五、使用 Fluffy Mod Manager

### 1. 设置正确的游戏

打开 Fluffy Mod Manager，选择目标游戏，例如：

```text
Resident Evil 4 Remake
```

游戏路径应指向放有游戏 EXE 的目录，例如：

```text
E:\SteamLibrary\steamapps\common\RESIDENT EVIL 4  BIOHAZARD RE4
```

### 2. 导入资源 Mod

把 `.zip` 或 `.rar` 放入对应游戏的 Mods 目录，或者在 Fluffy 中使用：

```text
Add mod
```

选择 Mod 压缩包。

### 3. 启用并安装

1. 在列表中找到 Mod 名称。
2. 勾选基础 Mod。
3. 如果有 `addonfor=`，先安装它依赖的基础 Mod。
4. 选择一个需要的外观/风格变体。
5. 点击 **Install mods**。
6. 启动游戏测试。

Fluffy 的优点是可以：

- 开关 Mod
- 管理附加组件
- 减少手动覆盖原文件的风险
- 更方便恢复原版
- 识别 `modinfo.ini` 中的 Mod 名称和依赖

> 一个 Mod 包可能包含多个可选变体，例如基础服装、隐藏服装、Style 2、Style 3、油身、湿身。不要默认全部同时启用。

---

## 六、手动安装 `Natives` Mod

手动安装只建议在你确认该 Mod 支持手动安装时使用。

### 1. 复制到游戏根目录

解压 Mod 后，将 `Natives` 合并到目标游戏根目录：

```text
目标游戏根目录/
└── Natives/
    └── STM/
        └── ...
```

以 RE4 为例：

```text
E:\SteamLibrary\steamapps\common\RESIDENT EVIL 4  BIOHAZARD RE4\Natives\STM\...
```

不要放进：

```text
reframework/autorun/
reframework/plugins/
reframework/data/
```

### 2. 哪些游戏需要开启散装文件加载

**原理**：RE Engine 正常运行时会从游戏内置的 pak 归档（`re_chunk_000.pak` 等）里按索引读资源。开发期为了方便美术/程序快速替换单个文件，引擎保留了另一条路径：**如果游戏根目录下有 `natives/<平台>/<资源相对路径>` 的散装文件，先读这个，再回落到 pak**。这就是所谓的 Loose File Loader / FirstNatives 生效的机制——它并没有解包 pak，只是让引擎多走了一次“先看散装再看归档”的判断。

`natives/` 文件夹是 RE Engine 的开发调试功能，早期发行的几个游戏（RE2R/RE3R）保留了代码但关掉了这个后门，后续新游戏则放开了：

| 游戏 | 是否需要 FirstNatives |
|------|---------------------|
| RE2R / RE3R（无光追版） | **需要**（首批上 PC 的 RE Engine 游戏，发行配置关了散装加载） |
| RE2R / RE3R（光追版） | 不需要（光追更新后恢复了原生支持） |
| RE4R / RE8 / 街霸 6 / 龙之信条 2 | 不需要（原生支持 `natives/`） |
| 生化 7 / DMC5 | 看情况，无光追版可能需要 |

> **判断方法**：建个 `natives/` 把皮肤解压进去启动游戏，没生效就装 FirstNatives，生效就不用管。装了也不会出错，它只是个开关。

开启散装文件加载有两种方式：

| 方式 | 做法 | 适用 |
|------|------|------|
| **FirstNatives 插件**（推荐） | 把 `FirstNatives.dll` 丢进 `reframework/plugins/`，永久生效 | 已装 REFramework 的游戏 |
| **LooseFileLoader 配置** | 打开该游戏的 REFramework 配置文件（如 RE4 的 `re2_fw_config.txt`），把 `LooseFileLoader_Enabled=false` 改为 `true` | 已装 REFramework 但不想装插件 |

> **更简单的方法**：装了 REFramework 之后，皮肤 Mod 直接往 `natives/` 解压 + FirstNatives 插件搞定，**连 Fluffy 都不需要**。流程如下：
>
> ```
> ① 装 REFramework（dinput8.dll + 启动一次游戏生成 reframework/）
>        ↓
> ② FirstNatives.dll 丢进 reframework/plugins/
>        ↓
> ③ 下载皮肤 Mod → 解压出 natives/ → 合并到游戏根目录
>        ↓
> ④ 启动游戏，皮肤生效
> ```
>
> 后续再装别的皮肤，也只需要重复第 ③ 步。

### 3. 不要删除整个 `Natives`

如果你手动安装过多个 Mod，不要为了卸载一个 Mod 直接删除整个：

```text
Natives
```

因为里面可能有其他 Mod 的资源。应使用 Fluffy 管理，或者只删除目标 Mod 对应的资源文件。

---

## 七、Mod 冲突与附加组件

### 1. 依赖关系

如果 `modinfo.ini` 中出现：

```ini
addonfor=基础Mod名称
```

说明它是附加组件，必须先安装基础 Mod。

### 2. 资源路径冲突

两个 Mod 如果修改同一个路径，通常只能有一个最终生效。例如：

```text
Natives/STM/_Chainsaw/Character/...
Natives/STM/_Toxic/12_texture/...
```

常见冲突组合：

- 两套角色服装
- 两个身体贴图 Mod
- 两个 Style 变体
- 两个武器模型 Mod
- 两个 UI 或 HUD Mod

不要同时启用相同资源路径的变体，除非作者明确说明可以叠加。

### 3. 推荐测试顺序

```text
先安装基础框架
        ↓
只启用一个基础 Mod
        ↓
确认游戏能启动
        ↓
再启用一个附加组件
        ↓
出现问题就关闭最后添加的 Mod
```

---

## 八、常见问题

### Mod 没有生效

1. 确认 Mod 针对当前游戏，而不是其他 RE Engine 游戏。
2. 确认 Mod 页面要求的 REFramework、Fluffy 或其他前置已经安装。
3. 检查是否把 `Natives` 放到了游戏根目录，而不是 `reframework` 目录中。
4. 手动安装资源 Mod 时，确认 `LooseFileLoader_Enabled=true` 是否为作者要求的前置。
5. 通过 Fluffy 检查 Mod 是否已勾选并安装。
6. 一次只保留一个同类型外观 Mod。

### 游戏闪退

1. 关闭游戏并移走最近安装的 Mod。
2. 保留 REFramework 基础文件，确认游戏能否正常启动。
3. 检查 Mod 是否与当前游戏补丁兼容。
4. 检查是否重复安装了多个冲突的 `dinput8.dll`、资源 Mod 或插件。
5. 使用 Steam/Epic/Rockstar 客户端验证游戏文件。

### 游戏更新后 Mod 失效

这是常见情况。游戏更新可能改变：

- RE Engine 类型数据库
- 资源路径
- 方法名和字段名
- 文件加载机制
- Mod 依赖的框架版本

等待 REFramework 和 Mod 作者发布适配版本，不要直接把旧文件强行覆盖到新版本上。

---

## 九、恢复原版

### Fluffy 安装

在 Fluffy 中取消勾选 Mod，然后执行卸载/重新安装操作。

### 手动安装

1. 关闭游戏。
2. 删除目标 Mod 自己添加的文件，不能直接删除整个 `Natives` 或 `reframework`。
3. 如果曾经覆盖原始资源，使用游戏平台的文件验证功能恢复原版。
4. 不再使用任何 `Natives` Mod 时，可以把：

```ini
LooseFileLoader_Enabled=true
```

改回：

```ini
LooseFileLoader_Enabled=false
```

这不会卸载 REFramework，只会关闭松散资源文件加载。

---

## 十、安全边界

- 只从可信来源下载 Mod，并查看作者许可和 Requirements。
- 不要在带反作弊、公共服务器、竞技或未明确允许的联机环境使用注入式 Mod。
- 不要寻找绕过封禁、绕过检测或修改 Online 的工具。
- 备份自己的配置、存档和 Mod 清单，不要传播或打包游戏本体。
- 每款游戏单独保留自己的 `dinput8.dll`、`reframework` 配置和 Mod 文件，不要跨游戏复制。

> **核心口诀：先确认游戏 → 再看 Mod 类型 → Fluffy 管资源包 → REFramework 管脚本 → Natives 放游戏根目录 → 一次测试一个 Mod。**

## 参考资料

- [REFramework 官方仓库](https://github.com/praydog/REFramework)
- [Fluffy Mod Manager](https://fluffyquack.com/tools/modmanager.zip)
- [RE Engine Mod 通用说明](https://reframework.praydog.com/)
