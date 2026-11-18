# -*- coding: utf-8 -*-
#!/usr/bin/python
# 遮天法 · 无限天山 修复版
# 关键修复：分类/播放/搜索 使用 index.php 真实路径

import re, json, html, time
from urllib.parse import quote, urljoin

try:
    from lxml import etree
except ImportError:
    etree = None

try:
    import requests
except ImportError:
    requests = None

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        def init(self, extend=""): pass
        def homeContent(self, filter): pass
        def homeVideoContent(self): pass
        def categoryContent(self, tid, pg, filter, extend): pass
        def detailContent(self, ids): pass
        def playerContent(self, flag, id, vipFlags=None): pass
        def searchContent(self, key, quick, pg="1"): pass
        def isVideoFormat(self, url): pass
        def manualVideoCheck(self): pass
        def localProxy(self, param): pass


def fix_url(url, host):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return urljoin(host, url)
    if url.startswith("http"):
        return url
    return urljoin(host, "/" + url)


def clean_text(text):
    if not text:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", str(text))).strip()


def extract_play(html_text, host):
    patterns = [
        r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
        r'(https?://[^\s"\']+\.mp4[^\s"\']*)',
        r'var\s*now\s*=\s*["\']([^"\']+)["\']',
        r'player_data\s*=\s*(\{.*?\})',
        r'player_aaaa\s*=\s*(\{.*?\})',
        r'url\s*:\s*["\']([^"\']+\.m3u8)["\']',
        r'var\s*playurl\s*=\s*["\']([^"\']+)["\']',
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        r'(https?://[^\s"\']+\.(?:m3u8|mp4|flv))',
    ]
    for pat in patterns:
        m = re.search(pat, html_text, re.DOTALL | re.I)
        if not m:
            continue
        if "player_data" in pat or "player_aaaa" in pat:
            try:
                data = json.loads(m.group(1))
                url = data.get("url") or data.get("url_next") or ""
                if url:
                    return url
            except:
                continue
        if "iframe" in pat:
            iframe = m.group(1)
            if iframe.startswith("//"):
                iframe = "https:" + iframe
            elif iframe.startswith("/"):
                iframe = urljoin(host, iframe)
            return iframe
        return m.group(1)
    return ""


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        # 当前可用域名（可被 init(extend) 覆盖）
        self.host = "https://wxts.wuxiants966.com"
        self.name = "ZheTian_WuXianTianShan"
        self.s = requests.Session() if requests else None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.host + "/",
        }
        self.seen_ids = set()
        if self.s:
            self.s.headers.update(self.headers)
            self.s.verify = False

    def init(self, extend=""):
        if extend and extend.startswith("http"):
            self.host = extend.rstrip("/")
            self.headers["Referer"] = self.host + "/"
            if self.s:
                self.s.headers.update(self.headers)

    def getName(self):
        return self.name

    def isVideoFormat(self, url):
        return any(x in (url or "") for x in [".m3u8", ".mp4", ".flv", ".ts"])

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return [200, "video/MP2T", b"", {}]

    def _fetch(self, url, retry=3):
        if not self.s:
            return ""
        for i in range(retry):
            try:
                r = self.s.get(url, timeout=15, headers=self.headers)
                if r.status_code == 404:
                    return ""
                r.raise_for_status()
                r.encoding = "utf-8"
                return r.text
            except Exception as e:
                if i == retry - 1:
                    print(f"[{self.name}] 请求失败: {url} - {e}")
                time.sleep(1)
        return ""

    def homeContent(self, filter):
        classes = [
            {"type_name": "偷拍自拍", "type_id": "2"},
            {"type_name": "国产精品", "type_id": "3"},
            {"type_name": "伦理三级", "type_id": "4"},
            {"type_name": "主播大秀", "type_id": "5"},
            {"type_name": "网曝黑料", "type_id": "6"},
            {"type_name": "热门头条", "type_id": "7"},
            {"type_name": "抖音视频", "type_id": "8"},
            {"type_name": "素人自拍", "type_id": "9"},
            {"type_name": "刘玥", "type_id": "10"},
            {"type_name": "过膝袜", "type_id": "11"},
            {"type_name": "探花系列", "type_id": "12"},
            {"type_name": "玩物姐姐", "type_id": "13"},
            {"type_name": "cosplay", "type_id": "14"},
            {"type_name": "学生诱惑", "type_id": "15"},
            {"type_name": "台湾粉红兔", "type_id": "16"},
            {"type_name": "口交颜射", "type_id": "17"},
            {"type_name": "女优明星", "type_id": "18"},
            {"type_name": "迷奸强奸", "type_id": "19"},
            {"type_name": "亚洲无码", "type_id": "20"},
            {"type_name": "中文字幕", "type_id": "21"},
            {"type_name": "熟女人妻", "type_id": "22"},
            {"type_name": "亚洲有码", "type_id": "23"},
            {"type_name": "强奸乱伦", "type_id": "24"},
            {"type_name": "制服美腿", "type_id": "25"},
            {"type_name": "丝袜美腿", "type_id": "26"},
            {"type_name": "少女萝莉", "type_id": "27"},
            {"type_name": "卡通动漫", "type_id": "28"},
            {"type_name": "东京热", "type_id": "29"},
            {"type_name": "一本道", "type_id": "30"},
            {"type_name": "素人搭讪", "type_id": "31"},
            {"type_name": "国产传媒", "type_id": "32"},
            {"type_name": "麻豆传媒", "type_id": "33"},
            {"type_name": "果冻传媒", "type_id": "34"},
            {"type_name": "兔子先生", "type_id": "35"},
            {"type_name": "天美传媒", "type_id": "36"},
            {"type_name": "SA国际传媒", "type_id": "37"},
            {"type_name": "性视界", "type_id": "38"},
            {"type_name": "扣扣传媒", "type_id": "39"},
            {"type_name": "精东影业", "type_id": "42"},
            {"type_name": "皇家华人", "type_id": "46"},
            {"type_name": "JVID", "type_id": "47"},
            {"type_name": "SWAG", "type_id": "48"},
            {"type_name": "多人群交", "type_id": "54"},
            {"type_name": "AI换脸", "type_id": "55"},
            {"type_name": "重口色情", "type_id": "56"},
            {"type_name": "同性专区", "type_id": "57"},
            {"type_name": "人妻绿帽", "type_id": "58"},
            {"type_name": "TS人妖", "type_id": "59"},
            {"type_name": "VR视角", "type_id": "60"},
            {"type_name": "欧美精品", "type_id": "65"},
            {"type_name": "韩国主播", "type_id": "66"},
            {"type_name": "极品黑料", "type_id": "67"},
        ]
        return {"class": classes, "filters": {}}

    def homeVideoContent(self):
        return self.categoryContent("2", "1", False, {})

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        try:
            # ★ 关键修复：使用 index.php 真实路径
            if int(pg) <= 1:
                url = f"{self.host}/index.php/vod/type/id/{tid}.html"
            else:
                url = f"{self.host}/index.php/vod/type/id/{tid}/page/{pg}.html"

            html_text = self._fetch(url)
            if not html_text:
                return result

            doc = etree.HTML(html_text) if etree else None
            if not doc:
                return result

            items = doc.xpath('//ul[contains(@class,"thumbnail-group")]//li')
            if not items:
                items = doc.xpath('//a[contains(@href,"/vod/play/id/") and .//img]/..')
            if not items:
                items = doc.xpath('//a[contains(@href,"/vod/play/id/")]')

            self.seen_ids.clear()
            for item in items:
                try:
                    title_nodes = item.xpath('.//h5/a/text() | .//a/@title | .//img/@alt')
                    title = clean_text(title_nodes[0]) if title_nodes else ""

                    href_nodes = item.xpath('.//a[contains(@href,"/vod/play/")]/@href | .//@href')
                    href = href_nodes[0] if href_nodes else ""

                    m = re.search(r'/vod/play/id/(\d+)/', href) or re.search(r'/id/(\d+)', href)
                    vid = m.group(1) if m else ""
                    if not vid or vid in self.seen_ids:
                        continue
                    self.seen_ids.add(vid)

                    pic_nodes = item.xpath('.//img/@src | .//img/@data-src | .//img/@data-original')
                    pic = fix_url(pic_nodes[0], self.host) if pic_nodes else ""

                    remark_nodes = item.xpath('.//p/text()')
                    remark = clean_text(remark_nodes[0]) if remark_nodes else ""

                    result["list"].append({
                        "vod_id": vid,
                        "vod_name": title or vid,
                        "vod_pic": pic,
                        "vod_remarks": remark
                    })
                except Exception as e:
                    print(f"[{self.name}] 单条解析失败: {e}")
                    continue

            # 分页：页面有 /page/1703 这类链接
            pc = re.search(r'/page/(\d+)', html_text)
            if pc:
                # 取最大页码
                pages = [int(x) for x in re.findall(r'/page/(\d+)', html_text)]
                if pages:
                    result["pagecount"] = max(pages)
            elif result["list"]:
                result["pagecount"] = int(pg) + 1

            print(f"[{self.name}] 分类 {tid} 第{pg}页 匹配到 {len(result['list'])} 条")
            return result
        except Exception as e:
            print(f"[{self.name}] 分类爬取失败: {e}")
            return result

    def detailContent(self, ids):
        result = {"list": []}
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            # ★ 播放页真实路径
            urls = [
                f"{self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html",
                f"{self.host}/vod/play/id/{vid}/sid/1/nid/1/",
            ]
            html_text = ""
            for u in urls:
                html_text = self._fetch(u)
                if html_text and len(html_text) > 500:
                    break
            if not html_text:
                return result

            doc = etree.HTML(html_text) if etree else None
            title = vid
            pic = ""
            if doc:
                t = doc.xpath('//h1/text() | //h2/text() | //title/text()')
                if t:
                    title = clean_text(t[0]).split("_")[0].split("-")[0]
                p = doc.xpath('//img[contains(@class,"poster") or contains(@class,"cover")]/@src | //meta[@property="og:image"]/@content')
                if p:
                    pic = fix_url(p[0], self.host)

            play_url = extract_play(html_text, self.host)
            if play_url:
                play_str = f"正片${play_url}"
            else:
                play_str = f"正片${self.host}/index.php/vod/play/id/{vid}/sid/1/nid/1.html"

            result["list"].append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": pic,
                "vod_play_from": "默认线路",
                "vod_play_url": play_str
            })
            return result
        except Exception as e:
            print(f"[{self.name}] 详情解析失败: {e}")
            return result

    def playerContent(self, flag, id, vipFlags=None):
        result = {"parse": 0, "playUrl": "", "url": "", "header": ""}
        try:
            if self.isVideoFormat(id):
                result["url"] = id
                result["header"] = json.dumps({
                    "Referer": self.host + "/",
                    "User-Agent": self.headers["User-Agent"]
                })
                return result

            html_text = self._fetch(id) if id.startswith("http") else ""
            if not html_text and not id.startswith("http"):
                html_text = self._fetch(f"{self.host}/index.php/vod/play/id/{id}/sid/1/nid/1.html")

            if html_text:
                play_url = extract_play(html_text, self.host)
                if play_url:
                    result["url"] = play_url
                    result["header"] = json.dumps({
                        "Referer": self.host + "/",
                        "User-Agent": self.headers["User-Agent"]
                    })
                    return result

            result["url"] = id
            result["parse"] = 1
            return result
        except Exception as e:
            print(f"[{self.name}] 播放解析失败: {e}")
            return {"parse": 0, "playUrl": "", "url": id, "header": ""}

    def searchContent(self, key, quick, pg="1"):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        try:
            # ★ 搜索真实路径
            url = f"{self.host}/index.php/vod/search.html?wd={quote(key)}"
            if int(pg) > 1:
                url = f"{self.host}/index.php/vod/search/wd/{quote(key)}/page/{pg}.html"

            html_text = self._fetch(url)
            if not html_text:
                return result

            doc = etree.HTML(html_text) if etree else None
            if not doc:
                return result

            items = doc.xpath('//ul[contains(@class,"thumbnail-group")]//li')
            if not items:
                items = doc.xpath('//a[contains(@href,"/vod/play/id/") and .//img]/..')

            self.seen_ids.clear()
            for item in items:
                try:
                    title_nodes = item.xpath('.//h5/a/text() | .//a/@title | .//img/@alt')
                    title = clean_text(title_nodes[0]) if title_nodes else ""
                    href_nodes = item.xpath('.//a[contains(@href,"/vod/play/")]/@href | .//@href')
                    href = href_nodes[0] if href_nodes else ""
                    m = re.search(r'/vod/play/id/(\d+)/', href)
                    vid = m.group(1) if m else ""
                    if not vid or vid in self.seen_ids:
                        continue
                    self.seen_ids.add(vid)
                    pic_nodes = item.xpath('.//img/@src | .//img/@data-src | .//img/@data-original')
                    pic = fix_url(pic_nodes[0], self.host) if pic_nodes else ""
                    result["list"].append({
                        "vod_id": vid,
                        "vod_name": title or vid,
                        "vod_pic": pic
                    })
                except:
                    continue
            return result
        except Exception as e:
            print(f"[{self.name}] 搜索失败: {e}")
            return result