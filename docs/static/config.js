/**
 * Libya B2B Platform — Runtime API + site configuration
 * Loaded FIRST in <head> via build_static.py.
 * Sets window.API_BASE so all fetch() calls work on any origin.
 * Sets window.SITE_BASE so all JS-built internal links work under the
 * GitHub Pages repo prefix (/b2b-libya). Empty string for same-origin/local.
 */
(function () {
  var loc = window.location;
  var isLocal = loc.hostname === "localhost" || loc.hostname === "127.0.0.1";
  window.API_BASE = isLocal ? "/api" : "https://libya-b2b-backend.onrender.com";
  window.SITE_BASE = isLocal ? "" : "/b2b-libya";
})();
