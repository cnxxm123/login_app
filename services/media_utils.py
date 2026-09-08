"""media_utils 模块（services 包）
媒体处理（纯逻辑层，不依赖 Flask）。

职责：
- get_video_thumb()   为视频生成封面缩略图（ffmpeg 抽帧 + md5 缓存）
- get_image_thumb()   为图片生成压缩缩略图（Pillow 缩放 + md5 缓存）
- get_cover_thumb()   为文件夹封面生成高清缩略图（900px、质量 88，独立缓存）
- ensure_playable()   把手机浏览器无法播放的视频转成兼容格式（H.264 + faststart）
"""

import hashlib
import os
import re
import subprocess
import threading
from functools import lru_cache

from config import IMG_THUMB_DIR, THUMB_DIR, TRANSCODE_DIR

# 按路径加锁，防止并发请求同时用 ffmpeg 写同一个缓存文件（互相 -y 截断会把缓存写坏，
# 坏缓存被 isfile 命中后永久复用，表现为"视频有时候放不了/封面裂图"）。
#
# 【防内存泄漏】用 lru_cache 做成"固定容量 LRU 锁池"：
# - maxsize=512：最多同时持有 512 把路径锁，超出的"最久未使用"锁自动淘汰，
#   避免原实现里 dict 只增不减——服务跑得越久、浏览过的文件越多字典越大（内存泄漏）。
# - 锁在 with 块里是秒级持有，即使某把锁被淘汰后同路径再次出现，也只是新建一把锁，
#   最坏结果是同一缓存文件被并发写两次（有 .part + os.replace 原子替换兜底），
#   不影响正确性，代价可忽略。
@lru_cache(maxsize=512)
def _path_lock(key: str) -> threading.Lock:
    """取某个路径对应的互斥锁（LRU 缓存：最多 512 把，久未使用自动淘汰）。"""
    return threading.Lock()


def get_video_thumb(video_path: str) -> bytes | None:
    """为视频生成封面缩略图（JPG 字节流）；抽帧失败返回 None。

    实现：用 imageio_ffmpeg 自带的 ffmpeg 抽第 1 秒的一帧，
    缩放到宽 ~480px（保持宽高比），并按"视频绝对路径的 md5"命名缓存，
    之后直接读缓存，避免每次都启动 ffmpeg 重复抽帧。
    """
    if not os.path.isfile(video_path):
        return None
    # m3u8 是分片流播放列表，无法直接定位单帧，跳过
    if video_path.lower().endswith(".m3u8"):
        return None

    # 保证目录存在（若已存在会抛 FileExistsError，忽略即可）
    os.makedirs(THUMB_DIR, exist_ok=True)
    thumb_path = os.path.join(
        THUMB_DIR,
        hashlib.md5(os.path.abspath(video_path).encode("utf-8")).hexdigest() + ".jpg",
    )
    if os.path.isfile(thumb_path):  # 命中缓存
        with open(thumb_path, "rb") as f:
            return f.read()

    try:
        from imageio_ffmpeg import get_ffmpeg_exe  # 自带 ffmpeg 二进制，无需系统安装
    except Exception:
        return None

    # 并发保护：同一个视频同时被多个请求抽帧时，串行执行 + 原子写入，
    # 避免 ffmpeg 互相截断缓存导致封面损坏（broken image）。
    lock = _path_lock("thumb:" + os.path.abspath(video_path))
    with lock:
        if os.path.isfile(thumb_path):  # 等锁期间别人已抽好，直接复用
            with open(thumb_path, "rb") as f:
                return f.read()
        # 临时文件必须以标准图片扩展名 .jpg 结尾：ffmpeg 靠扩展名推断输出格式
        #（muxer），写成 .part 会报 "Unable to choose an output format" 直接失败。
        # 前缀加 .part 便于识别半成品，os.replace 原子改名后即对缓存可见。
        tmp_path = thumb_path + ".part.jpg"
        if os.path.isfile(tmp_path):     # 清理上次残留的半成品
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        # -ss 1 快速定位到第 1 秒；scale 限制宽度并保持宽高比（-2 让 ffmpeg 自动算偶数高度）
        cmd = [
            get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
            "-ss", "1", "-i", video_path, "-frames:v", "1",
            "-vf", "scale='min(480,iw)':-2", tmp_path,
        ]
        try:
            subprocess.run(cmd, timeout=15, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.replace(tmp_path, thumb_path)  # 原子替换：只有完整文件才对缓存可见
        except Exception:
            if os.path.isfile(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            return None
    with open(thumb_path, "rb") as f:
        return f.read()


def _video_codec(video_path: str) -> str | None:
    """探测视频编码格式（如 hevc / h264），失败返回 None。

    实现：运行 ffmpeg -i，从错误输出里抓 "Video: xxx" 一段，
    取编码名（hevc/h264/...）。不实际解码，只读头部，速度很快。
    """
    try:
        from imageio_ffmpeg import get_ffmpeg_exe  # 自带 ffmpeg 二进制
    except Exception:
        return None
    try:
        proc = subprocess.run(
            [get_ffmpeg_exe(), "-hide_banner", "-i", video_path],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",  # 中文文件名也可能触发解码错误，用 replace 兜底
            timeout=30,
        )
        m = re.search(r"Stream.*Video:\s*(\w+)", proc.stderr)
        return m.group(1).lower() if m else None
    except Exception:
        return None


def get_video_duration(video_path: str) -> float | None:
    """读取视频时长（秒，保留小数）；读取失败返回 None。

    用 ffmpeg -i 解析 "Duration: HH:MM:SS.xx"（只读头部不实际解码，速度很快）。
    按"绝对路径 + 修改时间 + 大小"的 md5 命名缓存到 THUMB_DIR，
    视频文件更新后自动失效，避免每次重复启动 ffmpeg。
    """
    if not os.path.isfile(video_path):
        return None
    # m3u8 是分片流播放列表，无固定时长，跳过
    if video_path.lower().endswith(".m3u8"):
        return None
    # 缓存键带上 mtime + size：同名文件被替换后缓存自动失效
    st = os.stat(video_path)
    cache_key = f"{os.path.abspath(video_path)}|{int(st.st_mtime)}|{st.st_size}"
    cache_path = os.path.join(
        THUMB_DIR,
        hashlib.md5(cache_key.encode("utf-8")).hexdigest() + ".dur",
    )
    if os.path.isfile(cache_path):  # 命中缓存
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return float(f.read().strip())
        except Exception:
            pass
    try:
        from imageio_ffmpeg import get_ffmpeg_exe  # 自带 ffmpeg 二进制
    except Exception:
        return None
    try:
        proc = subprocess.run(
            [get_ffmpeg_exe(), "-hide_banner", "-i", video_path],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",  # 中文文件名可能触发解码错误，用 replace 兜底
            timeout=30,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
        if not m:
            return None
        h, mm, ss = m.groups()
        duration = int(h) * 3600 + int(mm) * 60 + float(ss)
        os.makedirs(THUMB_DIR, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(str(duration))
        return duration
    except Exception:
        return None


def get_image_thumb(image_path: str) -> bytes | None:
    """为图片生成压缩缩略图（JPEG 字节流）；不支持的格式返回 None。

    与 get_video_thumb 同样的思路：
    - 用 Pillow 读原图，等比缩到 400px 以内后转存 JPEG（质量 80）；
    - 按"图片绝对路径的 md5"命名缓存到 IMG_THUMB_DIR，命中直接读缓存；
    - 缩放前先按 EXIF 方向转正（手机竖拍照片常见），保证缩略图不横躺；
    - SVG（矢量，缩放无损）/ ICO（本身很小）不需要缩略，返回 None
      让调用方退回原图 URL。
    """
    if not os.path.isfile(image_path):
        return None
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".svg", ".ico"):  # SVG 矢量无限缩放无损；ICO 本身极小 → 不缩略
        return None

    # 保证缓存目录存在（已存在会抛 FileExistsError，忽略即可）
    os.makedirs(IMG_THUMB_DIR, exist_ok=True)
    thumb_path = os.path.join(
        IMG_THUMB_DIR,
        hashlib.md5(os.path.abspath(image_path).encode("utf-8")).hexdigest() + ".jpg",
    )
    if os.path.isfile(thumb_path):  # 命中缓存
        with open(thumb_path, "rb") as f:
            return f.read()

    try:
        from PIL import Image, ImageOps
        with Image.open(image_path) as im:
            im = ImageOps.exif_transpose(im)   # 先按 EXIF 方向转正（手机照片）
            im = im.convert("RGB")             # RGBA/调色板 → RGB（JPEG 不支持透明）
            im.thumbnail((400, 400))           # 等比缩到 400×400 以内
            im.save(thumb_path, "JPEG", quality=80)
    except Exception:
        return None
    with open(thumb_path, "rb") as f:
        return f.read()


def get_cover_thumb(image_path: str) -> bytes | None:
    """为文件夹封面生成高清晰度缩略图（JPEG 字节流）；不支持的格式返回 None。

    与 get_image_thumb 同思路但更清晰：
    - 等比缩到 900px 以内、JPEG 质量 88，供文件夹封面卡片展示
      （封面卡片比普通文件卡片大，400px 缩略图放大后会发虚）；
    - 缓存文件用独立的 ".cvr.jpg" 后缀，与 400px 缩略图互不覆盖；
    - SVG（矢量，缩放无损）/ ICO（本身很小）不需要缩略，返回 None
      让调用方退回原图 URL。
    """
    if not os.path.isfile(image_path):
        return None
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".svg", ".ico"):  # SVG 矢量无限缩放无损；ICO 本身极小 → 不缩略
        return None

    os.makedirs(IMG_THUMB_DIR, exist_ok=True)
    thumb_path = os.path.join(
        IMG_THUMB_DIR,
        hashlib.md5(os.path.abspath(image_path).encode("utf-8")).hexdigest() + ".cvr.jpg",
    )
    if os.path.isfile(thumb_path):  # 命中缓存
        with open(thumb_path, "rb") as f:
            return f.read()

    try:
        from PIL import Image, ImageOps
        with Image.open(image_path) as im:
            im = ImageOps.exif_transpose(im)   # 先按 EXIF 方向转正（手机照片）
            im = im.convert("RGB")             # RGBA/调色板 → RGB（JPEG 不支持透明）
            im.thumbnail((900, 900))           # 等比缩到 900×900 以内（封面更清晰）
            im.save(thumb_path, "JPEG", quality=88)
    except Exception:
        return None
    with open(thumb_path, "rb") as f:
        return f.read()


def _moov_at_head(video_path: str) -> bool:
    """判断 mp4 的 moov 元数据原子是否在文件头部（前 64KB 内）。

    浏览器播放 mp4 必须先读 moov（时长/轨道/索引）。moov 在末尾时，
    浏览器要发 Range 请求去文件尾部找，很多手机浏览器（尤其 Edge）处理不佳导致黑屏。
    返回 True 表示 moov 在头部，可直接播放。
    """
    try:
        with open(video_path, "rb") as f:
            head = f.read(65536)
        return head.find(b"moov") != -1
    except Exception:
        return True  # 读不到文件时按"可播放"处理，交给浏览器决定


def ensure_playable(video_path: str) -> str:
    """返回一个"手机浏览器也能播"的视频路径；原视频本就兼容时返回原路径。

    处理两种不兼容情况（按"源视频绝对路径 md5"缓存，只转换一次，之后直接复用）：
    1. HEVC/H.265 编码 → 手机浏览器不支持，转码为 H.264 + AAC（faststart 前置 moov）
    2. mp4/mov 等容器 moov 在文件末尾 → 用流拷贝（不重新编码）把 moov 挪到头部

    返回：可播放的绝对路径（可能是原文件，也可能是转换缓存文件）。
    """
    if not os.path.isfile(video_path):
        return video_path
    ext = os.path.splitext(video_path)[1].lower()
    # m3u8 是分片播放列表，无法直接转换，跳过
    if ext == ".m3u8":
        return video_path

    codec = _video_codec(video_path)
    if codec is None:
        return video_path  # 探测失败，保持原样

    is_hevc = codec in ("hevc", "h265")
    needs_moov_fix = ext in (".mp4", ".mov", ".m4v") and not _moov_at_head(video_path)
    if not is_hevc and not needs_moov_fix:
        return video_path  # 本来就兼容，直接返回原文件

    # 转换缓存：按"源视频绝对路径 md5"命名，重复访问直接复用。
    # faststart 产物 moov 必然在头部——缓存存在但 moov 不在头部，
    # 说明是并发截断/未写完整的损坏缓存，删掉让下面重新生成（自愈）。
    os.makedirs(TRANSCODE_DIR, exist_ok=True)
    cache_path = os.path.join(
        TRANSCODE_DIR,
        hashlib.md5(os.path.abspath(video_path).encode("utf-8")).hexdigest() + ".mp4",
    )
    if os.path.isfile(cache_path) and _moov_at_head(cache_path):
        return cache_path

    # 并发保护：同一个视频同时被多个请求（探测/播放/拖动）触发转码时，
    # 串行执行 + 原子写入，防止 ffmpeg 互相 -y 截断缓存文件导致"视频放不了"。
    lock = _path_lock("trans:" + os.path.abspath(video_path))
    with lock:
        if os.path.isfile(cache_path) and _moov_at_head(cache_path):
            return cache_path  # 等锁期间别人已转好，直接复用
        if os.path.isfile(cache_path):  # 存在但已损坏，删掉重转
            try:
                os.remove(cache_path)
            except OSError:
                pass

        try:
            from imageio_ffmpeg import get_ffmpeg_exe
        except Exception:
            return video_path

        # 同封面缩略图：临时文件必须以 .mp4 结尾，ffmpeg 才能识别输出格式（muxer），
        # 写成 .part 会直接报 "Unable to choose an output format" 导致转码失败。
        tmp_path = cache_path + ".part.mp4"
        if os.path.isfile(tmp_path):     # 清理上次残留的半成品
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        if is_hevc:
            # HEVC → H.264 + AAC；faststart 把 moov 前置。压成 1080p 以内控制体积与手机解码压力
            cmd = [
                get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                "-i", video_path,
                "-vf", "scale='min(1920,iw)':-2",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-movflags", "+faststart", tmp_path,
            ]
        else:
            # moov 在末尾：流拷贝（不重新编码，秒级完成）只调整 moov 位置
            cmd = [
                get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                "-i", video_path, "-c", "copy", "-movflags", "+faststart", tmp_path,
            ]
        try:
            subprocess.run(cmd, timeout=600, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.replace(tmp_path, cache_path)  # 原子替换：只有完整文件才对缓存可见
            return cache_path
        except Exception:
            if os.path.isfile(tmp_path):  # 转码失败，清理半成品
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            return video_path  # 转换失败时退回原文件，至少桌面浏览器还能播
