# 按照 star 数量搜索开源项目
# 每次请求最多返回1000个，所以要动态缩放窗口
import requests
import time
import typing
import datetime
import json
from utils import TokenManager 
TM = TokenManager(1)

def get_next_url(link_str):  
    for url in link_str.split(', '):
        if 'rel="next"' in url:
            next_page_url = url.split(';')[0]
            return next_page_url.strip("<>")
        
def format_timestamp(time_stamp: str):
    try:
        time_stamp = int(time_stamp)
        # 将 datetime 对象转换为人性化时间格式
        time_stamp = datetime.datetime.fromtimestamp(time_stamp)
        reset_time_str = time_stamp.strftime('%Y-%m-%d %H:%M:%S')
        return reset_time_str
    except Exception as e:
        print(e)
    return ""

        
def handle_url(url: str) ->  typing.Tuple[typing.Union[str, None], int, any]:
    response = TM.make_request(url)

    data = response.json()
    # for row in data['items']:
    #     document = row
    #     try:
    #         collection.update_one({'_id':row['id'],},{'$set':document },upsert=True)
    #     except Exception as e:
    #         print(e)
    # import pdb
    # pdb.set_trace()
    total_count = response.json()['total_count']
    print(url, total_count,len(data['items']))

    # for k,v in response.headers.items():
    #     print(k,v)
    link_str = response.headers.get("Link")
    if link_str:
        next_url = get_next_url(link_str)
        if next_url:
            return next_url, total_count, data['items']
    return None, total_count, data['items']

# 自动滑动窗口控制，缩小窗口后， 3次内禁止放大窗口
def handle_star_range(start:int,end:int,window=100, language=""):
    min_star,max_start = start,start
    
    ret_repo_total_list = []

    language_str = f" language:{language}"
    print("start language:,", language)
    resize_flag = 0
    while min_star < end :
        max_start = min_star + window
        url = f"https://api.github.com/search/repositories?q=stars:{min_star}..{max_start}{language_str}&sort=stars&order=desc&per_page=100"

        next_url, total_count, repo_data_list = handle_url(url)
        ret_repo_total_list.extend(repo_data_list)
        if total_count >= 1000:
            # 缩小窗口：
            window = window // 2
            resize_flag = 3
            print("window size reduce", window)
            continue
        elif total_count <= 400 and resize_flag <= 0:
            window = window * 2
            print("window size amplify", window)
        
        if (next_url):
            query_list = [next_url, ]
            while(query_list):
                url = query_list.pop()
                next_url, _, repo_data_list = handle_url(url)
                ret_repo_total_list.extend(repo_data_list)
                if (next_url):
                    query_list.append(next_url)
            
        resize_flag -=1
        min_star = max_start
    return ret_repo_total_list


if __name__ == "__main__":
    # handle_star_range(1000, 1000000)
    # handle_star_range(1000, 3000)
    repo_list = handle_star_range(1000, 1000000, language="python")
    with open("./out/python.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="java")
    with open("./out/java.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="c")
    with open("./out/c.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="c++")
    with open("./out/c++.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="go")
    with open("./out/go.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="JavaScript")
    with open("./out/JavaScript.json", 'wt') as f:
        json.dump(repo_list, f)

    repo_list = handle_star_range(1000, 1000000, language="TypeScript")
    with open("./out/TypeScript.json", 'wt') as f:
        json.dump(repo_list, f)


    # repo_list = handle_star_range(1000, 1000000, "java")