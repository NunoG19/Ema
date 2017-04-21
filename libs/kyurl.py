# -*- coding: utf-8 -*-
#
# (c) 2016 Nuneo, http://www.nuneo.top
#
# This file is part of Ema.
#
# Ema is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ema is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ema.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function


class KyUrlRequest():
    
    def _url_request(self, url, callback=None, callback_if_fail=None):
        Logger.info(
            self.name+": Downloading: %s -> %s" % (url, callback))
        
        if not callback:
             req = UrlRequest(url,
                on_redirect=self._on_url_request_redirect,
                on_success=self._on_url_request_success,
                on_failure=self._on_url_request_fail,
                on_error=self._on_url_request_error,
                timeout=10)
        elif callback_if_fail:
            req = UrlRequest(url,
                on_redirect=self._on_url_request_redirect,
                on_success=callback,
#                on_progress=self._on_url_request_progress,
                on_failure=lambda x, y:
                        self._on_url_request_fail(
                            x, y, callback_if_fail),
                on_error=lambda x, y:
                        self._on_url_request_error(
                            x, y, callback_if_fail),
                timeout=10)
        else:
           req = UrlRequest(url,
                on_redirect=self._on_url_request_redirect,
                on_success=callback,
                on_failure=self._on_url_request_fail,
                on_error=self._on_url_request_error,
                timeout=10)
        req.callback = callback
        req.callback_if_fail = callback_if_fail
        return req

    def _on_url_request_redirect(self, request, result, callback=None):
        self._url_request(
            "http://"+request.resp_headers["x-host"]
                +request.resp_headers["location"],
            request.callback,
            request.callback_if_fail)

    def _on_url_request_success(self, request, result, callback=None):
        Logger.info(self.name+": Url request success: %s" % request)

    def _on_url_request_progress(self, request, result, callback=None):
        Logger.info(self.name+": Progress %s" % request)
        
    def _on_url_request_fail(self, request, result, callback=None):
        Logger.error(self.name+": Url request failed: %s" % result)
        if callback:
            callback(request, result)

    def _on_url_request_error(self, request, result, callback=None):
        Logger.error(self.name+": Url request error: %s" % result)
        if callback:
            callback(request, result)
