"""
Zernio posting and Bright Data post-generation helpers.

CLI examples:
  source "ztmp/env_gitignore.sh"
  python uinterface/zernio/run.py create_post --prompt="Write a post about APIs"
  python uinterface/zernio/run.py search_googleai \
    --query="Best API design practices" --dirout="ztmp/out.txt"
  python uinterface/zernio/run.py send_post --subreddit="mysub" \
    --title="My title" --post_markdown="My post"
"""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os,sys
import fire

import json
import random
import uuid
from datetime import datetime, timezone

import requests

def log_info(*s):
  print(*s)

log_error = log_info
log_trace = log_info
log_warning = log_info



ZERNIO_URL = "https://zernio.com/api/v1"
BRIGHT_DATA_URL = "https://api.brightdata.com"
BRIGHT_DATA_CHATGPT_DATASET = "gd_m7aof0k82r803d5bjm"
BRIGHT_DATA_GOOGLEAI_DATASET = "gd_mcswdt6z2elth3zqr2"

query_list = [
    """ Provide long summary of 4 pages  for V-Modal SDK Video Search for mobile, Flutter and Android 
    using all the links below: 
    
      - "https://github.com/orgs/v-modal/repositories"  
      - "https://devhunt.org/tool/vmodal-visual-video-search-sdk?banner=true"
      - "https://dev.to/metaexpert/simple-sdk-to-enable-search-4gkh"

- "https://github.com/v-modal/vmodal_sdk_flutter/issues/13"
- "https://www.linkedin.com/feed/update/urn:li:activity:7473925833758232576"
- "https://www.linkedin.com/posts/v-modal_search-through-the-inifinite-activity-7465309888324345858-VxWZ?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_search-from-anywhere-activity-7465603389905637376-6Sav?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7473925833758232576-xh2A?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7468546583274450944-vbq4?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7467217731868848128-3kjs?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7465819290479345665--lIg?utm_source=share"
- "https://dev.to/nauman_khalid_795e95b4501/exploring-the-vmodal-flutter-sdk-a-modular-sdk-for-ai-powered-video-search-plc"
- "https://www.reddit.com/user/CalligrapherFalse609/comments/1v65m3z/vmodal_flutter_sdk_for_integrating_with_vmodal_ai/?share_id=6EPUh-g56W06Uvx9pybyo"

https://www.reddit.com/r/androiddev/comments/1ul9zv5/comment/oz7laj7/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
https://www.reddit.com/r/aitubers/comments/1qn8lti/comment/ozmr1ji/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
https://www.reddit.com/r/android_search_tools/comments/1v60f64/tool_to_build_video_search_on_mobile_app/
https://www.reddit.com/r/androiddev/s/GQt9QaCQyQ
https://www.reddit.com/r/android_search_tools/comments/1v1e05w/recent_trend_in_search_tools_for_android_platform/


    """,
    """
      Explain how to integrate V-Modal SDK Search into an Android and Flutter mobile application:
      
      
      -  "https://github.com/orgs/v-modal/repositories"       
      -  "https://github.com/orgs/v-modal/repositories"  
      -  "https://devhunt.org/tool/vmodal-visual-video-search-sdk?banner=true"
      -  "https://dev.to/metaexpert/simple-sdk-to-enable-search-4gkh"

- "https://github.com/v-modal/vmodal_sdk_flutter/issues/13"
- "https://www.linkedin.com/feed/update/urn:li:activity:7473925833758232576"
- "https://www.linkedin.com/posts/v-modal_search-through-the-inifinite-activity-7465309888324345858-VxWZ?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_search-from-anywhere-activity-7465603389905637376-6Sav?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7473925833758232576-xh2A?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7468546583274450944-vbq4?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7467217731868848128-3kjs?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7465819290479345665--lIg?utm_source=share"
- "https://dev.to/nauman_khalid_795e95b4501/exploring-the-vmodal-flutter-sdk-a-modular-sdk-for-ai-powered-video-search-plc"
- "https://www.reddit.com/user/CalligrapherFalse609/comments/1v65m3z/vmodal_flutter_sdk_for_integrating_with_vmodal_ai/?share_id=6EPUh-g56W06Uvx9pybyo"


- https://www.reddit.com/r/androiddev/comments/1ul9zv5/comment/oz7laj7/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/aitubers/comments/1qn8lti/comment/ozmr1ji/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/android_search_tools/comments/1v60f64/tool_to_build_video_search_on_mobile_app/
- https://www.reddit.com/r/androiddev/s/GQt9QaCQyQ
- https://www.reddit.com/r/android_search_tools/comments/1v1e05w/recent_trend_in_search_tools_for_android_platform/

      
      """,

  
  """ Describe with summary of 3 pages V-Modal semantic video search SDK features for mobile developers: 
  
      - "https://github.com/orgs/v-modal/repositories"  
      - "https://devhunt.org/tool/vmodal-visual-video-search-sdk?banner=true"
      - "https://dev.to/metaexpert/simple-sdk-to-enable-search-4gkh"
- "https://github.com/v-modal/vmodal_sdk_flutter/issues/13"
- "https://www.linkedin.com/feed/update/urn:li:activity:7473925833758232576"
- "https://www.linkedin.com/posts/v-modal_search-through-the-inifinite-activity-7465309888324345858-VxWZ?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_search-from-anywhere-activity-7465603389905637376-6Sav?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7473925833758232576-xh2A?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7468546583274450944-vbq4?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7467217731868848128-3kjs?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7465819290479345665--lIg?utm_source=share"
- "https://dev.to/nauman_khalid_795e95b4501/exploring-the-vmodal-flutter-sdk-a-modular-sdk-for-ai-powered-video-search-plc"
- "https://www.reddit.com/user/CalligrapherFalse609/comments/1v65m3z/vmodal_flutter_sdk_for_integrating_with_vmodal_ai/?share_id=6EPUh-g56W06Uvx9pybyo"


- https://www.reddit.com/r/androiddev/comments/1ul9zv5/comment/oz7laj7/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/aitubers/comments/1qn8lti/comment/ozmr1ji/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/android_search_tools/comments/1v60f64/tool_to_build_video_search_on_mobile_app/
- https://www.reddit.com/r/androiddev/s/GQt9QaCQyQ
- https://www.reddit.com/r/android_search_tools/comments/1v1e05w/recent_trend_in_search_tools_for_android_platform/

  
  """,

  
  """ Generate a very deailed Comparison of 2 pages
  between V-Modal SDK Search for Android and Flutter: 
  
  
      - "https://github.com/orgs/v-modal/repositories"
      - "https://github.com/orgs/v-modal/repositories"  
      - "https://devhunt.org/tool/vmodal-visual-video-search-sdk?banner=true"
      - "https://dev.to/metaexpert/simple-sdk-to-enable-search-4gkh"
- "https://github.com/v-modal/vmodal_sdk_flutter/issues/13"
- "https://www.linkedin.com/feed/update/urn:li:activity:7473925833758232576"
- "https://www.linkedin.com/posts/v-modal_search-through-the-inifinite-activity-7465309888324345858-VxWZ?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_search-from-anywhere-activity-7465603389905637376-6Sav?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7473925833758232576-xh2A?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7468546583274450944-vbq4?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7467217731868848128-3kjs?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7465819290479345665--lIg?utm_source=share"
- "https://dev.to/nauman_khalid_795e95b4501/exploring-the-vmodal-flutter-sdk-a-modular-sdk-for-ai-powered-video-search-plc"
- "https://www.reddit.com/user/CalligrapherFalse609/comments/1v65m3z/vmodal_flutter_sdk_for_integrating_with_vmodal_ai/?share_id=6EPUh-g56W06Uvx9pybyo"


- https://www.reddit.com/r/androiddev/comments/1ul9zv5/comment/oz7laj7/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/aitubers/comments/1qn8lti/comment/ozmr1ji/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/android_search_tools/comments/1v60f64/tool_to_build_video_search_on_mobile_app/
- https://www.reddit.com/r/androiddev/s/GQt9QaCQyQ
- https://www.reddit.com/r/android_search_tools/comments/1v1e05w/recent_trend_in_search_tools_for_android_platform/



  
  """,
  """ Deep summarize with extra-details
   V-Modal SDK mobile search API documentation and examples below: 
  
      -  https://github.com/orgs/v-modal/repositories
      - "https://github.com/orgs/v-modal/repositories"  
      - "https://devhunt.org/tool/vmodal-visual-video-search-sdk?banner=true"
      - "https://dev.to/metaexpert/simple-sdk-to-enable-search-4gkh"

- "https://github.com/v-modal/vmodal_sdk_flutter/issues/13"
- "https://www.linkedin.com/feed/update/urn:li:activity:7473925833758232576"
- "https://www.linkedin.com/posts/v-modal_search-through-the-inifinite-activity-7465309888324345858-VxWZ?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_search-from-anywhere-activity-7465603389905637376-6Sav?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7473925833758232576-xh2A?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_mobiledev-videosearch-sdk-activity-7468546583274450944-vbq4?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7467217731868848128-3kjs?utm_source=share"
- "https://www.linkedin.com/posts/v-modal_aiabrmobile-android-ios-activity-7465819290479345665--lIg?utm_source=share"
- "https://dev.to/nauman_khalid_795e95b4501/exploring-the-vmodal-flutter-sdk-a-modular-sdk-for-ai-powered-video-search-plc"
- "https://www.reddit.com/user/CalligrapherFalse609/comments/1v65m3z/vmodal_flutter_sdk_for_integrating_with_vmodal_ai/?share_id=6EPUh-g56W06Uvx9pybyo"


- https://www.reddit.com/r/androiddev/comments/1ul9zv5/comment/oz7laj7/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/aitubers/comments/1qn8lti/comment/ozmr1ji/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- https://www.reddit.com/r/android_search_tools/comments/1v60f64/tool_to_build_video_search_on_mobile_app/
- https://www.reddit.com/r/androiddev/s/GQt9QaCQyQ
- https://www.reddit.com/r/android_search_tools/comments/1v1e05w/recent_trend_in_search_tools_for_android_platform/
- https://github.com/v-modal/vmodal_sdk_android

  
  """,



]


def os_api_key(name: str) -> str:
    """Read a required API key from the sourced shell environment."""
    key = os.environ.get(name, "").strip()
    if not key:
        raise RuntimeError(
            f"{name} is missing. Run: source \"ztmp/env_gitignore.sh\""
        )
    return key


def api_json(
    method: str,
    url: str,
    api_key: str,
    body: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
    request_id: str = "",
) -> Any:
    """Send one authenticated JSON request and return its decoded body."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if request_id:
        headers["x-request-id"] = request_id

    res = requests.request(
        method,
        url,
        headers=headers,
        json=body,
        params=params,
        timeout=timeout,
    )
    if not res.ok:
        msg = f"{method} {url} failed ({res.status_code}): {res.text[:1500]}"
        log_error(msg)
        raise requests.HTTPError(msg, response=res)
    return res.json()


def zernio_account_id(target: str, account_id: str = "", timeout: int = 30) -> str:
    """Return the requested account ID or resolve one connected target account."""
    if account_id:
        return account_id

    data = api_json(
        "GET",
        f"{ZERNIO_URL}/accounts",
        os_api_key("ZERNIO_API_KEY"),
        params={"platform": target, "status": "connected"},
        timeout=timeout,
    )
    accounts = [
        x for x in data.get("accounts", [])
        if x.get("platform") == target and x.get("isActive", True)
    ]
    if len(accounts) != 1:
        ids = [x.get("_id") or x.get("id") for x in accounts]
        raise RuntimeError(
            f"Expected one connected {target} account, found {len(accounts)}: {ids}. "
            "Pass --account_id explicitly."
        )
    return accounts[0].get("_id") or accounts[0]["id"]


def send_post(
    target: str = "reddit",
    subreddit: str = "mysub",
    post_markdown: str = "markdowntext",
    title: str = "title",
    account_id: str = "",
    publish_now: bool = True,
    scheduled_for: str = "",
    timezone: str = "UTC",
    media_items: Optional[List[Dict[str, Any]]] = None,
    flair_id: str = "",
    url: str = "",
    custom_data: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Any:
    """Publish or schedule a post through Zernio."""
    target = target.strip().lower()
    if not target:
        raise ValueError("target is required")
    if not post_markdown.strip() and not media_items:
        raise ValueError("post_markdown or media_items is required")

    platform_data = dict(custom_data or {})
    if target == "reddit":
        subreddit = subreddit.strip().removeprefix("r/")
        if not subreddit:
            raise ValueError("subreddit is required for Reddit")
        platform_data["subreddit"] = subreddit
        platform_data["title"] = title
        if flair_id:
            platform_data["flairId"] = flair_id
        if url:
            platform_data["url"] = url
    elif subreddit and subreddit != "mysub":
        log_warning("subreddit is ignored when target is not reddit")

    platform = {
        "platform": target,
        "accountId": zernio_account_id(target, account_id, timeout=timeout),
    }
    if platform_data:
        platform["platformSpecificData"] = platform_data

    body: Dict[str, Any] = {
        "title": title,
        "content": post_markdown,
        "platforms": [platform],
        "timezone": timezone,
    }
    if media_items:
        body["mediaItems"] = media_items
    if scheduled_for:
        body["scheduledFor"] = scheduled_for
    else:
        body["publishNow"] = publish_now

    log_info(f"Sending {target} post through Zernio")
    return api_json(
        "POST",
        f"{ZERNIO_URL}/posts",
        os_api_key("ZERNIO_API_KEY"),
        body=body,
        timeout=timeout,
        request_id=str(uuid.uuid4()),
    )


def search_googleai(
    query: str = "",
    mode: str = "bright data",
    hl: str = "en",
    country: str = "",
    dirout: str = "ztmp/out.txt",
    timeout: int = 180,
) -> Any:
    """Search Google AI Mode through Bright Data and save the full response."""
    if mode.strip().lower().replace("_", " ") != "bright data":
        raise ValueError("Only mode='bright data' is supported")
    if not query.strip():
        raise ValueError("query is required")

    params = {
        "dataset_id": BRIGHT_DATA_GOOGLEAI_DATASET,
        "notify": "false",
        "include_errors": "true",
    }
    body = {
        "input": [{
            "url": "https://google.com/aimode",
            "prompt": query,
            "hl": hl,
            "country": country,
        }],
        "limit_per_input": None,
    }
    log_info("Searching Google AI Mode through Bright Data")
    data = api_json(
        "POST",
        f"{BRIGHT_DATA_URL}/datasets/v3/scrape",
        os_api_key("BRIGHT_DATA_API_KEY"),
        body=body,
        params=params,
        timeout=timeout,
    )
    print(data)
    if dirout:
        os.makedirs(os.path.dirname(dirout) or ".", exist_ok=True)
        with open(dirout, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        log_info(f"Google AI response saved to {dirout}")
    return data


def search_googleai_v1(
    dirout: str = "zout/{ymd}/googleai_resp_{ymd_hms}.json",
    hl: str = "en",
    country: str = "",
    timeout: int = 180,
) -> Dict[str, str]:
    """Pick one query randomly and run Bright Data Google AI Mode."""
    now = datetime.now(timezone.utc)
    dirout = dirout.format(
        ymd=now.strftime("%Y%m%d"),
        ymd_hms=now.strftime("%Y%m%d_%H%M%S"),
    )
    query = random.choice(query_list)
    log_info(f"Selected Google AI query: {query}")
    search_googleai(
        query=query,
        hl=hl,
        country=country,
        dirout=dirout,
        timeout=timeout,
    )
    return {"query": query, "dirout": dirout}


def create_post(
    prompt: str = "my prompt",
    dir_asset: str = "docs/post_asset/",
    country: str = "us",
    web_search: bool = True,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Create a Markdown post with Bright Data and save its response assets."""
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("prompt is required")
    post_prompt = (
        "Create a ready-to-publish social media post in Markdown. "
        "Return only the post text.\n\nUser brief:\n"
        f"{prompt}"
    )
    if len(post_prompt) > 4096:
        raise ValueError("prompt is too long for the Bright Data API")

    params = {
        "dataset_id": BRIGHT_DATA_CHATGPT_DATASET,
        "include_errors": "true",
    }
    body = {
        "input": [{
            "url": "https://chatgpt.com/",
            "prompt": post_prompt,
            "country": country.lower(),
            "web_search": web_search,
        }]
    }
    log_info("Creating post through Bright Data")
    data = api_json(
        "POST",
        f"{BRIGHT_DATA_URL}/datasets/v3/scrape",
        os_api_key("BRIGHT_DATA_API_KEY"),
        body=body,
        params=params,
        timeout=timeout,
    )

    item = data[0] if isinstance(data, list) and data else {}
    if not isinstance(item, dict):
        raise RuntimeError("Bright Data returned an unexpected response")
    if item.get("error"):
        raise RuntimeError(f"Bright Data failed: {item['error']}")

    md_text = (
        item.get("answer_text_markdown")
        or item.get("additional_answer_text")
        or item.get("answer_text")
        or ""
    ).strip()
    if not md_text:
        raise RuntimeError("Bright Data response did not contain post text")

    print(md_text)
    os.makedirs(dir_asset, exist_ok=True)
    post_path = os.path.join(dir_asset, "post.md")
    result_path = os.path.join(dir_asset, "result.json")
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(md_text + "\n")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    log_info(f"Post saved to {post_path}")
    return {
        "post_markdown": md_text,
        "post_path": post_path,
        "result_path": result_path,
        "result": item,
    }


if __name__ == "__main__":
    fire.Fire({
        "send_post": send_post,
        "create_post": create_post,
        "search_googleai": search_googleai,
        "search_googleai_v1": search_googleai_v1,
    })
