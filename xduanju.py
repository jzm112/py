# coding=utf-8
"""
目标站: X短剧网
首页: https://xduanju.net
"""
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
import sys
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        self.host = "https://xduanju.net"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Referer": self.host
        }
        # (显示名, 分类标识)；tid 直接用中文标签，运行时再 urlencode
        self.classes = [
            ("全部", "all"),
            ("都市", "都市"), ("现代", "现代"), ("高颜值", "高颜值"),
            ("大男主", "大男主"), ("熟女", "熟女"), ("后宫", "后宫"),
            ("古风", "古风"), ("剧情", "剧情"), ("校园", "校园"),
            ("奇幻", "奇幻"), ("大女主", "大女主"), ("职场", "职场"),
            ("逆袭", "逆袭"), ("甜宠", "甜宠"), ("系统", "系统"),
            ("脑洞", "脑洞"), ("穿越", "穿越"), ("乡村", "乡村"),
            ("虐恋", "虐恋"), ("玄幻", "玄幻"), ("禁忌", "禁忌"),
            ("仙侠", "仙侠"), ("同学", "同学"), ("超能力", "超能力"),
        ]

    def _parse_cards(self, soup):
        """列表页统一解析 a.drama-card 卡片。"""
        videos = []
        for a in soup.select('a.drama-card'):
            try:
                href = a.get('href', '')
                if not href:
                    continue
                h3 = a.select_one('.card-copy h3')
                vod_name = h3.text.strip() if h3 else a.get('title', '').strip()
                if not vod_name:
                    continue
                img = a.select_one('.poster img')
                pic = img.get('src', '') if img else ''
                videos.append({
                    "vod_id": href,
                    "vod_name": vod_name,
                    "vod_pic": urllib.parse.urljoin(self.host, pic) if pic else ""
                })
            except Exception:
                continue
        return videos

    def homeContent(self, filter):
        result = {"class": [], "filters": {}}
        try:
            result["class"] = [{"type_name": n, "type_id": t} for n, t in self.classes]
            print(f"[homeContent] 返回分类数量: {len(self.classes)}")
        except Exception as e:
            print(f"[homeContent] 异常: {e}")
        return result

    def categoryContent(self, tid, pg, filter, extend):
        try:
            pg = int(pg) if pg else 1
            if not tid or tid == "all":
                base = f"{self.host}/explore"
            else:
                base = f"{self.host}/explore?tag={urllib.parse.quote(tid)}"
            sep = "&" if "?" in base else "?"
            url = base if pg <= 1 else f"{base}{sep}page={pg}"
            res = self.fetch(url, headers=self.headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_cards(soup)
            pagecount = 1
            pager = soup.select_one('.pager')
            if pager:
                m = re.search(r'(\d+)\s*/\s*(\d+)', pager.text)
                if m:
                    pagecount = int(m.group(2))
            print(f"[categoryContent] 分类 {tid} 第{pg}页 匹配 {len(videos)} 条")
            return {
                "list": videos,
                "page": pg,
                "pagecount": pagecount,
                "limit": len(videos),
                "total": len(videos) * pagecount if pagecount else len(videos)
            }
        except Exception as e:
            print(f"[categoryContent] 异常: {e}")
            return {"list": [], "page": 1, "pagecount": 0, "limit": 0, "total": 0}

    def detailContent(self, ids):
        try:
            vod_id = ids[0] if isinstance(ids, list) else ids.split(",")[0]
            url = urllib.parse.urljoin(self.host, vod_id) if vod_id.startswith("/") else vod_id
            res = self.fetch(url, headers=self.headers)
            soup = BeautifulSoup(res.text, 'html.parser')

            title_el = soup.select_one('h1.watch-title')
            vod_name = title_el.text.strip() if title_el else ""
            if not vod_name:
                og = soup.select_one('meta[property="og:title"]')
                vod_name = og.get('content', '').strip() if og else ""

            og_img = soup.select_one('meta[property="og:image"]')
            vod_pic = og_img.get('content', '') if og_img else ""

            # 播放地址统一从 #player-data 的 JSON 里取：[{"seq":"1","src":"...m3u8"}]
            ep_list = []
            pd = soup.select_one('#player-data')
            if pd and pd.string:
                try:
                    data = json.loads(pd.string)
                    for ep in data:
                        seq = ep.get('seq', '')
                        src = ep.get('src', '')
                        if src:
                            ep_list.append(f"第{seq}集${src}")
                except Exception:
                    ep_list = []

            play_from = "X短剧" if ep_list else ""
            play_url = "#".join(ep_list)

            vod = {
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": urllib.parse.urljoin(self.host, vod_pic) if vod_pic else "",
                "vod_play_from": play_from,
                "vod_play_url": play_url
            }
            print(f"[detailContent] {vod_name} 集数:{len(ep_list)}")
            return {"list": [vod]}
        except Exception as e:
            print(f"[detailContent] 异常: {e}")
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        try:
            pg = int(pg) if pg else 1
            url = f"{self.host}/search?q={urllib.parse.quote(key)}"
            res = self.fetch(url, headers=self.headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            videos = self._parse_cards(soup)
            print(f"[searchContent] 搜索 {key} 结果 {len(videos)} 条")
            return {
                "list": videos,
                "page": pg,
                "pagecount": 1,
                "limit": len(videos),
                "total": len(videos)
            }
        except Exception as e:
            print(f"[searchContent] 异常: {e}")
            return {"list": [], "page": 1, "pagecount": 0, "limit": 0, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        try:
            header = json.dumps(self.headers)
            # 详情页里已经直接把 m3u8 塞进播放列表，这里原样透传即可
            if ".m3u8" in id or ".mp4" in id:
                return {"parse": 0, "playUrl": "", "url": id, "header": header}
            # 兼容：若传入的是详情页路径，再取第一集
            if id.startswith("/"):
                url = urllib.parse.urljoin(self.host, id)
                res = self.fetch(url, headers=self.headers)
                soup = BeautifulSoup(res.text, 'html.parser')
                pd = soup.select_one('#player-data')
                if pd and pd.string:
                    data = json.loads(pd.string)
                    if data and data[0].get('src'):
                        play_url = data[0]['src']
                        print(f"[playerContent] 播放: {flag} -> {play_url[:50]}...")
                        return {"parse": 0, "playUrl": "", "url": play_url, "header": header}
            print(f"[playerContent] 播放: {flag} 未解析到链接")
            return {"parse": 0, "playUrl": "", "url": "", "header": ""}
        except Exception as e:
            print(f"[playerContent] 异常: {e}")
            return {"parse": 0, "playUrl": "", "url": "", "header": ""}
