#!/usr/bin/env python3
"""
Данная утилита предназначена для скачивания файлов с имиджборды 2ch.hk.

Created by https://github.com/kiriharu
Re-writen by https://github.com/hatkidchan
"""
import requests
import traceback
import re
import os

IGNORE_TYPES = (100,)  # 100=sticker


def mkdir(path: str):
    if not os.path.exists(path):
        os.mkdir(path)
        print("[I] mkdir %r" % path)
    else:
        print("[I] directory %r already exists" % path)

def download_file(fileobject: dict, out_folder: str=".", status: str=None):
    """
    Download file. Parameters given in file object
    @param fileobject: dict{path,fullname,md5}
    @param out_folder: str
    @param status: str
    """
    url = "https://2ch.hk" + fileobject["path"]
    fallback = fileobject["name"]
    name = fileobject["md5"] + " " + fileobject.get("fullname", fallback)
    path = os.path.join(out_folder, name)
    status = ("[%s]" % status) if status else ""
    try:
        with open(path, "wb") as fd:
            with requests.get(url, stream=True) as rq:
                expected_size = int(rq.headers.get("Content-Length", 1))
                downloaded = 0
                for chunk in rq.iter_content(chunk_size=16384):
                    downloaded += len(chunk)
                    progress = downloaded / expected_size
                    line = "[I] %35s: [%-20s] %7.3f%% %s" % (fileobject["path"],
                                                     "=" * int(progress * 20),
                                                     progress * 100,
                                                     status)
    
                    print(line, end="\r", flush=1)
                    fd.write(chunk)
                    fd.flush()
    except IOError as e:
        print("[E] Filed to open file %r: %r" % (name, e))
    except Exception as e:
        print("[E] Exception occurred: %r" % e)
    else:
        print("")

def iter_files(board: str, thread: int):
    """
    Yields files from thread
    @param board: str, board letters (example, "b")

    @return generator(fileobject:dict, tuple(i, n_posts), tuple(j, n_files))
    """
    thread_url = f"https://2ch.hk/{board}/res/{thread}.json"
    print("[I] Getting", thread_url)
    data = requests.get(thread_url).json()
    for thread in data["threads"]:
        n_posts = len(thread["posts"])
        for i, post in enumerate(thread["posts"], 1):
            n_files = len(post["files"])
            for j, fileobj in enumerate(post["files"], 1):
                if fileobj["type"] not in IGNORE_TYPES:
                    yield fileobj, (i, n_posts), (j, n_files)

def iter_threads(board: str):
    for index in range(1, 10):
        index = "index" if index == 1 else index
        page_url = f"https://2ch.hk/{board}/{index}.json"
        print("[I] Getting", page_url)
        data = requests.get(page_url).json()
        threads = len(data["threads"])
        for i, thread in enumerate(data["threads"], 1):
            thread_num = thread["thread_num"]
            yield thread_num, (i, threads)

def main():
    print("Welcome to 2chdownloader!")
    print("Type board name as 'name' to download all posts from board")
    print("Type thread as 'board/thread' to download one thread")
    print("Type 'exit' to exit")
    while True:
        try:
            line = input("> ")
            if line == "exit":
                return
            elif re.match(r"^(\w+)$", line):
                mkdir(line)
                for thread, (i, threads) in iter_threads(line):
                    out_path = '%s/%s' % (line, thread)
                    mkdir(out_path)
                    print("[I] Downloading %s (%d/%d)" % (thread, i, threads))
                    for fileobj, a, b in iter_files(line, thread):
                        status = '%3d/%3d:%d/%d' % (a + b)
                        download_file(fileobj, out_path, status)
                print("[I] Done")
            elif re.match(r"^(\w+)\/(\d+)$", line):
                board, thread = line.split("/")
                mkdir(board)
                out_path = os.path.join(board, thread)
                mkdir(out_path)
                for fileobj, a, b in iter_files(board, int(thread)):
                    status = '%3d/%3d:%d/%d' % (a + b)
                    download_file(fileobj, out_path, status)
                print("[I] Done")
            else:
                print("Something went wrong")
        except KeyboardInterrupt:
            print("[I] Type 'exit' for exit")
        except Exception as e:
            for line in traceback.format_exc().split("\n"):
                print("[E] %s" % line)

if __name__ == '__main__':
    main()

