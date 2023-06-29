# 导入所需的库
import os
import datetime

import win32api
import platform
from flask import Flask, render_template, request, send_file
from pathlib import Path
from io import StringIO, BytesIO
import textract
from urllib import parse
from chardet import detect
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 创建一个flask应用
app = Flask(__name__, static_url_path='', static_folder='templates', template_folder='templates')
progress = 0  # 定义一个全局变量progress
total = 0  # 获取文件总数
count = 0  # 用来记录已经搜索过的文件数


# 用于从文件中提取文本，并返回包含关键字的行号和内容
def extract_text(file_path, keyword):
    print("Searching \"" + str(file_path) + "\"")
    text = ""
    try:
        # 根据文件扩展名，选择不同的方法来提取文本
        ext = file_path.suffix.lower()
        if ext == ".txt":
            # 对于txt文件，直接读取内容，若遇到编码错误，就换一种编码
            # text = file_path.read_text()
            is_success = False
            # 按常用度列举编码方式
            encodings = ['utf-8', 'gbk', 'iso-8859-1', 'windows-1252', 'big5', 'shift_jis', 'euc-jp', 'euc-kr',
                         'utf-16', 'utf-32', 'ascii']
            for encoding in encodings:
                try:
                    text = file_path.read_text(encoding=encoding)
                    is_success = True
                    break
                except UnicodeDecodeError:
                    pass
            if not is_success:  # 还没试出来，用detect模块
                with open(file_path, 'rb') as ef:
                    data = ef.read()
                    result = detect(data)
                    if result is None:
                        return []
                    else:
                        try:
                            text = file_path.read_text(encoding=result['encoding'])
                        except UnicodeDecodeError:
                            return []
        elif ext in ['.pdf', '.doc', '.docx']:
            # 对于pdf/word文件，使用textract库来提取内容
            text = textract.process(str(file_path)).decode('utf-8')
        else:
            # 对于其他类型的文件，返回空结果
            return []
    except Exception:
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


def search_a_file(file_path: Path, keyword, lock):
    global progress, count, total
    results = []
    if file_path.suffix.lower() in [".txt", ".pdf", ".doc", ".docx"]:
        matches = extract_text(file_path, keyword)
        if matches:
            results.append((file_path, matches))
    # 在需要操作共享变量的代码块前，获取锁
    lock.acquire()
    # 操作共享变量
    # 每搜索完一个文件，计数加一
    count += 1
    # 根据计数和总数计算进度百分比，并四舍五入至2位小数
    progress = round(count / total * 100, 1)
    # 在操作完成后，释放锁
    lock.release()
    print(f"-----------{count}/{total}，progress: {progress}")
    return results

# 递归搜索文件的函数，接收folder和keyword参数
def search_files_threading(folder, keyword, lock):
    results = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = Path(os.path.join(root, file))
            results.extend(search_a_file(file_path, keyword, lock))
    return results

def search_files(folder, keyword):
    global progress  # 使用全局变量progress
    global total
    global count
    results = []
    # 创建一个 ThreadPoolExecutor 对象，用来管理线程池
    executor = ThreadPoolExecutor()
    # 创建一个空列表，用来存储 Future 对象
    futures = []
    # 多线程环境下，创建同步锁操作共享变量
    lock = threading.Lock()
    # 遍历folder下的所有子文件夹，调用search_folder函数，并提交一个任务到线程池中，收集返回的 Future 对象
    for sub in os.listdir(folder):
        sub_path = os.path.join(folder, sub)
        if os.path.isdir(sub_path):
            future = executor.submit(search_files_threading, sub_path, keyword, lock)
            futures.append(future)
        else:
            sub_path = Path(sub_path)
            results.extend(search_a_file(sub_path, keyword, lock))
    # 等待所有任务完成，并获取最终的结果列表
    for future in as_completed(futures):
        results.extend(future.result())
    return results  # 返回搜索结果


class SearchThread(threading.Thread):
    def __init__(self, folder, keyword, results, lock):
        super().__init__()
        self.folder = folder
        self.keyword = keyword
        self.results = results
        self.lock = lock

    def run(self):
        # 调用原来的搜索函数
        search_result = search_files(self.folder, self.keyword)
        # 获取锁
        self.lock.acquire()
        # 将搜索结果添加到共享列表中
        self.results.extend(search_result)
        # 释放锁
        self.lock.release()

# 定义一个路由，用于显示主页
@app.route("/")
def index():
    #记录开始时间
    starttime = datetime.datetime.now()
    global progress  # 使用全局变量progress
    global total
    global count
    progress = 0  # 初始化进度为0
    total = 0  # 初始化查询文件总数为0
    count = 0  # 用来记录已经搜索过的文件数
    # 获取用户选择的目录，默认为根目录
    folder = request.args.get("folder")
    os_name = platform.system()
    if folder is None:
        # 根据操作系统设置默认值
        if os_name == "Windows":
            # Windows下展示所有驱动器
            folder = win32api.GetLogicalDriveStrings()
        elif os_name == "Linux":
            # Linux下展示根目录
            folder = os.path.abspath(os.sep)
        elif os_name == "Darwin":
            # Mac OS X下展示根目录
            folder = os.path.abspath(os.sep)
        else:
            # 其他操作系统暂不支持
            return "Sorry, your operating system is not supported."
    else:
        # 因为input标签的value属性无法识别"\0"字符导致乱码，所以保存url编码后的folder，这里再url解码
        folder = parse.unquote(folder)
    # 创建一个空列表来存储查询结果
    results = []
    # 获取用户输入的关键字，默认为空
    keyword = request.args.get("keyword", "")
    # 如果用户输入了关键字，就遍历目录下的所有txt/pdf/word文件，并调用extract_text函数来获取结果
    if keyword:
        if os_name == "Windows" and folder == win32api.GetLogicalDriveStrings():
            drives = folder.split('\x00')[:-1]
            for drive in drives:  # 对所有盘符
                for root, dirs, files in os.walk(drive):
                    total += len(files)  # 累加每个文件夹下的文件数
            for drive in drives:  # 对所有盘符
                results.extend(search_files(drive, keyword))
        else:
            for root, dirs, files in os.walk(folder):
                total += len(files)  # 累加每个文件夹下的文件数
            results = search_files(folder, keyword)
        print(f"progress: {progress}")
    #记录结束时间
    endtime = datetime.datetime.now()
    #打印
    print('运行时间:', (endtime - starttime).microseconds, 'ms')
    # 渲染主页模板，并传递参数
    return render_template("index.html", folder=folder, keyword=keyword, results=results,
                           DriveStrings=win32api.GetLogicalDriveStrings() if os_name == "Windows" else None,
                           Path=Path, os=os, win32api=win32api, platform=platform, parse=parse)


def err_call_back(err):
    print(f'出错啦~ error：{str(err)}')
    raise err


# 定义一个新的路由/progress，返回全局变量progress的值
@app.route('/progress')
def get_progress():
    global progress
    print(progress)
    return str(progress)


# 定义一个路由，用于保存用户选择的结果到文本，并下载
@app.route("/save")
def save():
    # 获取用户选择的结果，格式为"文件路径:行号"，例如"test.txt:3"
    selections = request.args.getlist("selections")
    # 创建一个StringIO对象来存储文本内
    output = StringIO()
    # 遍历每一个选择，根据文件路径和行号，提取对应的内容，并写入到StringIO对象中
    for file_path in selections:
        output.write(file_path + "\n")
        output.write("-" * 50 + "\n")
        line_nums = request.args.getlist(file_path)
        file_lines = extract_text(Path(file_path), "")
        for line_number in line_nums:
            line_number = int(line_number)
            content = file_lines[line_number - 1][1]
            output.write(f"Line {line_number} \t {content}\n")
        output.write("\n\n")
    output_b = BytesIO()
    output_b.write(output.getvalue().encode('utf-8'))
    output_b.seek(0)
    output.close()
    return send_file(output_b, as_attachment=True, download_name="results.txt")


# 运行flask应用
if __name__ == "__main__":
    app.run(debug=True)
