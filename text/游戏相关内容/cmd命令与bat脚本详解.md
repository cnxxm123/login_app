# CMD 命令与 BAT 脚本详解（小白向）

> 本文讲清两件事：**cmd 命令行是什么**，以及**怎么把命令写成 .bat 脚本自动执行**。每个知识点都配了可直接复制运行的实战案例。
>
> 官方参考：[Windows 命令官方文档](https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/windows-commands)、[cmd 命令参考](https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/cmd)、[set 变量](https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/set)、[for 循环](https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/for)。

## 目录

- [1. 基础概念](#1-基础概念)
- [2. 打开 cmd 与创建第一个 bat](#2-打开-cmd-与创建第一个-bat)
- [3. 常用命令大全（附案例）](#3-常用命令大全附案例)
- [4. 批处理核心语法](#4-批处理核心语法)
- [5. 实战案例合集](#5-实战案例合集)
- [6. 常见问题与安全提醒](#6-常见问题与安全提醒)

---

## 1. 基础概念

**一句话总结：bat 脚本 = 把 cmd 命令行打包成文件自动执行。**

| 概念 | 说明 |
|:---|:---|
| **cmd（命令提示符）** | Windows 自带的命令行窗口，在里面手动敲命令执行 |
| **cmd 命令** | 在窗口里输入的每一条指令，如 `dir`、`cd`、`start` |
| **.bat 文件** | 纯文本文件，把一条条 cmd 命令按顺序写进去，改成 `.bat` 后缀，双击就自动逐条执行 |
| **.cmd 文件** | 和 .bat 基本一样，一般可混用 |
| **批处理（batch）** | 即"批量处理"——让计算机自动按顺序执行一组命令 |

> 注意：**bat 里能写的命令，就是在 cmd 里能敲的命令**，语法完全一样。区别只有"手动敲"和"自动执行"。

---

## 2. 打开 cmd 与创建第一个 bat

### 2.1 打开 cmd 的四种方法

| 方法 | 操作 |
|:---|:---|
| 方法一 | `Win + R` 输入 `cmd` 回车 |
| 方法二 | 开始菜单搜索 `cmd` 或 `命令提示符` |
| 方法三 | 在任意文件夹地址栏输入 `cmd` 回车（**直接打开当前目录的 cmd，最常用**） |
| 方法四 | 按住 `Shift` 右键文件夹空白处 → "在此处打开 PowerShell / 命令窗口" |

### 2.2 创建并运行第一个 bat 脚本

1. 新建一个文本文件，命名为 `test.txt`
2. 写入以下内容，保存后把文件名改成 `test.bat`
3. 双击运行，看效果

```bat
@echo off
rem ================ 第一个脚本 ================
echo 你好，世界！
echo 当前目录下的文件有：
dir
pause
```

逐行解释：

| 行 | 作用 |
|:---|:---|
| `@echo off` | 关闭命令回显，执行时只显示我们自己输出的内容，不显示每条命令本身（脚本第一行惯例） |
| `rem ...` | 注释，不执行，用来写说明 |
| `echo 文字` | 在窗口里打印一行文字 |
| `dir` | 列出当前目录的文件和文件夹 |
| `pause` | 暂停，按任意键继续（放在结尾可防止窗口一闪而过） |

> **编码提醒**：Windows 记事本保存 bat 文件时，如果脚本里有中文，建议编码选 **ANSI（GBK）**。用 UTF-8 保存的话中文在某些系统上会显示乱码。

---

## 3. 常用命令大全（附案例）

> 记不住没关系，命令后加 `/?` 可查看帮助，如 `copy /?`。

### 3.1 目录与文件操作

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `dir` | 列出目录内容 | `dir`、`dir /w`（宽列表）、`dir *.txt`（只显示 txt） |
| `cd 路径` | 切换目录 | `cd C:\Game`、`cd ..`（返回上一级） |
| `md / mkdir` | 新建文件夹 | `mkdir backup`、`mkdir a\b\c`（可一次建多层） |
| `rd / rmdir` | 删除文件夹 | `rmdir /s /q folder`（`/s` 连内容一起删，`/q` 不询问） |
| `del 文件` | 删除文件 | `del a.txt`、`del *.tmp`（删所有 tmp 文件） |
| `copy 源 目标` | 复制文件 | `copy a.txt b.txt`、`copy a.txt backup\` |
| `xcopy 源 目标` | 复制整个目录树 | `xcopy src backup /e /i`（`/e` 含空目录，`/i` 目标是目录） |
| `move 源 目标` | 移动/重命名 | `move a.txt b.txt` |
| `ren 旧 新` | 重命名 | `ren a.txt b.txt` |
| `type 文件` | 查看文本内容 | `type readme.txt` |
| `tree` | 显示目录树 | `tree /f`（含文件） |

**案例 3-1：批量重命名文件（加统一前缀）**

在目标文件夹打开 cmd，执行：

```
for %i in (*.png) do ren "%i" "screenshot_%i"
```

说明：把当前目录所有 `.png` 文件改成 `screenshot_xxx.png`。
（注意：**在 cmd 里敲用单个 `%i`，在 bat 脚本里要写成 `%%i`**，见 4.4 节。）

**案例 3-2：一键清空文件夹里的所有临时文件**

```bat
@echo off
echo 正在清理当前目录的 .tmp 和 .bak 文件...
del /q *.tmp *.bak
echo 清理完成！
pause
```

> `del` 是**不可恢复**删除，不经过回收站。运行前请确认目录内容，或用 `copy`/`move` 先做备份。

### 3.2 程序与进程操作

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `start "" "路径"` | 启动程序/文件 | `start "" "C:\Game\game.exe"` |
| `start 文件名` | 用默认程序打开 | `start readme.txt`、`start https://www.baidu.com`（开网页） |
| `tasklist` | 列出运行中的进程 | `tasklist`、`tasklist /fi "imagename eq game.exe"`（过滤） |
| `taskkill` | 结束进程 | `taskkill /im game.exe /f`（`/f` 强制结束） |

**案例 3-3：强制结束卡死的游戏进程**

```bat
@echo off
echo 正在结束 game.exe 进程...
taskkill /im game.exe /f
taskkill /im "game's launcher.exe" /f
pause
```

说明：游戏崩溃或卡死时，`/im` 按进程名结束，`/f` 强制。名字带空格要加双引号。

**案例 3-4：一键启动游戏（切目录 + 启动）**

```bat
@echo off
rem 切换到游戏目录再启动，避免因工作目录不对导致的加载失败
cd /d D:\SteamLibrary\steamapps\common\MyGame
start "" "MyGame.exe"
exit
```

> `cd /d` 可以跨盘符切换（普通 `cd` 切不到别的盘）。`exit` 运行完自动关掉窗口。

### 3.3 网络相关

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `ping 地址` | 测试网络连通与延迟 | `ping www.baidu.com`、`ping -n 4 8.8.8.8` |
| `ipconfig` | 查看本机 IP / 网卡 | `ipconfig`、`ipconfig /all`（详细信息） |
| `tracert 地址` | 跟踪路由（看走了哪些节点） | `tracert www.baidu.com` |
| `nslookup 域名` | 查域名对应 IP | `nslookup www.baidu.com` |

**案例 3-5：测速并输出结果到文件**

```
ping -n 20 www.baidu.com > ping_result.txt
```

说明：`> ` 把命令输出写进文件（而不是显示在屏幕上）。`-n 20` 连续 ping 20 次。

### 3.4 系统与信息

| 命令 | 作用 | 示例 |
|:---|:---|:---|
| `cls` | 清屏 | `cls` |
| `echo 文字` | 输出文字 | `echo hello` |
| `echo 文字 > 文件` | 把文字写入文件 | `echo done > log.txt` |
| `set 变量=值` | 设置环境变量 | `set MYVAR=abc` |
| `set 变量=` | 清空变量 | `set MYVAR=` |
| `ver` | 查看系统版本 | `ver` |
| `systeminfo` | 查看系统详细信息 | `systeminfo` |
| `whoami` | 查看当前用户 | `whoami` |
| `shutdown` | 关机/重启/注销 | `shutdown /s /t 0`（立即关机）、`shutdown /r /t 60`（60秒后重启）、`shutdown /a`（取消） |

**案例 3-6：3 分钟倒计时自动关机（加班/睡觉好帮手）**

```bat
@echo off
echo 将在 180 秒后关机，要取消请马上运行 shutdown /a
shutdown /s /t 180
pause
```

### 3.5 组合符号与重定向

| 符号 | 作用 | 示例 |
|:---|:---|:---|
| `&&` | 前一条**成功**才执行后一条 | `cd /d D:\Game && start game.exe` |
| `\|\|` | 前一条**失败**才执行后一条 | `dir backup \|\| mkdir backup` |
| `>` | 输出**覆盖**写入文件 | `dir > list.txt` |
| `>>` | 输出**追加**到文件末尾 | `echo x >> log.txt` |
| `\|` | 管道，前一条的输出传给后一条 | `tasklist \| find "game"` |
| `%变量%` | 读取变量值 | `echo %PATH%` |

**案例 3-7：文件存在才启动，不存在就提示**

```bat
@echo off
if exist game.exe (start "" "game.exe") else (
    echo 找不到 game.exe，请检查游戏是否完整安装
    pause
    exit
)
```

> 小括号把多行包成一整块，`if ... else` 里用逗号/括号分组时要注意格式，这是 bat 新手最容易踩的坑之一。

---

## 4. 批处理核心语法

### 4.1 变量：`set` 与 `%变量%`

```bat
@echo off
rem 定义变量
set game_name=MyGame
set game_path=D:\Games\MyGame

rem 使用变量（读取时要包 %）
echo 游戏名是 %game_name%
echo 游戏路径是 %game_path%

pause
```

### 4.2 用户输入：`set /p`

```bat
@echo off
set /p name=请输入你的名字：
echo 你好，%name%！
pause
```

`set /p 变量=提示语` 会显示提示并等待用户输入，回车后把输入内容存入变量。

### 4.3 条件判断：`if`

常用形式：

| 写法 | 含义 |
|:---|:---|
| `if exist 路径 (命令)` | 文件/文件夹存在 |
| `if not exist 路径 (命令)` | 文件/文件夹不存在 |
| `if "%a%"=="值" (命令)` | 字符串相等（变量要加引号防止空格问题） |
| `if %n% EQU 5 (命令)` | 数字比较（EQU/NEQ/LSS/LEQ/GTR/GEQ） |

**案例 4-1：判断存档是否存在，存在就备份**

```bat
@echo off
set save_path=D:\MyGame\saves\save01.dat
if exist "%save_path%" (
    echo 找到存档，开始备份...
    copy "%save_path%" backup\
) else (
    echo 没找到存档
)
pause
```

### 4.4 循环：`for`

**遍历当前目录所有某类文件：**

```bat
@echo off
echo 当前目录下的所有 .txt 文件：
for %%f in (*.txt) do echo %%f
pause
```

> 重要：**cmd 里手敲用 `%f`，写进 bat 脚本必须用 `%%f`**（双百分号）。

**案例 4-2：批量给一组文件改名（bat 版）**

```bat
@echo off
rem 把当前目录所有 .log 文件改成 备份_xxx.log
for %%f in (*.log) do ren "%%f" "备份_%%f"
echo 改名完成
pause
```

### 4.5 跳转：`goto` 与标签

```bat
@echo off
echo 按 1 玩游戏，按 2 打开官网
set /p choice=你的选择：
if "%choice%"=="1" goto play
if "%choice%"=="2" goto web
goto end

:play
start "" "D:\Game\game.exe"
goto end

:web
start https://www.example.com
goto end

:end
echo 完成！
pause
```

### 4.6 调用其他脚本：`call`

```bat
@echo off
echo 先执行第一个脚本...
call setup.bat
echo setup.bat 执行完了，继续...
start "" "game.exe"
pause
```

> 直接写 `setup.bat` 也能调用，但执行完**不会回到当前脚本**；用 `call` 会执行完再回来继续。涉及多脚本协作时用 `call` 更安全。

### 4.7 错误码：`%errorlevel%`

```bat
@echo off
ping -n 1 8.8.8.8
if %errorlevel% EQU 0 (
    echo 网络通畅
) else (
    echo 网络不通
)
pause
```

每条命令执行完后会留下一个"错误码"，`0` 通常表示成功。上面用它判断 ping 是否成功。

---

## 5. 实战案例合集

> 以下案例都是完整可运行的脚本，按你自己的路径改一改就能用。

### 案例 A：游戏一键启动器（切目录 + 校验文件 + 启动）

```bat
@echo off
title MyGame 启动器
chcp 65001 >nul
rem chcp 65001 切到 UTF-8 代码页，解决中文乱码（配合 UTF-8 编码保存时使用）

set game_path=D:\SteamLibrary\steamapps\common\MyGame

rem 检查目录存在
if not exist "%game_path%" (
    echo 找不到游戏目录：%game_path%
    echo 请检查游戏是否安装或路径是否正确
    pause
    exit /b
)

rem 切到游戏目录再启动
cd /d "%game_path%"
start "" "MyGame.exe"
exit
```

### 案例 B：自动备份存档（带日期，保留最近 7 份）

```bat
@echo off
rem 目标：把游戏存档复制到备份目录，备份文件夹带日期，并只保留最近 7 份

set save_source=D:\MyGame\saves
set backup_root=D:\MyGame\backup

rem 生成日期字符串，例如 20261002
set today=%date:~0,4%%date:~5,2%%date:~8,2%
rem 解释：%date% 形如 2026/10/02，:0,4 取前4位年份，:5,2 取月，:8,2 取日

set backup_dir=%backup_root%\%today%
mkdir "%backup_dir%"
xcopy "%save_source%" "%backup_dir%" /e /i /y
echo 已备份到 %backup_dir%

rem 只保留最近 7 个备份文件夹：按日期排序，删除第 8 个及以后
set /a count=0
for /d %%d in ("%backup_root%\*") do (
    set /a count+=1
)
if %count% GTR 7 (
    echo 备份超过 7 份，开始清理最旧的...
)

rem 简单方案：直接用 forfiles 删除 7 天前的备份
forfiles /p "%backup_root%" /d -7 /c "cmd /c if @isdir==TRUE rd /s /q @path" 2>nul
echo 备份完成！
pause
```

> 说明：`%date%` 的格式跟系统区域设置有关，可能不是 `年/月/日`，自己先 `echo %date%` 看一眼再套用。
> `forfiles /d -7` 表示修改时间超过 7 天的项，这句会删掉 7 天前的备份文件夹。

### 案例 C：游戏缓存/垃圾文件一键清理

```bat
@echo off
set cache_dir=C:\Users\%USERNAME%\AppData\Local\MyGame\Cache

echo 正在清理游戏缓存：%cache_dir%
if exist "%cache_dir%" (
    rd /s /q "%cache_dir%"
    echo 缓存已清空，游戏下次启动会自动重建
) else (
    echo 没有找到缓存目录，无需清理
)
pause
```

> `%USERNAME%` 是系统内置变量，自动取当前用户名。`rd /s /q` 删除整个目录树且不询问。

### 案例 D：文件分类整理器（把同类型文件移到对应文件夹）

```bat
@echo off
rem 把"下载文件夹"里的图片/文档/压缩包自动归类

set src=C:\Users\%USERNAME%\Downloads

cd /d "%src%"
mkdir 图片 文档 压缩包 其他 2>nul

for %%f in (*.jpg *.png *.gif *.bmp) do move "%%f" 图片\ >nul 2>nul
for %%f in (*.doc *.docx *.pdf *.txt) do move "%%f" 文档\ >nul 2>nul
for %%f in (*.zip *.rar *.7z) do move "%%f" 压缩包\ >nul 2>nul

echo 整理完成！
pause
```

> `2>nul` 把错误提示丢弃（比如"没有匹配文件"），`>nul` 丢弃正常输出，让脚本安静执行。

### 案例 E：带菜单的多功能脚本（组合运用 if / goto）

```bat
@echo off
:menu
cls
echo ==============================
echo        MyGame 工具菜单
echo ==============================
echo 1. 启动游戏
echo 2. 备份存档
echo 3. 清理缓存
echo 4. 退出
echo ==============================
set /p choice=请选择（1-4）：

if "%choice%"=="1" goto play
if "%choice%"=="2" goto backup
if "%choice%"=="3" goto clean
if "%choice%"=="4" exit
echo 输入无效，请重新选择
pause
goto menu

:play
cd /d D:\Games\MyGame
start "" "MyGame.exe"
goto menu

:backup
set today=%date:~0,4%%date:~5,2%%date:~8,2%
mkdir "D:\MyGameBackup\%today%" 2>nul
xcopy "D:\Games\MyGame\saves" "D:\MyGameBackup\%today%" /e /i /y
echo 备份完成
pause
goto menu

:clean
rd /s /q "C:\Users\%USERNAME%\AppData\Local\MyGame\Cache" 2>nul
echo 缓存已清理
pause
goto menu
```

> `:menu` 是标签，`goto menu` 跳回去，配合 `cls` 清屏形成循环菜单。`2>nul` 忽略"目录已存在"之类的提示。

### 案例 F：定时提醒脚本

```bat
@echo off
set /p minutes=多少分钟后提醒（填数字）：
set /a seconds=minutes*60
echo %minutes% 分钟后会弹出提示...
timeout /t %seconds%
echo 时间到！该休息/去收菜啦！
pause
```

> `timeout /t 秒` 等待指定秒数；`set /a` 是做数学运算（`set /a` 不需要 `%` 包裹变量）。

---

## 6. 常见问题与安全提醒

### 6.1 常见问题

| 问题 | 原因与解决 |
|:---|:---|
| 双击 bat 一闪而过 | 结尾没有 `pause`，执行完窗口自动关了。加上 `pause` 即可 |
| 中文乱码 | 文件编码问题。记事本保存选 ANSI；或在脚本开头加 `chcp 65001 >nul` 并保存为 UTF-8 |
| `%%f` 报错 | 把脚本里的 `%%f` 写成 `%f` 了。cmd 手敲用 `%f`，bat 文件里必须 `%%f` |
| 提示"不是内部或外部命令" | 命令拼错，或该命令不在 PATH 里。检查拼写，`/?` 看帮助 |
| `cd` 切盘符没反应 | 跨盘要用 `cd /d 路径`，或先输入 `D:` 回车再 cd |
| 杀毒软件报警 | bat 里的行为（如删除文件、改注册表）可能触发误报。确认内容是自己写的再放行 |
| 管理员权限不足 | 脚本需要管理员权限时，右键 bat →"以管理员身份运行" |

### 6.2 安全提醒（重点）

1. **从网上下载的 .bat 先编辑再看内容再运行**，别直接双击。bat 能执行任意命令。
2. **警惕这些危险命令**，一旦出现在脚本里要格外小心：
   - `del /s /q`、`rd /s /q` —— 静默删文件/目录，不可恢复
   - `format` —— 格式化磁盘，数据全没
   - `shutdown` —— 关机/重启
   - `powershell -c ...` / `curl ... | 运行` —— 下载并执行远程内容，可能中招
3. **`del` 不走回收站**，删了就是真的没了，操作前先备份。
4. **路径建议加双引号**，尤其是带空格或中文的路径。

### 6.3 查看命令帮助

任何命令后加 `/?` 查看完整参数说明：

```
copy /?
xcopy /?
for /?
set /?
```

---

## 附：参考链接

- Windows 命令官方文档：<https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/windows-commands>
- cmd 命令参考：<https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/cmd>
- set 变量详解：<https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/set>
- for 循环详解：<https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/for>
- if 条件详解：<https://learn.microsoft.com/zh-cn/windows-server/administration/windows-commands/if>
