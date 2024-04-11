# clone github 中的项目, 在 repositories 添加 _clone_state 字段， 1，表示成功
import pathlib
import subprocess
import shutil
import logging
import shutil
import random
import uuid
import json
import tarfile
from utils import get_console_handler
from multiprocessing import Pool
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(get_console_handler())

BASIC_PATH = pathlib.Path("/tmp/github")

BASIC_PATH.mkdir(exist_ok=True)


def generate_uuid_as_directory_name():
    # 生成 UUID
    uuid_str = str(uuid.uuid4())

    # 处理 UUID 字符串，使其适合作为目录名
    directory_name = uuid_str.replace("-", "_")  # 将 "-" 替换为 "_"

    return directory_name


def compree_test(dest_path):
    # tarfile

    totle_size = 0
    for file_path in dest_path.glob("**/*"):
        if file_path.is_file():
            totle_size += file_path.stat().st_size

    ret_data = {}
    ret_data["size"] = totle_size

    out_file = pathlib.Path(f"/home/codespace/{generate_uuid_as_directory_name()}")

    with tarfile.open(out_file.as_posix(), "w|gz") as f:
        f.add(dest_path)
    d_size = out_file.stat().st_size
    ret_data["gz"] = d_size

    with tarfile.open(out_file, "w|bz2") as f:
        f.add(dest_path)
    d_size = out_file.stat().st_size
    ret_data["bz2"] = d_size

    with tarfile.open(out_file, "w|xz") as f:
        f.add(dest_path)
    d_size = out_file.stat().st_size
    ret_data["xz"] = d_size

    out_file.unlink()
    return ret_data


def run_command(doc):
    # clone_url_1 = "https://ghproxy.com/" + doc['clone_url']
    # clone_url_2 = "https://gitclone.com/github.com/" + doc['clone_url'].replace("https://github.com/","")
    # clone_urls = [clone_url_1,clone_url_2, doc['clone_url']]
    clone_urls = [ doc['clone_url']]
    # random.shuffle(clone_urls)
    for clone_url in clone_urls: 
        full_name = doc['full_name']
        repositories_path = pathlib.Path(BASIC_PATH).joinpath(full_name)
        if len(full_name) > 0 and repositories_path.exists():
            try:
                shutil.rmtree(repositories_path)
            except Exception as e:
                logger.warn(e)
                pass
            
        repositories_path.mkdir(parents=True,exist_ok=True)
        logger.info(f"Git clone {full_name} start. {clone_url}")
        try:
            result = subprocess.run(['git', 'clone', '--depth',"1", clone_url, repositories_path, ], capture_output=True, timeout=30*60)
        except subprocess.TimeoutExpired:
            logger.info("The git clone command timed out.")
            continue
        
        # 检查命令的执行结果
        if result.returncode == 0:
            logger.info(f"Git clone {full_name} succeeded.")
            shutil.rmtree(repositories_path.joinpath(".git"))
            ret = compree_test(repositories_path)
            shutil.rmtree(repositories_path)
            ret['repo'] = full_name
            logger.info(f"repo {full_name} test successed.")
            return ret
        else:
            logger.info(f"Git clone {full_name} failed.")
            logger.info(f"Error message: {result.stderr.decode('utf-8')}")
    return None
    
def handle_language_top_repo(top_limit=1000, language=""):
    workspace = "./out"
    if not language:
        logger.info("place spefic language")
        return
    
    repo_info_path = pathlib.Path(workspace).joinpath(f"{language}.json")
    with open(repo_info_path,'rt')as f:
        data = json.load(f)

    data.sort(key=lambda x:-x['stargazers_count'])

    logger.info("languag: %s. total repo count: %s", language, len(data))
    logger.info("start: %s", top_limit)

    with Pool(2) as p:
        ret_list = p.starmap(
            run_command,
            [(doc,) for doc in data[:top_limit]],
            chunksize=1,
        )
    return ret_list


if __name__ == "__main__":

    language_list = ['python','java','c++','go','JavaScript', 'TypeScript']
    for name in language_list:
        ret_data = handle_language_top_repo(top_limit=1000, language=name)
        df = pd.DataFrame(ret_data)
        df.to_csv(f"./out/{name}_compress.csv",index=False)
    