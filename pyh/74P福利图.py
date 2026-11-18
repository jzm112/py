# -*- coding: utf-8 -*-
import sys
import re
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from base.spider import Spider

requests.packages.urllib3.disable_warnings()


class Spider(Spider):
    def getName(self):
        return "74P福利(漫画版)"

    def init(self, extend=""):
        super().init(extend)
        self.base_url = "https://www.74p.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': self.base_url + '/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def destroy(self):
        if hasattr(self, 'session'):
            self.session.close()

    def fetch(self, url, headers=None):
        req_headers = headers or self.headers.copy()
        try:
            return self.session.get(url, headers=req_headers, timeout=10, verify=False, allow_redirects=True)
        except:
            return None

    def homeContent(self, filter):
        cats = [
            {"type_name": "=== 写真 ===", "type_id": "ignore"},
            {"type_name": "秀人网", "type_id": "xiurenwang"},
            {"type_name": "语画界", "type_id": "yuhuajie"},
            {"type_name": "花漾", "type_id": "huayang"},
            {"type_name": "星颜社", "type_id": "xingyanshe"},
            {"type_name": "嗲囡囡", "type_id": "feilin"},
            {"type_name": "爱蜜社", "type_id": "aimishe"},
            {"type_name": "波萝社", "type_id": "boluoshe"},
            {"type_name": "尤物馆", "type_id": "youwuguan"},
            {"type_name": "蜜桃社", "type_id": "miitao"},
            {"type_name": "=== 漫画 ===", "type_id": "ignore"},
            {"type_name": "日本漫画", "type_id": "comic/category/jp"},
            {"type_name": "韩国漫画", "type_id": "comic/category/kr"},
            {"type_name": "=== 小说 ===", "type_id": "ignore"},
            {"type_name": "都市", "type_id": "novel/category/Urban"},
            {"type_name": "乱伦", "type_id": "novel/category/Incestuous"},
            {"type_name": "玄幻", "type_id": "novel/category/Xuanhuan"},
            {"type_name": "武侠", "type_id": "novel/category/Wuxia"}
        ]
        return {'class': [c for c in cats if c['type_id'] != 'ignore']}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg)
        url = f"{self.base_url}/{tid}/page/{pg}"
        return self._get_post_list(url, pg)

    def _get_post_list(self, url, pg):
        resp = self.fetch(url)
        vlist = []
        if resp and resp.status_code == 200:
            resp.encoding = 'utf-8'
            html = resp.text

            list_block = html
            main_block = re.search(r'(?:id="index_ajax_list"|class="site-main")[^>]*>(.*?)<(?:footer|aside)', html, re.S)
            if main_block:
                list_block = main_block.group(1)

            items = re.findall(r'<li[^>]*>(.*?)</li>', list_block, re.S)
            for item in items:
                href_match = re.search(r'href=["\']([^"\']+)["\']', item)
                if not href_match:
                    continue
                href = href_match.group(1)

                if any(x in href for x in ['.css', '.js', 'templates/', 'wp-includes']):
                    continue

                img_match = re.search(r'data-original=["\']([^"\']+)["\']', item)
                if not img_match:
                    img_match = re.search(r'src=["\']([^"\']+)["\']', item)
                pic = img_match.group(1) if img_match else ""

                if not pic:
                    pic = "https://www.74p.net/static/images/cover.png"

                title_match = re.search(r'title=["\']([^"\']+)["\']', item)
                name = title_match.group(1) if title_match else re.sub(r'<[^>]+>', '', item).strip().split('\n')[0]
                if name.startswith('.') or '{' in name or len(name) > 100:
                    continue

                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = self.base_url + href

                vlist.append({
                    'vod_id': href,
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_remarks': '点击查看',
                    'style': {"type": "rect", "ratio": 1.33}
                })

        return {'list': vlist, 'page': pg, 'pagecount': pg + 1 if len(vlist) >= 15 else pg, 'limit': 20, 'total': 9999}

    def searchContent(self, key, quick, pg=1):
        search_path = f"/search/{key}"
        headers = self.headers.copy()
        if "漫画" in key:
            headers['Referer'] = f"{self.base_url}/comic"
        else:
            headers['Referer'] = f"{self.base_url}/novel"
        if int(pg) > 1:
            url = f"{self.base_url}{search_path}/page/{pg}"
        else:
            url = f"{self.base_url}{search_path}"
        return self._get_post_list(url, int(pg))

    # ==========================
    #  详情页 - 直接抓当前页面的所有图片作为选集
    # ==========================
    def detailContent(self, ids):
        url = ids[0]
        
        # 直接抓取当前页面的所有图片
        images = self._scrape_all_images(url)
        
        vod = {
            'vod_id': url,
            'vod_name': '',
            'vod_pic': '',
            'type_name': '漫画',
            'vod_content': '',
            'vod_play_from': '接口源码分享QQ交流群:212706934',
            'vod_play_url': ''
        }
        
        # 获取标题
        resp = self.fetch(url)
        if resp:
            resp.encoding = 'utf-8'
            html = resp.text
            h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html)
            if h1:
                vod['vod_name'] = h1.group(1)
            else:
                vod['vod_name'] = '漫画'
        else:
            vod['vod_name'] = '漫画'
        
        if images:
            # ====== 把每张图片作为一集 ======
            play_items = []
            for idx, img in enumerate(images, 1):
                play_items.append(f"第{idx}页${img}")
            vod['vod_play_url'] = "#".join(play_items)
            vod['vod_pic'] = images[0]
            vod['vod_content'] = f'共 {len(images)} 张图片'
        else:
            # 没有图片，尝试找章节链接
            if resp:
                chapter_links = re.findall(r'<a[^>]+href=["\']([^"\']*/(?:comic|novel)/chapter/[^"\']+)["\'][^>]*>(.*?)</a>', resp.text)
                if chapter_links:
                    play_list = []
                    for href, name in chapter_links:
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            href = self.base_url + href
                        play_list.append(f"{name.strip()}${href}")
                    vod['vod_play_url'] = "#".join(play_list)
                else:
                    vod['vod_play_url'] = f"在线观看${url}"
            else:
                vod['vod_play_url'] = f"在线观看${url}"
        
        return {'list': [vod]}

    # ==========================
    #  播放页
    # ==========================
    def playerContent(self, flag, id, vipFlags):
        # 如果 id 是图片链接，直接播放
        if id.startswith('http') and re.search(r'\.(jpg|jpeg|png|webp|gif|bmp)', id, re.I):
            return {
                "parse": 0,
                "playUrl": "",
                "url": id,
                "header": ""
            }
        
        # 否则尝试抓取图片
        images = self._scrape_all_images(id)
        if images:
            return {
                "parse": 0,
                "playUrl": "",
                "url": images[0],
                "header": ""
            }
        
        return {
            "parse": 0,
            "playUrl": "",
            "url": "",
            "header": "",
            "msg": "无法播放"
        }

    # ==========================
    #  工具：翻页抓取所有图片
    # ==========================
    def _scrape_all_images(self, url):
        images = []
        visited = set()
        current_url = url
        page = 1
        max_pages = 50

        while page <= max_pages:
            if current_url in visited:
                break
            visited.add(current_url)

            resp = self.fetch(current_url)
            if not resp or resp.status_code != 200:
                break
            resp.encoding = 'utf-8'
            html = resp.text

            content_match = re.search(r'(?:id="content"|class="entry-content"|class="single-content")[^>]*>(.*?)<(?:div class="related|footer|section)', html, re.S)
            content_html = content_match.group(1) if content_match else html

            img_matches = re.findall(r'<img[^>]+(?:src|data-original|data-src)=["\']([^"\']+)["\']', content_html)
            for src in img_matches:
                if any(x in src.lower() for x in ['.gif', '.svg', 'logo', 'avatar', 'icon']):
                    continue
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = self.base_url + src
                if src not in images:
                    images.append(src)

            next_url = None
            next_match = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(?:下一页|Next|»)</a>', html, re.I)
            if not next_match:
                next_match = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*next[^"\']*["\']', html, re.I)

            if next_match:
                href = next_match.group(1)
                if href.startswith('//'):
                    next_url = 'https:' + href
                elif href.startswith('/'):
                    next_url = self.base_url + href
                else:
                    next_url = href

            if not next_url:
                break
            current_url = next_url
            page += 1

        return images