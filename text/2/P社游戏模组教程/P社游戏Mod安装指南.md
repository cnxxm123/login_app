# P 社游戏 Mod 安装指南（Clausewitz / Jomini 引擎篇）

> 本指南面向 **Paradox Interactive** 用 **Clausewitz** 与 **Jomini** 引擎开发的大型策略游戏（Grand Strategy Game，GSG）。这些游戏 Mod 生态的最大特点是**数据驱动**——绝大多数 Mod 不需要注入 DLL、不需要加载器，改的都是**纯文本数据**。
>
> **主要覆盖**：
>
> - **《欧陆风云 4》**（Europa Universalis IV，EU4）
> - **《十字军之王 3》**（Crusader Kings III，CK3）
> - **《钢铁雄心 4》**（Hearts of Iron IV，HoI4）
> - **《群星》**（Stellaris）
> - **《维多利亚 3》**（Victoria 3，V3）
> - **《大将军：罗马》**（Imperator: Rome）
>
> **总规则**：**Mod 是给哪个游戏、哪个游戏版本写的，只能装到那个组合上**。P 社游戏几乎每个大补丁（1.34 → 1.35、1.11 → 1.12 之类）都会引入 script/数据格式变化，让老 Mod 部分或完全失效。

---

## 一、Clausewitz 与 Jomini 简介

Clausewitz 是 P 社从 2007 年《欧陆风云 3》起使用的自研引擎，历代迭代到现在覆盖了 GSG 的整条产品线。**Jomini** 是 2019 年（CK3 前后）在 Clausewitz 之上抽出来的**上层游戏框架**——处理 UI、事件、模组接口，让不同游戏的通用系统更好复用。

| 游戏 | 引擎 | 备注 |
|---|---|---|
| EU4 | Clausewitz | 生态最庞大，Mod 数量以万计 |
| Stellaris | Clausewitz | 与 EU4 底层相似，Mod 系统类似 |
| HoI4 | Clausewitz | 剧本 Mod（AAR）与总替换（Total Conversion）繁多 |
| CK3 | Clausewitz + Jomini | Mod 接口现代化，脚本更强 |
| V3 | Clausewitz + Jomini | 最新一代 GSG 架构 |
| Imperator: Rome | Clausewitz + Jomini | 官方停更但 Mod 生态仍活跃 |

**从玩家安装 Mod 的角度看，这几个游戏的 Mod 目录结构、descriptor 文件写法几乎一样**——学会一个就能推到其他游戏。

---

## 二、原理：P 社 Mod 是怎么加载的

理解下面几点，就能明白为什么 P 社 Mod 装起来简单、冲突起来又极其复杂：

### 2.1 游戏 = 引擎 + 一堆数据文件

- 游戏本体安装目录下的 `common/`、`events/`、`history/`、`localisation/`、`gfx/`、`map/`、`music/` 等一系列文件夹，装的其实都是**明文文本**：`.txt`（脚本）、`.yml`（本地化）、`.dds`（贴图）、`.ogg`（音频）等。
- 引擎在启动时把这些数据全部读进内存，构建整个模拟世界。
- Mod 的本质：**用同名/同路径的文件覆盖或追加游戏本体的数据**。

### 2.2 Mod 目录 vs Documents/Paradox Interactive/

- **游戏本体安装目录**（Steam 库）里的是原版数据，Mod 不要往这里塞。
- 用户 Mod 都放到 `<Documents>/Paradox Interactive/<游戏名>/mod/`。
- 启动时游戏的 launcher 会扫描这个目录里所有 `.mod` 描述文件，把找到的 Mod 显示在启动器的 Mod 列表里。

### 2.3 `.mod` 描述文件与 `descriptor.mod`

一个 Mod 由两部分组成：

1. **Mod 目录本身**（存放实际内容），里面必须有一个 `descriptor.mod`。
2. **`.mod` 描述文件**（同名，放在 `mod/` 目录根部），告诉 launcher「这里有个 Mod，路径在哪」。

```text
Documents/Paradox Interactive/Crusader Kings III/mod/
├── my_awesome_mod.mod                ← 描述文件（launcher 靠它找到 Mod）
└── my_awesome_mod/                   ← Mod 实际内容
    ├── descriptor.mod                ← Mod 自身描述（版本、依赖、tags）
    ├── common/
    ├── events/
    ├── localization/
    └── ...其他覆盖/新增的数据文件
```

**`.mod` 和 `descriptor.mod` 的内容几乎一样**，Steam Workshop 下载的 Mod 只有 `descriptor.mod`（launcher 会自动为它生成 `.mod`）；手动装的 Mod 两者都要有。

### 2.4 覆盖规则

- 加载顺序：**先加载游戏本体 → 再按 Mod 列表顺序加载启用的 Mod**。
- 后加载覆盖先加载：Mod B 在列表里排在 Mod A 后面时，若它们都改了 `common/religions/00_religions.txt`，B 的整份文件会替换 A 的（**是文件级覆盖，不是记录级合并**）。
- 这就是为什么 P 社 Mod 冲突特别难处理——两个 Mod 都改了同一份宗教定义文件，先加载的直接被丢弃。
- **加载顺序 = Playset 里的排序**，不是 Mod 列表勾选顺序。

### 2.5 依赖（Dependencies）

`descriptor.mod` 里可以声明 `dependencies={ "Mod A" "Mod B" }`，让启动器提示玩家先装前置。**这只是提示**，并不强制加载顺序；实际顺序仍然靠 Playset 手动调整。

### 2.6 版本 tag 与失效警告

`descriptor.mod` 有 `supported_version="1.12.*"` 字段。游戏启动器把它和当前游戏版本比对，不匹配时会在 Mod 列表里显示黄色/红色警告。

但 P 社的策略是：**警告归警告，游戏仍然会加载**。所以看到「For 1.11」但你在 1.12：**可能能玩，可能崩，可能异常，凭运气**。

---

## 三、Steam Workshop：最简单的路子

绝大多数 P 社玩家的 Mod 通过 Steam Workshop 获取：

1. 打开游戏的 Workshop 页面（Steam → 游戏 → 创意工坊）。
2. 找到想要的 Mod 点「订阅」。
3. Steam 会自动下载到 `Steam/steamapps/workshop/content/<game_id>/<mod_id>/`。
4. 启动游戏，在启动器的「Mod」标签页里把订阅的 Mod 添加到 Playset，勾选启用。
5. 「Playsets」页里调整 Mod 的加载顺序（拖动排序）。
6. 点「Play」启动游戏。

**Workshop 优势**：

- 自动更新——Mod 作者更新时 Steam 会自动拉新版。
- 自动跟游戏版本关联——`descriptor.mod` 的 `supported_version` 让 launcher 判断兼容性。
- 一键取消订阅 = 卸载。

**Workshop 局限**：

- Mod 作者停更之后老版本没法回退（除非用 SteamCMD 或第三方工具）。
- 中国大陆访问 Steam Workshop 有时不稳定。
- 一些成人向、NSFW、大型 TC（Total Conversion）Mod 只在 Paradox Plaza、Nexus、GitHub、ModDB 分发。

---

## 四、手动安装

从 Nexus / ModDB / 作者的 GitHub 或 Discord 下载 Mod 压缩包时用手动安装。

### 4.1 步骤

1. 关闭游戏和 launcher。
2. 下载 Mod 压缩包（`.zip` 或 `.rar`）。
3. 打开 Mod 用户目录：

   | 游戏 | 路径 |
   |---|---|
   | EU4 | `<Documents>\Paradox Interactive\Europa Universalis IV\mod\` |
   | CK3 | `<Documents>\Paradox Interactive\Crusader Kings III\mod\` |
   | HoI4 | `<Documents>\Paradox Interactive\Hearts of Iron IV\mod\` |
   | Stellaris | `<Documents>\Paradox Interactive\Stellaris\mod\` |
   | V3 | `<Documents>\Paradox Interactive\Victoria 3\mod\` |
   | Imperator | `<Documents>\Paradox Interactive\Imperator\mod\` |

4. 把压缩包**内容**解压到 `mod/` 目录。理想结果：`mod/mymod/` 和 `mod/mymod.mod` 同级存在。
5. 如果压缩包**只包含** `mymod/` 一个文件夹而没有 `mymod.mod` 描述文件：
   - 打开 `mod/mymod/descriptor.mod`，复制里面所有内容。
   - 在 `mod/` 根部新建 `mymod.mod`，粘贴内容进去。
   - 在文件末尾加一行：`path="mod/mymod"`（**这是关键的一行**，告诉 launcher 去哪找）。

**完整 `.mod` 示例**：

```text
version="1.0.0"
tags={
    "Historical"
    "Overhaul"
}
name="My Awesome Mod"
supported_version="1.12.*"
path="mod/mymod"
```

### 4.2 校对：能不能在启动器看到

启动游戏 launcher → 「Mods」标签页，如果 Mod 出现在列表里就装成功了。找不到：

- 检查 `.mod` 文件在 `mod/` 目录里，不是嵌套一层。
- 检查 `path` 是否正确（相对 `Documents\Paradox Interactive\<游戏>\`，不是绝对路径）。
- `.mod` 编码问题：用记事本另存为 UTF-8 without BOM。
- 中文路径：`Documents\Paradox Interactive` 是英文的，Mod 目录名尽量也用英文/数字。

### 4.3 加入 Playset

「Playsets」是启动器的 Mod 组合功能：

- 一个 Playset 是一组勾选启用的 Mod + 一个加载顺序。
- 可以创建多个 Playset 应对不同玩法（历史流、TC 流、快速游戏流）。
- 想改加载顺序：进 Playset 编辑，拖动 Mod 位置——**上面的先加载，下面的后加载，冲突时下面的覆盖上面的**。

---

## 五、常见 Mod 类型

### 5.1 数据 Mod（Data / Small Overhaul）

改数值、加剧本、加事件、加历史人物；本质上是往 `common/`、`events/`、`history/` 里添加或覆盖 `.txt`。

- **示例**：CK3 的「More Bookmarks+」（增加历史书签起点）、HoI4 的「Historical Focus Only」（去掉替代历史选项）。
- **冲突风险**：低到中。

### 5.2 图像 / UI Mod（Cosmetic）

改 `.dds` 贴图、`gui/`（UI 布局）、`gfx/`（美术资源）。

- **示例**：CK3 的「Ethnicities & Portraits Expanded」（更多人物肖像）、EU4 的「Better UI」类。
- **冲突风险**：视覆盖的资源决定。同时装两个「大字体」类 UI Mod 大概率冲突。

### 5.3 本地化 Mod（Localisation）

只改 `localization/` 里的 `.yml` 语言文件——最常见的是**汉化 Mod**、**英文润色 Mod**。

- **示例**：3DM/贴吧、Steam Workshop 的各种 EU4/CK3 汉化包。
- **冲突风险**：多个汉化 Mod 只能选一个；和内容 Mod 冲突时可能出现文本键找不到（游戏内显示英文 key 或 `???`）。

### 5.4 总替换（Total Conversion，TC）

从头替换游戏世界——不同时代、不同宇宙、不同规则。

- **知名 TC**：
  - **CK3 冰与火之歌 AGOT**（A Game of Thrones，权游背景）
  - **EU4 MEIOU and Taxes**、**Anbennar**（架空奇幻）
  - **HoI4 Kaiserreich**（一战德国胜利架空）、**Old World Blues**（辐射背景）
  - **Stellaris Star Trek: New Horizons**、**Star Wars: New Republic**
  - **Imperator Invictus**（社区大型内容扩展，弥补官方停更）

- **冲突风险**：极高，TC 通常**独占启用**——除了作者提交的兼容子 Mod，不要和其他大型 Mod 混。
- **通常需要开新档**，老档不兼容。

### 5.5 平衡 / MP 用小 Mod

- **示例**：AI 增强、经济平衡、Balanced Trade、Multiplayer Fixes。
- 多人游戏中所有人必须启用**完全一致的 Mod 列表** + **相同顺序**（不然会 desync）。

---

## 六、目录结构（Mod 内部）

一个典型 Mod 内部结构（以 CK3 为例）：

```text
my_awesome_mod/
├── descriptor.mod              ← Mod 自身信息，必需
├── thumbnail.png               ← Steam Workshop 缩略图（可选）
├── common/                     ← 数据脚本
│   ├── religion/               ← 宗教定义
│   ├── traits/                 ← 特质定义
│   ├── cultures/               ← 文化定义
│   ├── decisions/              ← 决议
│   └── ...大量子目录，每个对应游戏一个系统
├── events/                     ← 事件脚本
│   └── my_events.txt
├── history/                    ← 起始历史数据
│   ├── characters/
│   ├── titles/
│   └── provinces/
├── localization/               ← 本地化文本（CK3 用 localization，EU4 用 localisation）
│   ├── english/
│   │   └── my_mod_l_english.yml
│   ├── simp_chinese/
│   └── ...
├── gfx/                        ← 美术资源
│   ├── portraits/
│   ├── interface/
│   └── flags/
├── gui/                        ← UI 布局
├── map_data/                   ← 地图数据（CK3/V3）
├── music/                      ← 自定义音乐
└── sound/                      ← 音效
```

**关键约定**：

- 文件夹和文件命名**必须和游戏本体的路径一致**才能实现覆盖。例如 CK3 的宗教在 `common/religion/religions/00_religions.txt`，Mod 想覆盖它就必须放同样的相对路径。
- 覆盖是**整份文件替换**，不是记录级合并。如果只想改一条记录，最好：**只保留改动，其他记录一并抄过来**——否则会丢失游戏本体的其他条目。
- 更优雅的做法：**把要覆盖的文件重命名并做成新文件**。P 社的加载会把同一目录下所有 `.txt` 都读进内存并合并，`ZZZ_MyMod_00_religions.txt` 会比原版 `00_religions.txt` 后加载（字母序靠后）——但这条不适用于「按文件名覆盖」的目录（如 `history/provinces/`），需要具体研究游戏文档。

---

## 七、进阶：Mod 冲突处理

### 7.1 使用 Compatibility Patch

多个大型 Mod 之间通常有**社区维护的兼容 patch**——一个小 Mod，专门把 A Mod 和 B Mod 的改动合并起来。

在 Playset 里加载顺序：`A → B → A+B Compat Patch`（Patch 放最后覆盖）。

### 7.2 手动合并

如果找不到现成 Patch：

1. 用 [Winmerge](https://winmerge.org/) 或 VS Code + Compare 扩展比较两个 Mod 的同名文件。
2. 手动合并成一份新文件。
3. 建一个小型「私人 Patch Mod」，只放这些合并结果，加载顺序放最后。

### 7.3 冲突检查工具：Irony Mod Manager

[Irony Mod Manager](https://github.com/bcssov/IronyModManager) 是一款开源的 Mod 冲突分析器：

- 支持 EU4、CK3、HoI4、Stellaris、V3、Imperator。
- 可视化冲突：直接指出哪个 Mod 覆盖了哪个 Mod 的哪个文件。
- 自动合并、手动合并、生成 patch。
- 装大型 Mod 组合时极大提高排错效率。

### 7.4 版本降级

想玩老 Mod 时游戏版本已经升级：

- Steam 有 Beta 分支（游戏属性 → Betas），P 社通常保留几个大版本的 rollback。
- 用 SteamCMD 拉指定 depot manifest ID 也可以。
- **单机可行，MP 需要所有人版本一致**。

---

## 八、多人游戏（MP）

P 社 GSG 多人游戏是 lockstep 模拟，所有玩家的模拟必须完全同步。因此：

- **所有玩家的 Mod 列表必须完全一致**（名称、版本、顺序）。
- **DLC 同样必须一致**（否则加入房间时直接被踢或 desync）。
- 使用 Playset 的「Export」功能把配置导出为 `.pdsmod` 或 `.zip`，发给队友导入，能避免手工对齐失误。
- 任何 Mod 的随机数生成、AI 决策差异都会 desync；MP 前先在 hotjoin 测试几个游戏日看有没有 out of sync。

---

## 九、常见问题排查

### Q1：启动器看不到 Mod

- `.mod` 描述文件在 `mod/` 根部；不能嵌套在 `mod/subdir/mymod.mod`。
- `path=` 路径正确，指向实际 Mod 内容目录（相对 `Documents/Paradox Interactive/<游戏>/`）。
- 编码是 UTF-8 no BOM。
- Windows「显示扩展名」打开，确认不是 `mymod.mod.txt`。

### Q2：游戏启动崩溃

- 大概率是 Mod 与当前游戏版本不兼容。看看 Playset 里 Mod 的黄/红警告。
- 一个个禁用 Mod 找出罪魁：先只启用一个，能进就加下一个。
- 用 Irony 检查冲突文件，某个关键系统被两个 Mod 争夺时会崩。
- 打开 `Documents\Paradox Interactive\<游戏>\logs\error.log`，最后几行常有报错。

### Q3：游戏能启动但玩到某个时间点崩

- 事件脚本错误：某个事件在特定条件下触发时崩溃。查 `error.log` 找相关事件 ID。
- Mod 的 `history/` 数据与当前世界状态不匹配（例如指向了不存在的省份/角色）。

### Q4：Localisation 显示的是英文 key 或 `???`

- 汉化 Mod 与内容 Mod 冲突——内容 Mod 加了新 key，汉化 Mod 没覆盖到。
- 检查汉化 Mod 是否是为当前内容 Mod 版本做的。
- 加载顺序：汉化 Mod 排在内容 Mod **之后**。

### Q5：MP 玩着玩着 desync

- 检查所有玩家 Mod 列表和 DLC 是否完全一致，包括加载顺序。
- 移除有随机因素的 Mod。
- Paradox 的 pdxlan 桌面工具或 Playset 导出功能对齐配置。

### Q6：Steam Workshop 下载不下来 / 更新不了

- Steam Workshop 有时对个别地区不稳定。
- 用 [Steam Workshop Downloader](https://steamworkshopdownloader.io/) 之类第三方工具下载 Mod ZIP，再手动放到 `mod/` 目录。
- 服务端下载工具 SteamCMD 也能拉 Workshop 内容。

---

## 十、卸载

- **单个 Workshop Mod**：Steam 页面「取消订阅」。
- **单个手动 Mod**：删掉 `Documents/Paradox Interactive/<游戏>/mod/` 下对应的 `.mod` 描述文件和 Mod 目录。
- **完全清空**：删掉整个 `mod/` 目录；但 Steam 订阅的 Mod 下次启动会重新出现（先取消订阅）。
- 存档：装了 Mod 打的存档**一般无法在原版打开**，游戏会因为找不到 Mod 特有的 flag/事件/记录而拒绝加载。想回原版建议开新档。

---

## 十一、安全边界

- Mod 是纯数据文件时**理论上无安全风险**——不会跑 native code。但要小心：
  - Mod 包里附带的 `.exe`、`.dll`、`.bat`——P 社 Mod 正常不需要这些，出现了要警惕。
  - 极少数 Mod 在 `.mod` 或 `descriptor.mod` 里嵌入路径注入（利用 launcher 漏洞），从可信来源下载即可规避。
- **多人游戏**只装大家商量好的 Mod，Ranked / Achievement 游戏往往关闭 Mod（P 社在启用 Mod 后自动关闭成就）。
- 备份 `Documents\Paradox Interactive\<游戏>\save games\` 存档目录。

---

## 十二、流程总结

```text
① 确认游戏和版本号（EU4 1.37、CK3 1.13、HoI4 1.14 之类）
       ↓
② Steam Workshop 订阅 或 手动放到 Documents/Paradox Interactive/<游戏>/mod/
       ↓
③ 启动 launcher 确认 Mod 出现在列表
       ↓
④ 新建 Playset，加入 Mod 并调整加载顺序（下面覆盖上面）
       ↓
⑤ 冲突检查用 Irony Mod Manager；找不到兼容 Patch 就自己合并
       ↓
⑥ 启动游戏；崩溃看 error.log
       ↓
⑦ MP 前所有玩家对齐 Mod 列表、DLC 和加载顺序
```

> 核心口诀：**看清游戏版本 → 用 Playset 管顺序 → 冲突靠 Irony → 覆盖是文件级而非记录级 → MP 全员一致。**

---

## 参考资料

- [Paradox Interactive 官网](https://www.paradoxinteractive.com/)
- [Paradox Plaza（官方 Mod 平台）](https://mods.paradoxplaza.com/)
- [Paradox Wiki（EU4/CK3/HoI4/Stellaris/V3 都有专门 wiki）](https://eu4.paradoxwikis.com/)
- [Irony Mod Manager](https://github.com/bcssov/IronyModManager)
- [Steam Workshop（各游戏）](https://steamcommunity.com/workshop/browse/)
- [CK3 Modding Wiki](https://ck3.paradoxwikis.com/Modding)
- [Stellaris Modding Wiki](https://stellaris.paradoxwikis.com/Modding)
- [Anbennar（EU4 奇幻 TC）](https://www.anbennar.com/)
- [Kaiserreich（HoI4 架空 TC）](https://kaiserreich.com/)
- [Winmerge 文件比较](https://winmerge.org/)
