# 导入所需的库
import os
import win32api
import platform
from flask import Flask, render_template, request
from pathlib import Path
import textract

# 创建一个flask应用
app = Flask(__name__)

# 定义一个函数，用于从文件中提取文本，并返回包含关键字的行号和内容
def extract_text(file_path, keyword):
    # 根据文件扩展名，选择不同的方法来提取文本
    ext = file_path.suffix.lower()
    if ext == ".txt":
        # 对于txt文件，直接读取内容
        text = file_path.read_text(encoding="utf-8")
    elif ext in ['.pdf', '.doc', '.docx']:
        # 对于pdf/word文件，使用textract库来提取内容
        text = textract.process(file_path, encoding="utf-8").decode("utf-8")
    else:
        # 对于其他类型的文件，返回空结果
        return []

    # 将文本按行分割，并创建一个空列表来存储结果
    lines = text.splitlines()
    results = []

    # 遍历每一行，如果包含关键字，就将行号和内容添加到结果列表中
    for i, line in enumerate(lines, 1):
        if keyword in line:
            results.append((i, line))

    # 返回结果列表
    return results

# 定义一个路由，用于显示主页
@app.route("/")
def index():
    # 获取用户选择的目录，默认为根目录
    folder = request.args.get("folder", os.path.abspath(os.sep))
    # 获取用户输入的关键字，默认为空
    keyword = request.args.get("keyword", "")
    # 创建一个空列表来存储查询结果
    results = []
    # 如果用户输入了关键字，就遍历目录下的所有txt/pdf/word文件，并调用extract_text函数来获取结果
    if keyword:
        for file_path in Path(folder).glob("*.*"):
            if file_path.suffix.lower() in [".txt", ".pdf", ".doc", ".docx"]:
                matches = extract_text(file_path, keyword)
                if matches:
                    results.append((file_path, matches))
    # 渲染主页模板，并传递参数
    return render_template("index.html", folder=folder, keyword=keyword, results=results,
                           Path=Path, os=os, win32api=win32api, platform=platform)

# 运行flask应用
if __name__ == "__main__":
    app.run(debug=True)
