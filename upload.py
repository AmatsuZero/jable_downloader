"""Module providingFunction upload file to aliyunpan."""
import sys
import getopt
import os
import subprocess
import zipfile
import tempfile
from typing import Tuple
import requests
from aligo import Aligo


def combine(zip_file: str, tmpd: str):
    """Function combine video and cover image."""
    name = os.path.basename(zip_file)
    out = os.path.join(tmpd, name)
    pic = os.path.join(tmpd, "wallpaper" + name)
    # 获取伪装图片

    img_data = requests.get("https://pic.re/image", timeout=300).content
    with open("image_name.jpg", "wb") as handler:
        handler.write(img_data)

    print("开始合并文件")
    subprocess.call(["cat", zip_file, pic, ">", out], stdout=subprocess.DEVNULL)
    print("合并结束")


def get_file(argv: list[str]) -> Tuple[str, str, str]:
    """Function get video / image / output file path."""
    image_file = ""
    video_file = ""
    output_file = ""
    help_line = "upload.py -v <video> -i <image> -o <outputfile>"

    try:
        opts, _ = getopt.getopt(
            argv, "hv:i:o:", ["help", "video=", "image=", "output="]
        )
    except getopt.GetoptError:
        print(help_line)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "help"):
            print(help_line)
            sys.exit()
        elif opt in ("-v", "--video"):
            video_file = arg
        elif opt in ("-i", "--image"):
            image_file = arg
        elif opt in ("-o", "--output"):
            output_file = arg
    return video_file, image_file, output_file


if __name__ == "__main__":
    folder_name = input()

    cwd = os.getcwd()
    video, image, output = get_file(sys.argv[1:])
    video = os.path.join(cwd, video)
    image = os.path.join(cwd, image)
    output = os.path.join(cwd, output)

    ali = Aligo()
    # 创建文件夹
    result = ali.create_folder(name=folder_name)

    if result.code != "0":
        print(f"阿里云盘创建文件夹失败：{result.message}")
        sys.exit(result.code)

    with tempfile.TemporaryDirectory() as tmpdir:
        print("开始生成原始压缩包")
        list_files = [video, image]
        raw_file = os.path.join(tmpdir, "raw.zip")
        with zipfile.ZipFile(raw_file, "w") as zipF:
            for file in list_files:
                zipF.write(file, compress_type=zipfile.ZIP_DEFLATED)
        print("原始压缩包生成完成")

        print("开始拆分成小压缩包 (500MB)")
        smallzip = os.path.join(tmpdir, "small.zip")
        subprocess.call(["zip", raw_file, "--out", smallzip, "-s", "500m"])
        print("拆分成小压缩包完成")

        os.walk(tmpdir)
