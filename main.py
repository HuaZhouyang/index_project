# 导入所需的库
import os
import win32api
import platform
from flask import Flask, render_template, request, send_file
from pathlib import Path
from io import StringIO
import re
import textract

# 创建一个flask应用
app = Flask(__name__, static_url_path='', static_folder='templates', template_folder='templates')

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
    folder = request.args.get("folder")
    if folder is None:
        # 根据操作系统设置默认值
        os_name = platform.system()
        if os_name == "Windows":
            # Windows下展示所有驱动器
            folder = win32api.GetLogicalDriveStrings()
            print(folder)
        elif os_name == "Linux":
            # Linux下展示根目录
            folder = os.path.abspath(os.sep)
        elif os_name == "Darwin":
            # Mac OS X下展示根目录
            folder = os.path.abspath(os.sep)
        else:
            # 其他操作系统暂不支持
            return "Sorry, your operating system is not supported."

    # 获取用户输入的关键字，默认为空
    keyword = request.args.get("keyword", "")
    # 创建一个空列表来存储查询结果
    results = []
    # 如果用户输入了关键字，就遍历目录下的所有txt/pdf/word文件，并调用extract_text函数来获取结果
    if keyword:
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".txt") or file.endswith(".txt") or file.endswith(".txt") or file.endswith(".txt"):
                    matches = extract_text(Path(os.path.join(root, file)), keyword)
                    if matches:
                        results.append((Path(os.path.join(root, file)), matches))
    # 渲染主页模板，并传递参数
    return render_template("index.html", folder=folder, keyword=keyword, results=results,
                           Path=Path, os=os, win32api=win32api, platform=platform)

# 定义一个路由，用于保存用户选择的结果到文本，并下载
@app.route("/save")
def save():
    # 获取用户选择的结果，格式为"文件路径:行号"，例如"test.txt:3"
    selections = request.args.getlist("selections")
    # 创建一个StringIO对象来存储文本内
    output = StringIO()
    # 遍历每一个选择，根据文件路径和行号，提取对应的内容，并写入到StringIO对象中
    for selection in selections:
        file_path = selection
        output.write(f"{file_path}" + "\n")
        output.write("-" * 50 + "\n")
        line_nums = request.args.getlist(file_path)
        for line_num in line_nums:
            line_number = int(line_num)
            content = extract_text(Path(file_path), "")[line_number - 1][1]
            output.write(f"Line {line_number}: {content}\n\n")
        output.write("-" * 100 + "\n")
    # 将StringIO对象的内容保存到一个临时文件中，并返回给用户下载
    with open('temp.txt', 'w') as f:
        f.write(output.getvalue())
    return flask.send_file('temp.txt', as_attachment=True, download_name="results.txt")

# 运行flask应用
if __name__ == "__main__":
    app.run(debug=True)
