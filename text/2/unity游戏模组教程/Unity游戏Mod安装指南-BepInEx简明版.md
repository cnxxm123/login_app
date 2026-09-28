# Unity 游戏 Mod 安装简明指南（BepInEx 篇）

> 详细说明见同目录《BepInEx.md》。
>
> **总规则：游戏和插件 Requirements 优先。** BepInEx 5.4.x 是正式稳定/LTS 线；BepInEx 6 仍属于预发布 / Bleeding Edge 生态。Mono、IL2CPP、游戏版本和插件要求必须一起确认。

---

## 一、平台包先选对

| 包名/环境 | 适用场景 | 关键区别 |
|---|---|---|
| `BepInEx_win_x64_5.4.23.5.zip` | Windows 64 位游戏 | 通常包含 Windows 注入文件，例如 `winhttp.dll`、`doorstop_config.ini`。 |
| `BepInEx_win_x86_5.4.23.5.zip` | Windows 32 位游戏 | 使用 x86 对应文件。 |
| `BepInEx_linux_x64_5.4.23.5.zip` | 原生 Linux、部分 Steam Deck/Proton 方案 | 使用 Linux 的 Doorstop/启动文件，不包含 Windows 的 `winhttp.dll`；按 Linux/Proton 说明启动。 |

如果你在 Windows 上运行游戏，应下载 `BepInEx_win_x64_5.4.23.5.zip`，不要把 `linux_x64` 包的文件补进 Windows 包中。下面的 Windows 目录示意只适用于 Windows 包。

---

## 二、先判断游戏后端

在包含游戏 EXE 的根目录观察：

- `游戏名_Data/Managed/` 中有大量游戏程序集：通常是 Mono。
- 有 `GameAssembly.dll`：通常是 Windows Unity IL2CPP 的强线索。
- 使用特殊启动器、改版或判断不明确：以游戏社区和插件 Requirements 为准。

后端只是判断方向，不能脱离游戏和插件要求强行选择版本。

---

## 三、选择 BepInEx 版本

- **BepInEx 5.4.x**：正式稳定/LTS，许多 Unity Mono 游戏使用。
- **BepInEx 6**：预发布 / Bleeding Edge；IL2CPP 游戏常需要，但也可能存在 Mono 预发布构建。
- 需要 v6 时，使用游戏社区指定的官方 Bleeding Edge 构建，不要从普通 Releases 页面猜版本。
- BepInEx 5 插件不能默认认为可直接运行在 v6；必须看插件作者的 Requirements。

参考：[BepInEx 官方仓库](https://github.com/BepInEx/BepInEx)、[BepInEx 文档](https://docs.bepinex.dev/)。

---

## 四、安装 BepInEx

**原理速查（Doorstop 注入器）**：BepInEx 靠 **UnityDoorstop** 进游戏——Windows 加载 EXE 时先在 EXE 所在目录找依赖 DLL，Unity 游戏本来就会加载系统的 `winhttp.dll`，Doorstop 把自己伪装成 `winhttp.dll` 放到 EXE 同级目录被优先加载；然后它在 Unity 初始化 Mono/CoreCLR 之前就挂钩子，把控制权交给 `BepInEx/core/` 里的 Preloader。所以 `winhttp.dll` + `doorstop_config.ini` 必须和游戏 EXE 同级；`doorstop_config.ini` 里把 `enabled` 改成 `false` 就能整体禁用 BepInEx。IL2CPP 构建的 `dotnet/`（自带的 CoreCLR 运行时）和 `BepInEx/interop/`（Il2CppInterop 生成的 C# 桥接层）不能删。BepInEx 的两条加载路径中，`patchers/` 在游戏 IL 被 JIT 之前跑，用于改写字节码；`plugins/` 在 Unity 场景加载后跑，是绝大多数普通插件的目录——不能互换。

1. 从官方 Release 或社区明确指定的 Bleeding Edge 构建下载与游戏位数匹配的 x86/x64 完整包。
2. 关闭游戏，把压缩包内容解压到包含游戏 EXE 的根目录。
3. 不要多套一层目录；`BepInEx/` 和注入相关文件应与游戏 EXE 同级，具体文件名以当前官方包为准。
4. 启动一次游戏，生成 `BepInEx/config/` 和实际日志文件，常见为 `BepInEx/LogOutput.*`。
5. 6.x/IL2CPP 构建可能需要生成 `interop/` 或其他运行文件，首次启动可能较慢；不要强制中断，也不要手动删减完整包。

典型结构：

```text
游戏根目录/
├── Game.exe
├── BepInEx/
│   ├── core/
│   ├── plugins/       ← 插件 Mod
│   ├── patchers/      ← 作者明确要求时才使用
│   ├── config/        ← 框架和插件配置
│   └── LogOutput.*     ← 日志，扩展名以实际版本为准
├── winhttp.dll        ← 仅作示意，以官方包为准
└── doorstop_config.ini
```

---

## 五、安装插件和验证

1. 阅读插件 README，确认 BepInEx 5/6、游戏版本、前置插件和架构要求。
2. 压缩包有 `plugins/`、`patchers/` 等目录时，按原结构合并到 `BepInEx/`。
3. 散装 DLL 通常放入 `BepInEx/plugins/`，但如果作者提供子文件夹、资源或依赖，必须完整保留。
4. 启动游戏，查看 `BepInEx/LogOutput.*`，搜索插件名、`Error` 和 `Skipping`。
5. 配置通常在 `BepInEx/config/`，但以插件作者说明和实际生成文件为准。

### 插件没有效果

- 检查 BepInEx 版本线、游戏版本、架构和前置依赖。
- 确认插件不是为另一个加载器或另一代 BepInEx 编写的。
- 不要只复制主 DLL，保留插件资源和作者提供的目录结构。
- 检查配置开关、游戏内热键和日志。

### 游戏闪退或无法启动

1. 移走所有插件，只保留原版，使用游戏平台验证文件。
2. 只保留 BepInEx 基础安装，确认日志能生成。
3. 再逐个恢复插件，定位冲突项。
4. 不要随机重命名代理 DLL；只有游戏社区或插件作者明确验证时才按说明调整。
5. 跨大版本、文件异常或排错时，备份后优先做干净安装，而不是直接覆盖旧框架。

---

## 六、安全边界

- 插件是可执行代码，只从可信来源下载，并阅读作者许可。
- 不要在带反作弊、公共服务器、竞技或未明确允许的联机环境使用注入式插件。
- 不要寻找绕过封禁、绕过反作弊或修改 Online 的工具。
- 备份自己的配置、存档和插件清单；不要传播或打包游戏本体。

> **核心口诀：Requirements 优先 → 完整官方包 → 保留插件结构 → 看 LogOutput.* → 一次只排查一个插件。**

## 参考资料

- [BepInEx 官方仓库](https://github.com/BepInEx/BepInEx)
- [BepInEx 官方文档](https://docs.bepinex.dev/)
- [BepInEx Mono 安装指南](https://docs.bepinex.dev/master/articles/user_guide/installation/unity_mono.html)
- [BepInEx IL2CPP 安装指南](https://docs.bepinex.dev/master/articles/user_guide/installation/unity_il2cpp.html)
- [BepInEx 升级指南](https://docs.bepinex.dev/articles/user_guide/upgrading.html)
