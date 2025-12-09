import os
import re
import json
import datetime
from pathlib import Path

# 配置
TEMPLATE_FILE = 'template.html'
ARTICLES_DIR = 'article'
INDEX_JSON = 'articles.json'


def parse_srt(srt_content):
    """解析 SRT 文件内容为列表 [{'start':秒, 'end':秒, 'text': '内容'}]"""
    pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:(?!\n\d+\n).)*)',
                         re.DOTALL)
    matches = pattern.findall(srt_content)

    subtitles = []
    for match in matches:
        start_str, end_str, text = match[1], match[2], match[3]

        # 转换时间为秒
        def time_to_seconds(t_str):
            h, m, s_ms = t_str.split(':')
            s, ms = s_ms.split(',')
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

        # 清理文本 (去除多余换行和 source 标签)
        clean_text = text.strip().replace('\n', '<br>')
        # 可选：如果你想去除 这种标签，可以使用下面的正则
        # clean_text = re.sub(r'\', '', clean_text)

        subtitles.append({
            'start': time_to_seconds(start_str),
            'end': time_to_seconds(end_str),
            'text': clean_text
        })
    return subtitles


def generate_article(video_url, srt_path, title, date_str):
    # 1. 提取 Video ID
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', video_url)
    if not video_id_match:
        print("错误：无法解析 YouTube URL")
        return
    video_id = video_id_match.group(1)

    # 2. 读取 SRT
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    subtitles = parse_srt(srt_content)

    # 3. 准备文件路径 (article/202312/slug.html)
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    folder_name = date_obj.strftime("%Y%m")
    file_slug = title.lower().replace(' ', '-').replace('.', '') + ".html"

    output_dir = os.path.join(ARTICLES_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, file_slug)

    # 4. 读取模板并替换内容
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()

    # 将 Python 对象转为 JSON 字符串插入 JS
    html_content = template.replace('{{VIDEO_ID}}', video_id)
    html_content = template.replace('{{TITLE}}', title)
    html_content = template.replace('{{DATE}}', date_str)
    html_content = html_content.replace('{{SUBTITLES_JSON}}', json.dumps(subtitles, ensure_ascii=False))
    html_content = html_content.replace('{{VIDEO_ID}}', video_id)  # 再次确保替换

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"成功生成文章: {output_path}")

    # 5. 更新索引 JSON (用于主页自动刷新)
    update_index(title, date_str, f"{folder_name}/{file_slug}", video_id)


def update_index(title, date, path, video_id):
    entries = []
    if os.path.exists(INDEX_JSON):
        with open(INDEX_JSON, 'r', encoding='utf-8') as f:
            try:
                entries = json.load(f)
            except:
                pass

    # 添加新条目到顶部
    new_entry = {
        'title': title,
        'date': date,
        'path': f"article/{path}",
        'video_id': video_id,
        'created_at': datetime.datetime.now().isoformat()
    }

    # 简单的去重逻辑（如果路径一样则更新）
    entries = [e for e in entries if e['path'] != new_entry['path']]
    entries.insert(0, new_entry)

    with open(INDEX_JSON, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("索引已更新。")


if __name__ == "__main__":
    # 使用交互式输入
    u_url = input("请输入 YouTube 视频网址: ").strip()
    u_srt = input("请输入 SRT 字幕文件路径 (例如 sub.srt): ").strip()
    u_title = input("请输入文章标题 (例如 NBC News Dec 8): ").strip()
    u_date = input("请输入日期 (YYYY-MM-DD, 留空则为今天): ").strip()

    if not u_date:
        u_date = datetime.datetime.now().strftime("%Y-%m-%d")

    generate_article(u_url, u_srt, u_title, u_date)