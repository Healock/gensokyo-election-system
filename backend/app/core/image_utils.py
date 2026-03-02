import os
import uuid
from PIL import Image
import io

# 确保上传目录存在
UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def compress_and_save_image(file_bytes: bytes, filename: str) -> str:
    """
    接收图片字节流，压缩至最大 500x500，并转为高保真 JPEG 保存
    返回可供前端访问的相对 URL
    """
    image = Image.open(io.BytesIO(file_bytes))
    
    # 如果是带有透明通道的 PNG (RGBA) 或 P 模式，转换为 RGB 以便保存为 JPEG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
        
    # 等比例缩放，限制最大宽高为 500x500
    image.thumbnail((500, 500))
    
    # 生成随机且唯一的文件名
    new_filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, new_filename)
    
    # 压缩保存 (quality=85 可以在画质和大小间取得完美平衡)
    image.save(filepath, "JPEG", quality=85, optimize=True)
    
    # 返回静态访问路径
    return f"/uploads/avatars/{new_filename}"