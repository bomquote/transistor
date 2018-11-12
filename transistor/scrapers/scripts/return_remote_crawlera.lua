-- transistor.scrapers.scripts.return_remote_crawlera
-- ~~~~~~~~~~~~
-- This script implements a more advanced lua script for Splash + Crawlera which can
-- return headers and status code from the end target website. This script is
-- compatable with the SplashScraper class from transistor.scrapers.splash_scraper_abc
-- and if using Splash + Crawlera, it is advised to use this script as a template per
-- your own final custom requirement.  Particularly, you should modify the
-- splash:on_request method to discard advertising and tracking domains, which your
-- target end website may be using.  There is no easy solution for this, you need to
-- do the research on your targets, for example, examine in google chrome dev tools.

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
    local session_id = splash.args.session_id

    splash:on_request(function (request)
        -- The commented code below can be used to speed up the crawling
        -- process. They filter requests to undesired domains and useless
        -- resources. Uncomment the ones that make sense to your use case
        -- and add your own rules.

        -- Discard requests to advertising and tracking domains.
         if string.find(request.url, 'doubleclick%.net') or
                 string.find(request.url, 'dpm%.demdex%.net') or
                 string.find(request.url, 'assets%.adobedtm%.com') or
                 string.find(request.url, 'secure%.livechatinc%.com') or
                 string.find(request.url, 'hm%.baidu%.com') or
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
        ["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    })

    splash:on_response_headers(function (response)
        if type(response.headers[session_header]) ~= nil then
            session_id = response.headers[session_header]
        end
    end)
end

function main(splash)
    use_crawlera(splash)
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
    assert(splash:wait(3.0))

    local entries = splash:history()
    local last_response = entries[#entries].response
    return {
        url = splash:url(),
        headers = last_response.headers,
        http_status = last_response.status,
        cookies = splash:get_cookies(),
        html = splash:html(),
        har=splash:har(),
        png = splash:png(),
    }
end