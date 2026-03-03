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
    
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    image.thumbnail((500, 500))
    
    new_filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, new_filename)
    
    image.save(filepath, "JPEG", quality=85, optimize=True)
    
    return f"/uploads/avatars/{new_filename}"