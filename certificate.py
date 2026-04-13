"""电子证书生成。"""

from __future__ import annotations

from typing import List


def generate_certificate_svg(
    *,
    user_name: str,
    activity_name: str,
    rank_title: str,
    score: int,
    medals: List[str],
) -> str:
    """生成可下载的 SVG 证书。"""
    medal_text = "、".join(medals[:4]) if medals else "长征精神学习纪念"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f9ecd2"/>
      <stop offset="100%" stop-color="#f2d2a0"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="900" rx="24" fill="url(#bg)" stroke="#8b3c2e" stroke-width="16"/>
  <rect x="48" y="48" width="1104" height="804" rx="18" fill="none" stroke="#b57b3d" stroke-width="4"/>
  <text x="600" y="140" text-anchor="middle" font-size="40" font-family="Microsoft YaHei" fill="#7b1f15">电子结业证书</text>
  <text x="600" y="230" text-anchor="middle" font-size="28" font-family="Microsoft YaHei" fill="#4b2119">《长征精神·沉浸式云端答题互动平台》</text>
  <text x="600" y="330" text-anchor="middle" font-size="54" font-family="Microsoft YaHei" font-weight="700" fill="#4b2119">{user_name}</text>
  <text x="600" y="410" text-anchor="middle" font-size="28" font-family="Microsoft YaHei" fill="#4b2119">已完成“{activity_name}”学习与互动答题任务</text>
  <text x="600" y="490" text-anchor="middle" font-size="26" font-family="Microsoft YaHei" fill="#6a3d1f">当前军衔：{rank_title}</text>
  <text x="600" y="545" text-anchor="middle" font-size="26" font-family="Microsoft YaHei" fill="#6a3d1f">红星积分：{score}</text>
  <text x="600" y="600" text-anchor="middle" font-size="24" font-family="Microsoft YaHei" fill="#6a3d1f">获得勋章：{medal_text}</text>
  <text x="600" y="720" text-anchor="middle" font-size="26" font-family="Microsoft YaHei" fill="#7b1f15">重走长征路，赓续长征魂</text>
  <text x="920" y="810" text-anchor="middle" font-size="22" font-family="Microsoft YaHei" fill="#6a3d1f">平台自动生成</text>
</svg>
""".strip()

