import argparse
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

console = Console()

CHUNK_SIZE = 256 * 1024
UI_REFRESH_SEC = 0.2

# Список всех стран
REGIONS = {
    "ru": {
        "title": "Россия",
        "servers": [
            {"name": "Selectel", "url": "https://speedtest.selectel.ru/10GB"},
            {"name": "RastrNet", "url": "http://speedtest.rastrnet.ru/10GB.zip"},
            {"name": "RastrNet (fallback)", "url": "http://speedtest.rastrnet.ru/1GB.zip"},
            {"name": "TrueNetwork", "url": "https://mirror-1.truenetwork.ru/speedtest/10GiB"},
            {"name": "TrueNetwork (fallback)", "url": "https://mirror-1.truenetwork.ru/speedtest/1GiB"},
        ],
    },

    # Северная Америка
    "us": {
        "title": "США",
        "servers": [
            {"name": "Vultr New Jersey (East)", "url": "https://nj-us-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Vultr Los Angeles (West)", "url": "https://lax-ca-us-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Leaseweb US mirror", "url": "http://mirror.us.leaseweb.net/speedtest/10000mb.bin"},
            {"name": "Leaseweb US mirror (fallback)", "url": "http://mirror.us.leaseweb.net/speedtest/1000mb.bin"},
        ],
    },
    "ca": {
        "title": "Канада",
        "servers": [
            {"name": "Vultr Toronto", "url": "https://tor-ca-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Vultr Vancouver", "url": "https://yvr-ca-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "mx": {
        "title": "Мексика",
        "servers": [
            {"name": "Vultr Mexico City", "url": "https://mex-mx-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "br": {
        "title": "Бразилия",
        "servers": [
            {"name": "Vultr Sao Paulo", "url": "https://sao-br-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },

    # Европа
    "uk": {
        "title": "Великобритания",
        "servers": [
            {"name": "Vultr London", "url": "https://lon-gb-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "ThinkBroadband (UK)", "url": "http://ipv4.download.thinkbroadband.com/10GB.zip"},
            {"name": "ThinkBroadband (UK) (fallback)", "url": "http://ipv4.download.thinkbroadband.com/1GB.zip"},
        ],
    },
    "fr": {
        "title": "Франция",
        "servers": [
            {"name": "Vultr Paris", "url": "https://par-fr-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "OVH (FR)", "url": "http://proof.ovh.net/files/10Gb.dat"},
            {"name": "OVH (FR) (fallback)", "url": "http://proof.ovh.net/files/1Gb.dat"},
        ],
    },
    "de": {
        "title": "Германия",
        "servers": [
            {"name": "Vultr Frankfurt", "url": "https://fra-de-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Hetzner (DE)", "url": "https://speed.hetzner.de/10GB.bin"},
            {"name": "Hetzner (DE) (fallback)", "url": "https://speed.hetzner.de/1GB.bin"},
        ],
    },
    "nl": {
        "title": "Нидерланды",
        "servers": [
            {"name": "Vultr Amsterdam", "url": "https://ams-nl-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Leaseweb NL mirror", "url": "http://mirror.nl.leaseweb.net/speedtest/10000mb.bin"},
            {"name": "Leaseweb NL mirror (fallback)", "url": "http://mirror.nl.leaseweb.net/speedtest/1000mb.bin"},
        ],
    },
    "es": {
        "title": "Испания",
        "servers": [
            {"name": "Vultr Madrid", "url": "https://mad-es-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "pl": {
        "title": "Польша",
        "servers": [
            {"name": "Vultr Warsaw", "url": "https://waw-pl-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "se": {
        "title": "Швеция",
        "servers": [
            {"name": "Vultr Stockholm", "url": "https://sto-se-ping.vultr.com/vultr.com.100MB.bin"},
            {"name": "Tele2 (SE)", "url": "http://speedtest.tele2.net/10GB.zip"},
            {"name": "Tele2 (SE) (fallback)", "url": "http://speedtest.tele2.net/1GB.zip"},
        ],
    },

    # Азия / Океания
    "sg": {
        "title": "Сингапур",
        "servers": [
            {"name": "Vultr Singapore", "url": "https://sgp-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "jp": {
        "title": "Япония",
        "servers": [
            {"name": "Vultr Tokyo (HND)", "url": "https://hnd-jp-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "kr": {
        "title": "Южная Корея",
        "servers": [
            {"name": "Vultr Seoul", "url": "https://sel-kor-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
    "au": {
        "title": "Австралия",
        "servers": [
            {"name": "Vultr Sydney", "url": "https://syd-au-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },

    # Африка
    "za": {
        "title": "ЮАР",
        "servers": [
            {"name": "Vultr Johannesburg", "url": "https://jnb-za-ping.vultr.com/vultr.com.100MB.bin"},
        ],
    },
}

ORDER = ["ru", "us", "ca", "mx", "br", "uk", "fr", "de", "nl", "es", "pl", "se", "sg", "jp", "kr", "au", "za"]


@dataclass
class Shared:
    bytes_total: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    stop: threading.Event = field(default_factory=threading.Event)


def short_url(u: str) -> str:
    p = urlparse(u)
    host = p.netloc or u
    path = p.path or ""
    return f"{host}{path}"


def verify_url(url: str) -> bool:
    try:
        with requests.get(
            url,
            stream=True,
            timeout=8,
            headers={"Range": "bytes=0-0", "User-Agent": "speedtest-menu/1.0"},
            allow_redirects=True,
        ) as r:
            if r.status_code >= 400:
                return False
            for _ in r.iter_content(chunk_size=1):
                break
        return True
    except requests.RequestException:
        return False


def pick_server(servers: list[dict]) -> dict:
    for s in servers:
        if verify_url(s["url"]):
            return s
    return servers[0]


def worker(shared: Shared, url: str, end_t: float):
    headers = {"User-Agent": "speedtest-menu/1.0"}
    while not shared.stop.is_set():
        if time.perf_counter() >= end_t:
            shared.stop.set()
            return
        try:
            with requests.get(url, stream=True, timeout=12, headers=headers, allow_redirects=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    with shared.lock:
                        shared.bytes_total += len(chunk)
                    if time.perf_counter() >= end_t:
                        shared.stop.set()
                        return
        except requests.RequestException:
            time.sleep(0.2)


def build_ui(title: str, server_name: str, url: str, elapsed: float, total: float, threads: int,
             mbps_now: float, mbps_avg: float, mib: float) -> Panel:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    table.add_column("k", style="bold cyan", width=11, no_wrap=True)
    table.add_column("v", overflow="ellipsis")

    table.add_row("Регион", title)
    table.add_row("Сервер", server_name)
    table.add_row("URL", short_url(url))
    table.add_row("Потоки", str(threads))
    table.add_row("Текущее", speed_pair_text(mbps_now, digits=1))
    table.add_row("Среднее", speed_pair_text(mbps_avg, digits=1))
    table.add_row("Скачано", f"{mib:.1f} MiB")
    table.add_row("Время", f"{min(elapsed, total):.1f} / {total:.1f} сек")

    return Panel(table, title="Speedtest BUTTER (sergey0066)", border_style="green")


def run_test(title: str, server_name: str, url: str, duration: float, threads: int, show_ui: bool = True) -> dict:
    shared = Shared()
    start = time.perf_counter()
    end_t = start + duration

    ts = [threading.Thread(target=worker, args=(shared, url, end_t), daemon=True) for _ in range(threads)]
    for t in ts:
        t.start()

    last_bytes = 0
    last_t = start
    mbps_now = 0.0

    def tick():
        nonlocal last_bytes, last_t, mbps_now
        now = time.perf_counter()
        elapsed = now - start
        with shared.lock:
            b = shared.bytes_total
        if now - last_t >= 1.0:
            db = b - last_bytes
            dt = now - last_t
            mbps_now = (db * 8.0) / (dt * 1_000_000.0) if dt > 0 else 0.0
            last_bytes = b
            last_t = now
        mbps_avg = (b * 8.0) / (max(elapsed, 1e-6) * 1_000_000.0)
        mib = b / 1024 / 1024
        if now >= end_t:
            shared.stop.set()
        return elapsed, b, mbps_avg, mib

    if show_ui:
        with Live(build_ui(title, server_name, url, 0, duration, threads, 0, 0, 0),
                  refresh_per_second=10, console=console) as live:
            while True:
                elapsed, b, mbps_avg, mib = tick()
                live.update(build_ui(title, server_name, url, elapsed, duration, threads, mbps_now, mbps_avg, mib))
                if shared.stop.is_set():
                    break
                time.sleep(UI_REFRESH_SEC)
    else:
        while True:
            tick()
            if shared.stop.is_set():
                break
            time.sleep(UI_REFRESH_SEC)

    for t in ts:
        t.join(timeout=0.2)

    total_bytes = shared.bytes_total
    avg_mbps = (total_bytes * 8.0) / (duration * 1_000_000.0)
    return {
        "region": title,
        "server": server_name,
        "url": url,
        "avg_mbps": avg_mbps,
        "avg_mbs": avg_mbps / 8.0,
        "downloaded_mib": total_bytes / 1024 / 1024,
        "elapsed_sec": duration,
    }


def build_all_ui(
    results_by_code: dict,
    current_k: str,
    remaining_s: float,
    downloaded_mib_now: float,
    mbps_now: float,
    mbps_avg: float,
) -> Panel:
    t = Table(box=box.SIMPLE, show_header=True, padding=(0, 1), expand=True)
    t.add_column("", justify="left", no_wrap=True, width=7)
    for k in ORDER:
        t.add_column(k, justify="center", no_wrap=True, width=5)

    row_status: List[object] = []
    row_mbps: List[object] = []
    for k in ORDER:
        if k == current_k:
            row_status.append(f"[bold yellow]{max(0, int(remaining_s + 0.999))}s[/]")
            row_mbps.append(speed_text(mbps_avg, digits=0))
            continue
        r = results_by_code.get(k)
        if not r:
            row_status.append("...")
            row_mbps.append("-")
        else:
            row_status.append("[green]OK[/]")
            row_mbps.append(speed_text(float(r["avg_mbps"]), digits=0))

    t.add_row("Time", *row_status)
    t.add_row("Среднее", *row_mbps)

    info = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    info.add_column("k", style="bold cyan", width=14, no_wrap=True)
    info.add_column("v", overflow="ellipsis")
    info.add_row("Режим", "all (по очереди)")
    info.add_row("Сейчас", f"{current_k} — {REGIONS[current_k]['title']}")
    info.add_row("Скачано", f"{downloaded_mib_now:.0f} MiB")
    info.add_row("Текущее", speed_pair_text(mbps_now, digits=1))
    info.add_row("Среднее", speed_pair_text(mbps_avg, digits=1))

    outer = Table.grid(expand=True)
    outer.add_row(t)
    outer.add_row(info)
    return Panel(outer, title="Speedtest BUTTER (sergey0066) ALL", border_style="green")


def rainbow_text(s: str) -> Text:
    colors = ["red", "orange1", "yellow1", "green", "cyan", "blue", "magenta"]
    t = Text(s)
    for i, _ch in enumerate(s):
        t.stylize(colors[i % len(colors)], i, i + 1)
    return t


def speed_style(v_mbps: float) -> str:
    if v_mbps <= 10:
        return "red"
    if v_mbps <= 50:
        return "orange1"
    if v_mbps <= 100:
        return "yellow1"
    if v_mbps <= 500:
        return "green"
    return "blue"


def colored_number_text(number_str: str, mbps_for_style: float) -> Text:
    st = speed_style(mbps_for_style)
    return rainbow_text(number_str) if st == "rainbow" else Text(number_str, style=st)


def speed_text(v: float, digits: int = 0) -> Text:
    s = f"{v:.{digits}f}"
    return colored_number_text(s, v)


def speed_pair_text(mbps: float, digits: int = 1) -> Text:
    a = f"{mbps:.{digits}f}"
    b = f"{(mbps / 8.0):.{digits}f}"
    t = Text()
    t.append_text(colored_number_text(a, mbps))
    t.append(" Mbps (")
    t.append_text(colored_number_text(b, mbps))
    t.append(" MB/s)")
    return t


def prompt_choice() -> str:
    menu = Table(
        title="By BUTTER (sergey0066)\nПроверка скорости интернета для 17 стран",
        box=box.SIMPLE,
    )
    menu.add_column("Код", style="bold cyan", no_wrap=True)
    menu.add_column("Страна/регион", style="bold")

    for k in ORDER:
        menu.add_row(k, REGIONS[k]["title"])

    menu.add_row("all", "Всё вместе")
    menu.add_row("custom", "Свой URL")
    console.print(menu)

    choices = ORDER + ["all", "custom"]
    choices_str = "/".join(choices)
    default = "ru"
    while True:
        s = input(f"Выберите [{choices_str}]: ").strip().lower()
        if not s:
            return default
        if s in choices:
            return s
        console.print("[red]Неверный выбор.[/] Попробуй ещё раз.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", help="Код региона (или all/custom). Если не указан — меню.")
    ap.add_argument("--threads", type=int, default=8, help="Количество потоков")
    ap.add_argument("--url", type=str, help="Свой URL (для custom)")
    args = ap.parse_args()

    choice = (args.region or prompt_choice()).lower()
    console.print()

    results: List[dict] = []
    results_by_code: Optional[Dict[str, dict]] = None
    duration = 60.0

    if choice == "custom":
        url = args.url or Prompt.ask("Вставь URL для скачивания (файл)")
        results.append(run_test("Свой URL", "custom", url, duration, args.threads, show_ui=True))
    elif choice == "all":
        duration = 15.0
        results_by_code = {}
        with Live(build_all_ui(results_by_code, ORDER[0], duration, 0.0, 0.0, 0.0),
                  refresh_per_second=10, console=console) as live:
            for k in ORDER:
                region = REGIONS[k]
                server = pick_server(region["servers"])
                url = server["url"]

                shared = Shared()
                start = time.perf_counter()
                end_t = start + duration
                ts = [threading.Thread(target=worker, args=(shared, url, end_t), daemon=True) for _ in range(args.threads)]
                for t in ts:
                    t.start()

                last_bytes = 0
                last_t = start
                mbps_now = 0.0
                samples: List[float] = []

                while True:
                    now = time.perf_counter()
                    elapsed = now - start
                    remaining = max(0.0, duration - elapsed)
                    with shared.lock:
                        b = shared.bytes_total

                    if now - last_t >= 1.0:
                        db = b - last_bytes
                        dt = now - last_t
                        mbps_now = (db * 8.0) / (dt * 1_000_000.0) if dt > 0 else 0.0
                        last_bytes = b
                        last_t = now
                        samples.append(mbps_now)

                    mbps_avg = (b * 8.0) / (max(elapsed, 1e-6) * 1_000_000.0)
                    downloaded_mib_now = b / 1024 / 1024
                    live.update(build_all_ui(results_by_code, k, remaining, downloaded_mib_now, mbps_now, mbps_avg))

                    if now >= end_t:
                        shared.stop.set()
                    if shared.stop.is_set():
                        break
                    time.sleep(UI_REFRESH_SEC)

                for t in ts:
                    t.join(timeout=0.2)

                total_bytes = shared.bytes_total
                avg_mbps = (total_bytes * 8.0) / (duration * 1_000_000.0)
                min_mbps = min(samples) if samples else avg_mbps
                max_mbps = max(samples) if samples else avg_mbps
                r = {
                    "region_code": k,
                    "region": region["title"],
                    "server": server["name"],
                    "url": url,
                    "avg_mbps": avg_mbps,
                    "avg_mbs": avg_mbps / 8.0,
                    "min_mbps": min_mbps,
                    "max_mbps": max_mbps,
                    "downloaded_mib": total_bytes / 1024 / 1024,
                    "elapsed_sec": duration,
                }
                results.append(r)
                results_by_code[k] = r
    else:
        if choice not in REGIONS:
            raise SystemExit("Неизвестный регион. Запусти без --region, чтобы увидеть меню.")
        region = REGIONS[choice]
        server = pick_server(region["servers"])
        results.append(run_test(region["title"], server["name"], server["url"], duration, args.threads, show_ui=True))

    console.print()
    if choice == "all":
        list_tbl = Table(title="Страна — Среднее / Max (Mbps)", box=box.SIMPLE_HEAVY, show_lines=False)
        list_tbl.add_column("Страна", style="bold", overflow="ellipsis")
        list_tbl.add_column("Среднее", justify="right")
        list_tbl.add_column("Max", justify="right")
        for k in ORDER:
            r = (results_by_code or {}).get(k)
            if not r:
                continue
            list_tbl.add_row(
                f"{REGIONS[k]['title']}",
                speed_text(float(r.get("avg_mbps", 0.0))),
                speed_text(float(r.get("max_mbps", 0.0))),
            )
        console.print(list_tbl)
    else:
        summary = Table(title="Итоговая сводка", box=box.SIMPLE_HEAVY)
        summary.add_column("Регион", style="bold")
        summary.add_column("Сервер")
        summary.add_column("Средняя", justify="right")
        summary.add_column("≈ MB/s", justify="right")
        summary.add_column("Скачано", justify="right")
        summary.add_column("Время", justify="right")

        for r in results:
            mbps = float(r["avg_mbps"])
            summary.add_row(
                r["region"],
                r["server"],
                speed_text(mbps, digits=1),
                colored_number_text(f"{(mbps / 8.0):.1f}", mbps),
                f"{r['downloaded_mib']:.0f} MiB",
                f"{r['elapsed_sec']:.0f}s",
            )
        console.print(summary)

    if sys.stdin and sys.stdin.isatty():
        try:
            input("\nНажми Enter, чтобы выйти...")
        except EOFError:
            pass


if __name__ == "__main__":
    main()