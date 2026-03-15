"""Targeted, high-signal crawler for women-health references."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import re
import scrapy


class WomenHealthSpider(scrapy.Spider):
    name = "women_health"

    allowed_domains = [
        "acog.org",
        "cdc.gov",
        "mayoclinic.org",
        "medlineplus.gov",
        "nichd.nih.gov",
        "nice.org.uk",
        "nhs.uk",
        "pubmed.ncbi.nlm.nih.gov",
        "who.int",
        "womenshealth.gov",
    ]

    # Seed list focuses on guideline-like pages (high signal, low noise).
    start_urls = [
        "https://www.acog.org/womens-health/faqs/periods",
        "https://www.acog.org/womens-health/faqs/heavy-menstrual-bleeding",
        "https://www.acog.org/womens-health/faqs/abnormal-uterine-bleeding",
        "https://www.acog.org/womens-health/faqs/endometriosis",
        "https://www.acog.org/womens-health/faqs/uterine-fibroids",
        "https://www.acog.org/womens-health/faqs/painful-periods",
        "https://www.who.int/health-topics",
        "https://www.who.int/news/item/23-04-2025-who-releases-new-guideline-to-prevent-adolescent-pregnancies-and-improve-girls--health",
        "https://www.cdc.gov/reproductivehealth/",
        "https://www.cdc.gov/contraception/hcp/usspr/standard-days-method.html",
        "https://www.cdc.gov/pid/about/index.html",
        "https://www.cdc.gov/std/treatment-guidelines/pid.htm",
        "https://womenshealth.gov/menstrual-cycle/your-menstrual-cycle",
        "https://womenshealth.gov/menstrual-cycle/period-problems",
        "https://womenshealth.gov/pregnancy",
        "https://www.nhs.uk/conditions/periods/period-problems/",
        "https://www.nhs.uk/conditions/vaginal-bleeding-between-periods-or-after-sex/",
        "https://www.nice.org.uk/guidance/ng88",
        "https://www.nichd.nih.gov/health/topics/menstruation/conditioninfo",
        "https://www.nichd.nih.gov/health/topics/pcos",
        "https://www.medlineplus.gov/reproductivehealth.html",
        "https://www.mayoclinic.org/symptoms/women",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        # High-throughput defaults tuned for your local run request.
        "CONCURRENT_REQUESTS": 20,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "REACTOR_THREADPOOL_MAXSIZE": 20,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_TIMEOUT": 25,
        "DOWNLOAD_DELAY": 0.1,
        "RANDOMIZE_DOWNLOAD_DELAY": False,
        "AUTOTHROTTLE_ENABLED": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 2,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "TELNETCONSOLE_ENABLED": False,
        "CLOSESPIDER_PAGECOUNT": 1000000,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "TrackyCrawler/1.1 (+women-health research, contact=local-repo)",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_FIELDS": [
            "url",
            "source",
            "title",
            "canonical_url",
            "language",
            "http_status",
            "publication_date",
            "crawl_depth",
            "fetched_at",
            "fetched_host",
            "content_sha1",
            "content_len",
            "content",
        ],
        "DEPTH_LIMIT": 3,
    }

    # Keywords used to keep only women-health-relevant pages.
    allowed_path_keywords = (
        "women",
        "reproductive",
        "pregnancy",
        "menstrual",
        "period",
        "breast",
        "gyne",
        "fertility",
        "sexual",
        "health-topics",
        "reproductivehealth",
        "reproductive-health",
        "maternal",
        "menopause",
        "childbirth",
        "contraception",
        "ovulation",
        "ovulatory",
        "pcos",
        "endometriosis",
        "fibroid",
        "ovarian",
        "pid",
        "sti",
        "thyroid",
        "infertility",
        "amenorrhea",
        "bleeding",
        "postpartum",
        "breastfeeding",
        "dysmenorrhea",
        "pelvic",
        "pain",
        "uterine",
    )

    # Reject noisy resources.
    blocked_patterns = (
        "mailto:",
        "javascript:",
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".css",
        ".js",
        ".xml",
        ".zip",
        ".json",
        "logout",
        "signin",
        "signup",
        "/search?",
        "&search=",
        "?search=",
        "?term=",
        "?q=",
        "?query=",
        "facebook.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
    )

    # PubMed has very high connectivity; keep only article pages and stop traversal there.
    pubmed_article_re = re.compile(r"https://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?$")
    pubmed_query_re = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/.+")
    canonical_query_params = {"page", "type", "utm_medium", "utm_source", "utm_campaign", "view"}

    # Domain-aware allow rules to avoid low-value follow links.
    allowed_domain_path_rules = {
        "acog.org": (r"^/womens-health/faqs/",),
        "cdc.gov": (r"^/reproductivehealth/", r"^/contraception/", r"^/pid/", r"^/std/"),
        "womenshealth.gov": (r"^/menstrual-cycle/", r"^/pregnancy", r"^/menopause/", r"^/health-topics/"),
        "who.int": (r"^/health-topics/", r"^/news/item/"),
        "nhs.uk": (r"^/conditions/"),
        "nice.org.uk": (r"^/guidance/"),
        "nichd.nih.gov": (r"/health/topics/"),
        "medlineplus.gov": (r"reproductivehealth", r"/conditions/"),
        "mayoclinic.org": (r"/symptoms/", r"/conditions/"),
        "pubmed.ncbi.nlm.nih.gov": (r"^/\d+/?$",),
    }

    # Limits keep crawl useful and fast.
    max_depth = 3
    max_links_per_page = 25
    min_content_chars = 180
    max_pages_per_domain = 4000
    follow_pubmed_links = False
    seed_urls = tuple(start_urls)
    allowed_path_patterns: tuple[re.Pattern[str], ...] = tuple(
        re.compile(rf"(?i){kw}") for kw in allowed_path_keywords
    )

    def __init__(
        self,
        max_depth="3",
        max_links_per_page="25",
        min_content_chars="180",
        max_pages_per_domain="4000",
        seed_file="",
        allowed_domain_file="",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.max_depth = int(max_depth)
        self.max_links_per_page = int(max_links_per_page)
        self.min_content_chars = int(min_content_chars)
        self.max_pages_per_domain = int(max_pages_per_domain)
        self.follow_pubmed_links = (str(kwargs.get("follow_pubmed_links", "false")).lower() == "true")

        # Ensure output directory exists.
        Path("data/web_crawl").mkdir(parents=True, exist_ok=True)

        # Expand seed list from current source catalog so curated URLs continue to surface.
        catalog_path = Path(__file__).resolve().parent.parent / "data" / "source_catalog.csv"
        if catalog_path.exists():
            with catalog_path.open(newline="") as f:
                catalog_rows = list(csv.DictReader(f))
            for row in catalog_rows:
                url = (row.get("url") or "").strip()
                if url.startswith("http") and url not in self.start_urls:
                    self.start_urls.append(url)
            self.start_urls = list(dict.fromkeys(self.start_urls))
            self.seed_urls = set(self.start_urls)

            # Add catalog hostnames to allowed_domains for safer redirects.
            for row in catalog_rows:
                host = (row.get("url") or "").split("://", 1)[-1].split("/", 1)[0].lower()
                if host:
                    self.allowed_domains.append(host)
            self.allowed_domains = list(dict.fromkeys([d.replace("www.", "") for d in self.allowed_domains if d]))
        else:
            self.seed_urls = set(self.start_urls)
        self.seen_urls: set[str] = set()
        self.domain_page_counts: dict[str, int] = {}

        # Optional seed URLs from a file (one URL per line).
        seed_file = (seed_file or "").strip()
        if seed_file:
            seed_path = Path(seed_file)
            if seed_path.exists():
                for line in seed_path.read_text().splitlines():
                    url = line.strip()
                    if url.startswith("http"):
                        self.start_urls.append(url)
                self.start_urls = list(dict.fromkeys(self.start_urls))
                self.seed_urls = set(self.start_urls)

        # Optional allowed domains from a file (one domain per line).
        allowed_domain_file = (allowed_domain_file or "").strip()
        if allowed_domain_file:
            domain_path = Path(allowed_domain_file)
            if domain_path.exists():
                for line in domain_path.read_text().splitlines():
                    domain = line.strip().lower()
                    if domain and not domain.startswith("#"):
                        self.allowed_domains.append(domain.replace("www.", ""))
                self.allowed_domains = list(dict.fromkeys(self.allowed_domains))

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip())

    def _canonicalize(self, raw_url: str) -> str:
        parsed = urlsplit(raw_url)
        if not parsed.scheme or not parsed.netloc:
            return raw_url
        pairs = []
        if parsed.query:
            pairs = [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if not k.startswith("utm_") or k in self.canonical_query_params
            ]
        query = urlencode(pairs, doseq=True)
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]
        return urlunsplit((parsed.scheme, parsed.netloc.lower(), path, query, ""))

    def _host(self, url: str) -> str:
        return (url.split("://", 1)[-1].split("/", 1)[0] or "").lower()

    def _is_blocked_url(self, url: str) -> bool:
        low = url.lower()
        if low.startswith("mailto:") or low.startswith("javascript:"):
            return True
        if low.endswith("#"):
            return True
        return any(token in low for token in self.blocked_patterns)

    def _is_allowed_host(self, host: str) -> bool:
        normalized = host.lower().replace("www.", "")
        for domain in self.allowed_domains:
            candidate = domain.lower().replace("www.", "")
            if normalized == candidate or normalized.endswith(f".{candidate}"):
                return True
        return False

    def _has_allowed_keyword(self, url: str) -> bool:
        low = url.lower()
        return any(pattern.search(low) for pattern in self.allowed_path_patterns)

    def _is_allowed_path(self, url: str) -> bool:
        parsed = urlsplit(url)
        host = self._host(url)
        path = parsed.path.lower()
        host_no_www = host.replace("www.", "")

        # PubMed: keep only direct article pages unless explicit follow flag is enabled.
        if "pubmed.ncbi.nlm.nih.gov" in host_no_www:
            if not self.follow_pubmed_links:
                return self.pubmed_article_re.fullmatch(url.lower()) is not None
            return self.pubmed_article_re.search(url.lower()) is not None

        # Domain rules first (highest precision).
        for domain, rules in self.allowed_domain_path_rules.items():
            if host_no_www == domain or host_no_www.endswith(f".{domain}"):
                if any(re.match(rule, path) for rule in rules):
                    return True
                # Fallback for pages not in explicit pattern (e.g. FAQ anchors).
                return self._has_allowed_keyword(url)

        # Default keyword fallback for additional trusted domains in source_catalog.
        return self._has_allowed_keyword(url)

    def _should_follow(self, host: str, path: str, current_depth: int, from_host: str) -> bool:
        if current_depth >= self.max_depth:
            return False
        if current_depth < 0:
            return False

        # Keep page fan-out bounded; avoids deep menus and infinite nav loops.
        if self.domain_page_counts.get(host, 0) >= self.max_pages_per_domain:
            return False
        if "pubmed.ncbi.nlm.nih.gov" in from_host and not self.follow_pubmed_links:
            return False
        if not self._is_allowed_host(host):
            return False
        if path.endswith("/"):
            pass
        if path and path.count("/") > 8:
            return False

        return True

    def _extract_publication_date(self, response: scrapy.http.Response) -> str:
        selectors = (
            'meta[name="citation_publication_date"]::attr(content)',
            'meta[property="article:published_time"]::attr(content)',
            "time::attr(datetime)",
            'meta[name="date"]::attr(content)',
            'meta[itemprop="dateModified"]::attr(content)',
        )
        for selector in selectors:
            value = response.css(selector).get("")
            if value and len(value.strip()) >= 4:
                return value.strip().split("T", 1)[0]
        return ""

    def _title(self, response: scrapy.http.Response) -> str:
        title = response.css("h1::text").get("") or response.css("title::text").get("") or ""
        return self._clean(title or f"Crawled Page: {response.url}")

    def _content_fingerprint(self, content: str) -> str:
        return hashlib.sha1(content.encode("utf-8")).hexdigest()

    def _extract_content(self, response: scrapy.http.Response) -> str:
        paragraph_nodes: Iterable[str] = response.css(
            "main p::text, article p::text, section p::text, .field-item p::text, .body p::text"
        ).getall()
        cleaned = [self._clean(node) for node in paragraph_nodes]
        paragraphs = [chunk for chunk in cleaned if len(chunk) > 20]
        return self._clean(" ".join(paragraphs))

    async def start(self):
        for url in self.start_urls:
            canonical = self._canonicalize(url)
            if self._is_blocked_url(canonical):
                continue
            if not self._is_allowed_host(self._host(canonical)):
                continue
            yield scrapy.Request(canonical, callback=self.parse, meta={"crawl_depth": 0, "parent": None})

    def parse(self, response: scrapy.http.Response):
        canonical_url = self._canonicalize(response.url)
        if self._is_blocked_url(canonical_url):
            return
        if canonical_url in self.seen_urls:
            return
        self.seen_urls.add(canonical_url)

        host = self._host(canonical_url)
        self.domain_page_counts[host] = self.domain_page_counts.get(host, 0) + 1

        if not self._is_allowed_host(host):
            return
        if self.domain_page_counts[host] > self.max_pages_per_domain:
            return

        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return

        depth = int(response.meta.get("crawl_depth", 0))
        content = self._extract_content(response)
        if len(content) >= self.min_content_chars:
            publication_date = self._extract_publication_date(response)
            lang = response.css("html::attr(lang)").get("en")[:2]
            yield {
                "url": canonical_url,
                "source": self.name,
                "title": self._title(response),
                "canonical_url": canonical_url,
                "language": lang,
                "http_status": response.status,
                "publication_date": publication_date,
                "crawl_depth": depth,
                "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "fetched_host": host,
                "content_sha1": self._content_fingerprint(content),
                "content_len": len(content),
                "content": content,
            }

        if depth >= self.max_depth:
            return

        links_followed = 0
        for raw_link in response.css("a::attr(href)").getall():
            if links_followed >= self.max_links_per_page:
                break
            if self._is_blocked_url(raw_link):
                continue
            url = self._canonicalize(response.urljoin(raw_link))
            if "#" in url:
                url = url.split("#", 1)[0]
            if not url.startswith("http"):
                continue
            if url in self.seed_urls or url in self.seen_urls:
                continue

            candidate_host = self._host(url)
            if not self._is_allowed_host(candidate_host):
                continue
            if self.pubmed_query_re.match(url.lower()) and not self.pubmed_article_re.fullmatch(url.lower()):
                # Prevent broad PubMed search/reference crawls.
                continue
            if not self._is_allowed_path(url):
                continue
            if not self._should_follow(candidate_host, urlsplit(url).path.lower(), depth, host):
                continue

            links_followed += 1
            yield response.follow(
                url,
                callback=self.parse,
                meta={"crawl_depth": depth + 1, "parent": canonical_url},
            )
