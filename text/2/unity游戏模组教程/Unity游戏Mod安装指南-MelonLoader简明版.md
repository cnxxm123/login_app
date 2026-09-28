# Unity 游戏 Mod 安装简明指南（MelonLoader 篇）

> 详细说明见同目录《MelonLoader.md》。
>
> **平台说明**：本文的 `version.dll`、`dobby.dll` 和目录示例针对 Windows。Linux/Proton 使用不同的发布包和启动文件，按当前 MelonLoader 包内说明操作，不要期待 Windows 文件一定存在。

---

## 一、先确认游戏和版本

在包含游戏 EXE 的根目录观察：

- `游戏名_Data/Managed/` 中有大量游戏程序集：通常是 Mono。
- 有 `GameAssembly.dll`：通常是 Windows Unity IL2CPP 的强线索。
- 使用特殊启动器、改版或判断不明确：以游戏社区和 Mod Requirements 为准。

不要因为是 Mono 或 IL2CPP 就自行猜 MelonLoader 版本。先看 Mod 页面要求的 0.5.x、0.6/0.7 或其他指定版本。

---

## 二、安装 MelonLoader

**原理速查（为什么文件必须放在游戏 EXE 同目录）**：MelonLoader 用「DLL 代理注入」进游戏——Windows 加载 EXE 时会先在 EXE 所在目录找依赖 DLL，Unity 游戏本来就会加载系统的 `version.dll`，MelonLoader 把自己伪装成 `version.dll` 放到 EXE 同级目录，就会被系统优先加载，加载后再把真的系统 DLL 拉进来转发调用。所以放到启动器目录、快捷方式目录都不生效；2.7 章让你改成 `winhttp.dll`、`winmm.dll` 等，本质是换一个游戏一定会加载的系统 DLL 当伪装身份。`dobby.dll`（仅新版）是底层 hook 库，负责运行时改写游戏函数入口。

1. 从 [MelonLoader 官方发布页](https://github.com/LavaGang/MelonLoader/releases)获取安装器或与游戏要求匹配的压缩包。
2. 关闭游戏，选择真正的游戏 EXE，不要选择快捷方式或启动器 EXE。
3. 按游戏社区和 Mod 页面要求选择版本与 x86/x64 架构。
4. 手动安装时，把当前发布包要求的 `MelonLoader/`、代理 DLL（常见为 `version.dll`）和其他依赖完整放到游戏根目录。
5. IL2CPP 游戏可能需要 .NET 6 Desktop Runtime；Windows 安装器可以自动处理，但失败时按官方要求手动安装。
6. 启动一次游戏，查看 `MelonLoader/Logs/` 是否生成日志。

典型目录示意：

```text
游戏根目录/
├── Game.exe
├── MelonLoader/
├── Mods/       ← 普通 Mod，平铺或子目录按作者说明
├── Plugins/    ← 明确标注 Plugin 的内容
└── UserData/   ← 配置和运行数据
```

> 不要只复制一个 DLL，也不要默认把所有内容平铺到 `Mods/` 根目录。保留 Mod 压缩包的运行时结构。

---

## 三、安装 Mod 和验证

1. 先阅读 README，确认游戏版本、MelonLoader 版本、前置依赖和安装目录。
2. 保留作者提供的 DLL、依赖、资源和配置文件；不要只抽取主 DLL。
3. 按作者说明放入 `Mods/`、`Plugins/`、`UserData/` 或其他指定目录。
4. 启动游戏后查看 `MelonLoader/Logs/`，搜索 Mod 名称、`Error` 和 `Exception`。
5. 需要热键、菜单或配置开关的 Mod，按作者说明验证功能。

### Mod 没生效

- 检查 MelonLoader 版本和 Mod Requirements 是否一致。
- 检查游戏版本、x86/x64 位数和前置依赖。
- 确认文件结构没有多套一层目录，也没有误删资源文件。
- 不要同时安装 BepInEx；两个框架可能争用注入入口。

### 游戏闪退

1. 移走所有 Mod，只保留原版，使用游戏平台验证文件。
2. 只保留 MelonLoader 基础安装并启动一次。
3. 再逐个恢复 Mod，定位冲突项。
4. 游戏更新后先使用 `--no-mods` 排查，等待作者适配。

---

## 四、安全边界

- Mod 是可执行代码，只从可信来源下载，并阅读作者许可。
- 不要在带反作弊、公共服务器、竞技或未明确允许的联机环境使用注入式 Mod。
- 不要寻找绕过封禁、绕过反作弊或修改 Online 的工具。
- 备份自己的配置、存档和 Mod 清单；不要传播或打包游戏本体。

> **核心口诀：Requirements 优先 → 版本和位数匹配 → 使用完整发布包 → 保留 Mod 结构 → 看日志验证。**

## 参考资料

- [MelonLoader 官方仓库](https://github.com/LavaGang/MelonLoader)
- [MelonLoader Releases](https://github.com/LavaGang/MelonLoader/releases)
