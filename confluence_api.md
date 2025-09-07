Got it ✅
I’ll do this in **two parts**:

1. **Fix + clean** your three files (`common.py`, `rest_client.py`, `confluence.py`) so they actually run.
2. Provide a **ready-to-use `extract_urls.py`** script that uses keywords to fetch & list Confluence URLs.

---

## 1. Fixed & Cleaned Files

### `common.py`

```python
import os
from hsbcnet.http import RestClient


class Sensitive:
    def __init__(self, credentials=tuple(), client=None):
        self.credentials = credentials if isinstance(credentials, tuple) else tuple(credentials)
        if client is None:
            self.client = RestClient(credentials=self.credentials)
        else:
            self.client = client

    def export_page(self, url, local_file):
        dirpath = Sensitive.get_dir(local_file)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        self.client.download_small_file(url, local_file)

    @staticmethod
    def get_dir(local_file):
        dirpath = os.path.dirname(local_file)
        if not dirpath.strip():
            return "."
        return dirpath
```

---

### `rest_client.py`

```python
import os
import requests
from urllib.parse import urlparse
from requests_toolbelt.multipart.encoder import MultipartEncoder


class RestClient:
    def __init__(self, credentials=tuple(), request_body=None, content_type="application/json",
                 proxies=None, additional_headers=None, disable_ssl_check=False,
                 response_callback=None, cert_file=None, cookies=None,
                 raise_for_status=True):
        self.credentials = credentials
        self.request_body = request_body
        self.content_type = content_type
        self.proxies = proxies
        self.additional_headers = additional_headers or {}
        self.disable_ssl_check = disable_ssl_check
        self.cookies = cookies or {}
        self.raise_for_status = raise_for_status
        self.response_callback = response_callback or RestClient._get_default_response_callback()
        self.cert_file = cert_file

    @staticmethod
    def _get_default_response_callback():
        def fn(r):
            if "application/json" in r.headers.get("Content-Type", "").lower():
                return r.json()
            return r.content.decode("utf8")
        return fn

    def delete(self, url):
        return self._invoke("delete", url)

    def post(self, url, after_request=None):
        return self._invoke("post", url, after_request)

    def put(self, url):
        return self._invoke("put", url)

    def patch(self, url):
        return self._invoke("patch", url)

    def get(self, url, after_request=None):
        return self._invoke("get", url, after_request)

    def download_file(self, url, local_file):
        def post_request(r, session=None):
            with open(local_file, "wb") as f:
                for chunk in r.iter_content(4096):
                    f.write(chunk)
        self.get(url, post_request)

    def download_small_file(self, url, local_file):
        page_content: str = self.get(url)
        with open(local_file, "wb") as f:
            f.write(page_content.encode("utf8"))

    def upload_file(self, local_file, url, content_type=None):
        self.content_type = content_type if content_type is not None else self.content_type
        with open(local_file, "rb") as f:
            self.request_body = f
            self.post(url)

    def _invoke(self, method, url, after_request=None):
        headers = self.create_headers()
        session = requests.Session()

        for k, v in self.cookies.items():
            session.cookies[k] = v

        self._configure_ssl(session, url)

        try:
            call = getattr(session, method)

            if not self.request_body:
                r = call(url, headers=headers, proxies=self.proxies, auth=self.credentials)
            else:
                if self.content_type == "application/json":
                    r = call(url, headers=headers, json=self.request_body, proxies=self.proxies, auth=self.credentials)
                elif self.content_type == "multipart/form-data":
                    m = MultipartEncoder(fields={"file": (self.request_body, open(self.request_body, "rb"))})
                    headers["Content-Type"] = m.content_type
                    r = call(url, headers=headers, data=m, proxies=self.proxies, auth=self.credentials)
                else:
                    r = call(url, headers=headers, data=self.request_body, proxies=self.proxies, auth=self.credentials)

            if self.raise_for_status:
                r.raise_for_status()

            if after_request is not None:
                after_request(r, session)

            return self.response_callback(r)

        finally:
            session.close()

    def _configure_ssl(self, session, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https":
            return

        if self.disable_ssl_check:
            session.verify = False
            return

        host = parsed_url.hostname
        cert_file = None

        if self.cert_file is None:
            if host.endswith(".hsbc"):
                cert_file = os.path.join(RestClient.get_current_dir(), "cert", "combined-g2.pem")
            elif host.endswith(".hsbc.com.hk"):
                cert_file = os.path.join(RestClient.get_current_dir(), "cert", "digi-cert.pem")
            else:
                cert_file = os.path.join(RestClient.get_current_dir(), "cert", "hsbc-proxy-ssl.pem")
        else:
            cert_file = os.path.join(RestClient.get_current_dir(), "cert", self.cert_file)

        session.verify = cert_file

    def create_headers(self):
        headers = {}
        if self.content_type:
            headers["Content-Type"] = self.content_type
        if self.additional_headers:
            headers.update(self.additional_headers)
        return headers

    @staticmethod
    def get_current_dir():
        return os.path.dirname(os.path.realpath(__file__))
```

---

### `confluence.py`

```python
import json
import os
from urllib.parse import quote_plus
import hsbcnet.api.common as common
from hsbcnet.http import RestClient


class Confluence(common.Sensitive):
    CONFLUENCE_HOST = "https://alm-confluence.systems.uk.hsbc/confluence"

    def __init__(self, credentials=tuple()):
        super().__init__(credentials)

    def create_page_body(self, space_key, page_title, parent_page_id, html_page_data):
        page_body = Confluence.get_data(html_page_data)
        return {
            "type": "page",
            "title": page_title,
            "ancestors": [{"id": parent_page_id}],
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": page_body,
                    "representation": "storage"
                }
            }
        }

    def create_or_update(self, space_key, page_title, json_page_data):
        resp = self.find_page(space_key, page_title)
        if resp is None:
            resp = self.create_page(json_page_data)
        else:
            resp = self.update_page(resp, json_page_data)
        return f"{self.CONFLUENCE_HOST}{resp['_links']['tinyui']}"

    def find_page(self, space_key, page_title):
        encoded_title = quote_plus(page_title)
        resp = self._call_confluence_service(
            f"/content?spaceKey={space_key}&title={encoded_title}&expand=version"
        )
        if "results" in resp and len(resp["results"]) > 0:
            return resp
        return None

    def create_page(self, json_page_data):
        page_data = Confluence.get_data(json_page_data, "application/json")
        return self._call_confluence_service("/content", "post", page_data)

    def copy_page(self, space_key, old_page_id, page_title, parent_page_id):
        resp = self._call_confluence_service(f"/content/{old_page_id}?expand=body.storage")
        html_page_content = resp["body"]["storage"]["value"]
        new_page_data = self.create_page_body(space_key, page_title, parent_page_id, html_page_content)
        return self.create_page(new_page_data)

    def get_content_by_title(self, space_key, page_title):
        encoded_space_key = quote_plus(space_key)
        encoded_page_title = quote_plus(page_title)
        resp = self._call_confluence_service(
            f"/content?title={encoded_page_title}&spaceKey={encoded_space_key}&expand=body.storage"
        )
        if "results" in resp and len(resp["results"]) > 0:
            result = resp["results"][0]
            return result["body"]["storage"]["value"]
        return None

    def update_page(self, json_resp, json_page_data):
        page_data = Confluence.get_data(json_page_data, "application/json")
        json_resp_data = Confluence.get_data(json_resp, "application/json")

        result = json_resp_data["results"][0]
        page_id = result["id"]

        page_version = result.get("version", {}).get("number", 1) + 1
        page_data["version"] = {"number": page_version}

        return self._call_confluence_service(f"/content/{page_id}", "put", page_data)

    def _call_confluence_service(self, endpoint, method="get", json_data=None):
        rest_client = RestClient(credentials=self.credentials, request_body=json_data)
        request_url = self._get_endpoint(endpoint)

        if method == "get":
            return rest_client.get(request_url)
        elif method == "post":
            return rest_client.post(request_url)
        elif method == "put":
            return rest_client.put(request_url)
        elif method == "patch":
            return rest_client.patch(request_url)
        return None

    @staticmethod
    def path(endpoint):
        e = endpoint
        if e.startswith("/"):
            e = e[1:]
        return e

    def _get_endpoint(self, endpoint):
        e = Confluence.path(endpoint)
        return f"{self.CONFLUENCE_HOST}/rest/api/{e}"

    @staticmethod
    def get_data(data, content_type=""):
        result = data
        if isinstance(data, str) and os.path.exists(data) and os.path.isfile(data):
            with open(data, "r", encoding="utf8") as f:
                if content_type == "application/json":
                    result = json.load(f)
                else:
                    result = f.read()
        return result
```

---

## 2. `extract_urls.py` – Search Pages by Keyword

```python
from confluence import Confluence
import sys

def search_pages(conf, space_key, keyword):
    cql = f'space="{space_key}" and title~"{keyword}"'
    resp = conf._call_confluence_service(
        f"/content/search?cql={cql}&expand=version"
    )
    urls = []
    if "results" in resp:
        for r in resp["results"]:
            urls.append(conf.CONFLUENCE_HOST + r["_links"]["tinyui"])
    return urls


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python extract_urls.py <space_key> <keyword> <username> <password_or_api_token>")
        sys.exit(1)

    space_key = sys.argv[1]
    keyword = sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]

    conf = Confluence(credentials=(username, password))

    urls = search_pages(conf, space_key, keyword)
    print("\n".join(urls))

```

---

✅ With this setup:

* Put your certs under `cert/` directory.
* Update credentials.
* Run `python extract_urls.py` → it will list all Confluence page URLs matching the keyword.

---

Do you want me to also make this script **accept keyword & space key from command line arguments** (`python extract_urls.py ALM setup`)?
