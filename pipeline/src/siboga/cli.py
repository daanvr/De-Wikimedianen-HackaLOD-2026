"""Commands: `siboga fetch`, `siboga build`, `siboga all` and `siboga check`."""
import argparse
import sys

from loguru import logger

from siboga.build import check_output, run_build
from siboga.cache import Cache
from siboga.config import Config, load_config
from siboga.content import is_term, read_content, record_uri
from siboga.explorer import fetch_explorer
from siboga.fetcher import Fetcher
from siboga.models import ItemKind, Report
from siboga.sources import build_registry

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog = "siboga",
        description = "Builds the frontend data for De Siboga Expeditie."
    )
    parser.add_argument("-v", "--verbose", action = "store_true", help = "also show debug messages")
    commands = parser.add_subparsers(dest = "command", required = True)
    fetch_parser = commands.add_parser("fetch", help = "fetch sources into the cache (needs internet)")
    fetch_parser.add_argument("--refresh", action = "store_true", help = "fetch everything again, including what is already in the cache")
    commands.add_parser("build", help = "build the frontend data from content and cache (no internet)")
    all_parser = commands.add_parser("all", help = "fetch, then build")
    all_parser.add_argument("--refresh", action = "store_true", help = "fetch everything again")
    commands.add_parser("check", help = "check the frontend data against the contract")
    args = parser.parse_args(argv)
    logger.remove()
    logger.add(sys.stderr, level = "DEBUG" if args.verbose else "INFO")
    config = load_config()
    if args.command == "check":
        return run_check(config)
    if not config.content_path.is_dir():
        logger.error(f"content not found in {config.content_path}; clone the content repo or set [content] path in pipeline/config.toml")
        return 1
    reports = {}
    if args.command in ("fetch", "all"):
        reports["fetch"] = Report()
        run_fetch(config, reports["fetch"], refresh = args.refresh)
    if args.command in ("build", "all"):
        reports["build"] = Report()
        run_build(config, reports["build"])
    for step, report in reports.items():
        logger.info(f"{step}: {len(report.warnings)} warnings")
    return 0

def run_check(config: Config) -> int:
    problems = check_output(config.output_path)
    for problem in problems:
        logger.error(problem)
    if problems:
        logger.error(f"check: {len(problems)} problems in {config.output_path}")
        return 1
    logger.info(f"check: frontend data in {config.output_path} is valid")
    return 0

def run_fetch(
    config: Config,
    report: Report,
    refresh: bool = False
) -> None:
    """Fetches a full copy of each record's source, including images."""
    items = read_content(config.content_path, report)
    registry = build_registry(config)
    cache = Cache(config.cache_path, config.media_path)
    fetcher = Fetcher(
        cache,
        config.user_agent,
        rate_limits = registry.rate_limits(),
        max_age_days = config.max_age_days,
        refresh = refresh,
        timeout_seconds = config.timeout_seconds
    )
    try:
        for item in items:
            # The uri of a term is only a link to read more
            if item.kind != ItemKind.RECORD or is_term(item):
                continue
            uri = record_uri(item, report)
            if uri is None:
                continue
            adapter = registry.adapter_for(uri)
            if adapter is None:
                report.warn(f"no adapter for {uri}", item.path)
                continue
            logger.info(f"{adapter.name}: {item.title}")
            try:
                adapter.fetch(uri, fetcher)
            except Exception as error:
                # One broken source must not stop the rest.
                report.warn(f"fetching failed ({adapter.name}): {error!r}", item.path)
        fetch_explorer(config.gold_path, config.stations_path, fetcher, config.image_width, report)
    finally:
        fetcher.close()
        cache.close()
    logger.info(f"fetch done: {fetcher.stats}")

if __name__ == "__main__":
    sys.exit(main())
