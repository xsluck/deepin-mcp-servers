import requests
from readability import Document
from readabilipy import simple_json
import markdownify
import re
headers = {
    "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def get_web_content(url):
    try:
        response = requests.get(
            url, 
            headers=headers,
            timeout=10,
            proxies=None
        )
        try:
            page_raw = bytes(response.text, response.encoding).decode("utf-8")
        except Exception as e:
            response.encoding = response.apparent_encoding  # 自动检测编码
            page_raw = response.text
        content_type = response.headers.get("content-type", "")
        is_page_html = (
                "<html" in page_raw[:100] or "text/html" in content_type or not content_type
        )
        try:
            if is_page_html:
                return extract_main_content(page_raw), response.url
            raise Exception("not a html page.")
        except Exception as e:
            doc = Document(page_raw)
            return doc.summary(), response.url
    except Exception as e:
        return "", ""

def extract_main_content(html):
    ret = simple_json.simple_json_from_html_string(
        html, use_readability=True
    )
    if not ret["content"]:
        return None
    content = markdownify.markdownify(
        ret["content"],
        heading_style=markdownify.ATX,
    )

    # 过滤无效内容
    content = re.sub(r"^[^\S\n]+", "", content)
    content = re.sub(r"\n+", "\n", content)
    content = re.sub(r"^\s*", "", content)
    content = re.sub(r"\s*$", "", content)

    return content