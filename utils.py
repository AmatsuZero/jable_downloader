import json
import os
from pathlib import Path
import re
import requests
import time
from urllib import parse

from config import CONF

video_index_cache_filename = "./jable_index_cache.json"

HEADERS = CONF.get("headers")


def get_video_ids_map_from_cache():
    cache = {}
    if os.path.exists(video_index_cache_filename):
        with open(video_index_cache_filename, 'r', encoding='utf-8') as f:
            cache = json.load(f)

    return cache


def _add_proxy(query_param, retry_index, ignore_proxy):
    if not ignore_proxy or retry_index > 1:
        proxies_config = CONF.get('proxies', None)
        if proxies_config and 'http' in proxies_config and 'https' in proxies_config:
            query_param['proxies'] = proxies_config


def requests_with_retry(url, headers=HEADERS, timeout=20, retry=5, ignore_proxy=False):
    query_param = {
        'headers': headers,
        'timeout': timeout
    }

    for i in range(1, retry+1):
        try:
            _add_proxy(query_param, i, ignore_proxy)
            response = requests.get(url, **query_param)
        except Exception as e:
            if i == 1 and ignore_proxy:
                continue
            if i == retry:
                print("Unexpected Error: %s" % e)
            time.sleep(120 * i)
            continue

        if str(response.status_code).startswith('2'):
            return response
        else:
            time.sleep(120 * i)
            continue
    raise Exception("%s exceed max retry time %s." % (url, retry))


def scrapingant_requests_get(url, retry=5):
    if not CONF.get('sa_token'):
        print("You need to go to https://app.scrapingant.com/ website to\n apply for a token and fill it in the sa_token field")
        exit(1)

    query_param = {
        "timeout": 180
    }

    sa_api = 'https://api.scrapingant.com/v2/general'
    qParams = {'url': url, 'x-api-key': CONF.get('sa_token'), 'browser': 'false'}
    if CONF.get('sa_mode', None) == 'browser':
        qParams['browser'] = 'true'
    reqUrl = f'{sa_api}?{parse.urlencode(qParams)}'

    proxies_config = CONF.get('proxies', None)

    if proxies_config and 'http' in proxies_config and 'https' in proxies_config:
        query_param['proxies'] = proxies_config

    for i in range(1, retry+1):
        try:
            response = requests.get(reqUrl, **query_param)
        except Exception as e:
            if i == retry:
                print("Unexpected Error: %s" % e)
            time.sleep(120 * i)
            continue

        if str(response.status_code).startswith('2'):
            return response
        else:
            time.sleep(120 * i)
            continue
    raise Exception("%s exceed max retry time %s" % (url, retry))


def update_video_ids_cache(data):
    with open(video_index_cache_filename, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


def get_local_video_list(path="./"):
    re_extractor = re.compile(r"[a-zA-Z0-9]{2,}-\d{3,}")

    def extract_movie_id(full_name):
        foo = re_extractor.search(full_name)
        movie_id = None
        if foo:
            movie_id = foo.group(0).lower()
        return movie_id

    result = {extract_movie_id(foo.name) for foo in list(Path(path).rglob("*.mp4"))}
    if None in result:
        result.remove(None)

    return result


def merge_mp4(input_path, output_path, video_name, ts_list):
    start_time = time.time()
    print('开始合成视频...')

    for i in range(len(ts_list)):
        file = ts_list[i].split('/')[-1][0:-3] + '.mp4'
        full_path = os.path.join(input_path, file)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f1:
                with open(os.path.join(output_path, video_name + '.mp4'), 'ab') as f2:
                    f2.write(f1.read())
        else:
            # TODO: retry download
            print(file + "不存在, 跳过该文件， 最终文件可能不完整 ")

    end_time = time.time()
    print('消耗 {0:.2f} 秒合成视频'.format(end_time - start_time))
    print('%s 下载完成!' % video_name)


def delete_m3u8(folder_path):
    files = os.listdir(folder_path)
    for file in files:
        if file.endswith('.m3u8'):
            os.remove(os.path.join(folder_path, file))
