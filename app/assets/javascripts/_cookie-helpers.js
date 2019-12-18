// Code to support the cookie banner component

(function (root) {
  'use strict'
  window.GOVUK.GDM = window.GOVUK.GDM || {}

  var DEFAULT_COOKIE_CONSENT = {
    essential: true,
    settings: true,
    usage: true
  }

  var COOKIE_CATEGORIES = {
    cookie_policy: 'essential',
    seen_cookie_message: 'essential',
    cookie_preferences_set: 'essential',
    dm_session: 'essential',
    dm_cookie_probe: 'essential',
    _ga: 'usage',
    _gid: 'usage',
    _gat: 'usage',
    _gat_govuk_shared: 'usage'
  }

  /*
    Cookie methods
    ==============

    Usage:

      Setting a cookie:
      GOVUK.GDM.cookie('hobnob', 'tasty', { days: 30 });

      Reading a cookie:
      GOVUK.GDM.cookie('hobnob');

      Deleting a cookie:
      GOVUK.GDM.cookie('hobnob', null);
  */

  var CookieHelper = function CookieHelper () {}

  CookieHelper.prototype.cookie = function cookie (name, value, options) {
    if (typeof value !== 'undefined') {
      if (value === false || value === null) {
        return this.setCookie(name, '', { days: -1 })
      } else {
        // Default expiry date of 30 days
        if (typeof options === 'undefined') {
          options = { days: 30 }
        }
        return this.setCookie(name, value, options)
      }
    } else {
      return this.getCookie(name)
    }
  }

  CookieHelper.prototype.setDefaultConsentCookie = function () {
    this.setCookie('cookie_policy', JSON.stringify(DEFAULT_COOKIE_CONSENT), { days: 365 })
  }

  CookieHelper.prototype.approveAllCookieTypes = function () {
    var approvedConsent = {
      essential: true,
      settings: true,
      usage: true
    }
    this.setCookie('cookie_policy', JSON.stringify(approvedConsent), { days: 365 })
  }

  CookieHelper.prototype.getConsentCookie = function () {
    var consentCookie = this.cookie('cookie_policy')
    var consentCookieObj

    if (consentCookie) {
      try {
        consentCookieObj = JSON.parse(consentCookie)
      } catch (err) {
        return null
      }

      if (typeof consentCookieObj !== 'object' && consentCookieObj !== null) {
        consentCookieObj = JSON.parse(consentCookieObj)
      }
    } else {
      return null
    }

    return consentCookieObj
  }

  CookieHelper.prototype.setConsentCookie = function (options) {
    var cookieConsent = this.getConsentCookie()

    if (!cookieConsent) {
      cookieConsent = JSON.parse(JSON.stringify(DEFAULT_COOKIE_CONSENT))
    }

    for (var cookieType in options) {
      cookieConsent[cookieType] = options[cookieType]

      // Delete cookies of that type if consent being set to false
      if (!options[cookieType]) {
        for (var cookie in COOKIE_CATEGORIES) {
          if (COOKIE_CATEGORIES[cookie] === cookieType) {
            this.cookie(cookie, null)

            if (this.cookie(cookie)) {
              document.cookie = cookie + '=;expires=' + new Date() + ';domain=.' + window.location.hostname + ';path=/'
            }
          }
        }
      }
    }

    this.setCookie('cookie_policy', JSON.stringify(cookieConsent), { days: 365 })
  }

  CookieHelper.prototype.checkConsentCookieCategory = function (cookieName, cookieCategory) {
    var currentConsentCookie = this.getConsentCookie()

    // If the consent cookie doesn't exist, but the cookie is in our known list, return true
    if (!currentConsentCookie && COOKIE_CATEGORIES[cookieName]) {
      return true
    }

    currentConsentCookie = this.getConsentCookie()

    // Sometimes currentConsentCookie is malformed in some of the tests, so we need to handle these
    try {
      return currentConsentCookie[cookieCategory]
    } catch (e) {
      console.error(e)
      return false
    }
  }

  CookieHelper.prototype.checkConsentCookie = function (cookieName, cookieValue) {
    // If we're setting the consent cookie OR deleting a cookie, allow by default
    if (cookieName === 'cookie_policy' || (cookieValue === null || cookieValue === false)) {
      return true
    }

    if (COOKIE_CATEGORIES[cookieName]) {
      var cookieCategory = COOKIE_CATEGORIES[cookieName]

      return this.checkConsentCookieCategory(cookieName, cookieCategory)
    } else {
      // Deny the cookie if it is not known to us
      return false
    }
  }

  CookieHelper.prototype.setCookie = function (name, value, options) {
    if (this.checkConsentCookie(name, value)) {
      if (typeof options === 'undefined') {
        options = {}
      }
      var cookieString = name + '=' + value + '; path=/'
      if (options.days) {
        var date = new Date()
        date.setTime(date.getTime() + (options.days * 24 * 60 * 60 * 1000))
        cookieString = cookieString + '; expires=' + date.toGMTString()
      }
      if (document.location.protocol === 'https:') {
        cookieString = cookieString + '; Secure'
      }
      document.cookie = cookieString
    }
  }

  CookieHelper.prototype.getCookie = function (name) {
    var nameEQ = name + '='
    var cookies = document.cookie.split(';')
    for (var i = 0, len = cookies.length; i < len; i++) {
      var cookie = cookies[i]
      while (cookie.charAt(0) === ' ') {
        cookie = cookie.substring(1, cookie.length)
      }
      if (cookie.indexOf(nameEQ) === 0) {
        return decodeURIComponent(cookie.substring(nameEQ.length))
      }
    }
    return null
  }

  window.GOVUK.GDM.CookieHelper = new CookieHelper()
}(window));
