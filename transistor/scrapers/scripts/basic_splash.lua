-- transistor.scrapers.scripts.basic_splash
-- ~~~~~~~~~~~~
-- This script implements a basic lua script for Splash which is compatable with
-- the SplashScraper class from transistor.scrapers.splash_scraper_abc

-- :copyright: Copyright (C) 2018 by BOM Quote Limited
-- :license: The MIT License, see LICENSE for more details.
-- ~~~~~~~~~~~~

function main(splash)
    splash:set_custom_headers({
      ["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
      ["Accept-Encoding"] = "identity",
      ["Accept-Language"] = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
      ["Connection"] = "keep-alive",
      ["DNT"] = "1",
      ["Referer"] = splash.args.referrer,
      ["User-Agent"] = splash.args.user_agent,
     })
    assert(splash:go{
    splash.args.url,
    -- https://splash.readthedocs.io/en/stable/scripting-ref.html#splash-set-user-agent
    -- When headers argument of splash:go is used headers set with splash:set_custom_headers...
    -- are not applied to the initial request: values are not merged, headers argument...
    -- of splash:go has higher priority.
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
    assert(splash:wait(splash.args.splash_wait))
    return {
        url = splash:url(),
        cookies = splash:get_cookies(),
        html = splash:html(),
        har=splash:har(),
        png = splash:png(),
    }
end