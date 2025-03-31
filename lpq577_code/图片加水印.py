from PIL import Image, ImageEnhance
import requests
from io import BytesIO
import os

def add_image_watermark(
        image_url,
        watermark_image_path,
        output_folder=r"C:\Users\Administrator\Desktop\水印图片测试",
        opacity=0.7,
        image_scale=0.2,
        margin=10  # 新增margin参数，默认10像素
):
    """
    给网络图片添加图片水印(右上角，可调整边距)

    参数:
        image_url: 网络图片的URL
        watermark_image_path: 图片水印路径
        output_folder: 输出文件夹路径
        opacity: 水印透明度(0.0-1.0)
        image_scale: 图片水印缩放比例(0.0-1.0)
        margin: 水印与右上角边界的距离(像素)
    """
    try:
        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)

        # 下载网络图片
        response = requests.get(image_url)
        main_image = Image.open(BytesIO(response.content)).convert("RGBA")

        # 生成输出文件名
        filename = os.path.basename(image_url).split('?')[0]
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            filename = "watermarked_image.jpg"
        output_path = os.path.join(output_folder, filename)

        # 打开水印图片
        watermark = Image.open(watermark_image_path).convert("RGBA")

        # 调整水印大小
        watermark_size = (
            int(main_image.width * image_scale),
            int(main_image.height * image_scale)
        )
        watermark = watermark.resize(watermark_size, Image.Resampling.LANCZOS)

        # 调整透明度
        if opacity < 1.0:
            alpha = watermark.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            watermark.putalpha(alpha)

        # 计算位置(右上角，带边距)
        x = main_image.width - watermark.width - margin  # 右对齐，减去边距
        y = margin  # 上边距

        # 确保位置不会超出图像范围
        x = max(0, x)  # 确保x不小于0
        y = max(0, y)  # 确保y不小于0

        # 合成水印
        main_image.paste(watermark, (x, y), watermark)

        # 保存图片
        main_image.convert("RGB").save(output_path, quality=95)
        return output_path

    except Exception as e:
        print(f"处理图片时出错: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    add_image_watermark(
        image_url="https://gcs.rimg.com.tw/g1/6/60/a3/21727657119907_741.png",
        watermark_image_path=r"C:\Users\Administrator\Desktop\水印图片测试\店铺水印\LOGO\tehs92.png",
        opacity=1,
        image_scale=0.18,
        margin=3
    )