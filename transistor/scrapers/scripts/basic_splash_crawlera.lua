-- transistor.scrapers.scripts.basic_splash_crawlera
-- ~~~~~~~~~~~~
-- This script implements a basic lua script for Splash + Crawlera which is compatable
-- with the SplashScraper class from transistor.scrapers.splash_scraper_abc

-- :copyright: Copyright (C) 2018 by BOM Quote Limited
-- :license: The MIT License, see LICENSE for more details.
-- ~~~~~~~~~~~~

function use_crawlera(splash)
    -- Make sure you pass your Crawlera API key in the 'crawlera_user' arg.
    -- Have a look at the file spiders/quotes-js.py to see how to do it.
    -- Find your Crawlera credentials in https://app.scrapinghub.com/
    local user = splash.args.crawlera_user
    local host = 'proxy.crawlera.com'
    local port = 8010
    local session_header = 'X-Crawlera-Session'
    local session_id = 'create'

    splash:on_request(function (request)
        -- The commented code below can be used to speed up the crawling
        -- process. They filter requests to undesired domains and useless
        -- resources. Uncomment the ones that make sense to your use case
        -- and add your own rules.

        -- Discard requests to advertising and tracking domains.
         if string.find(request.url, 'doubleclick%.net') or
                 string.find(request.url, 'dpm%.demdex%.net') or
                 string.find(request.url, 'assets%.adobedtm%.com') or
                 string.find(request.url, 'analytics%.google%.com') then
             request.abort()
             return
         end

        -- Avoid using Crawlera for subresources fetching to increase crawling
        -- speed. The example below avoids using Crawlera for URLS starting
        -- with 'static.' and the ones ending with '.png'.
         if string.find(request.url, '://static%.') ~= nil or
                 string.find(request.url, '%.png$') ~= nil then
             return
         end

        request:set_header('X-Crawlera-Cookies', 'disable')
        request:set_header(session_header, session_id)
        request:set_proxy{host, port, username=user, password=''}
    end)

     splash:set_custom_headers({
      ["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
      ["Accept-Encoding"] = "identity",
      ["Accept-Language"] = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
      ["Connection"] = "keep-alive",
      ["DNT"] = "1",
      ["Referer"] = splash.args.referrer,
      ["User-Agent"] = splash.args.user_agent,
     })

    splash:on_response_headers(function (response)
        if type(response.headers[session_header]) ~= nil then
            session_id = response.headers[session_header]
        end
    end)
end

function main(splash)
    splash.response_body_enabled = true
    use_crawlera(splash)
    assert(splash:go(splash.args.url))
    assert(splash:wait(3.0))
    return splash:html()
end