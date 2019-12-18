// Code to support the cookie banner page
(function (window) {
  'use strict'
  window.GOVUK.GDM = window.GOVUK.GDM || {}
  function CookieBanner () { }

  CookieBanner.prototype.init = function () {
    this.$cookieBanner = document.querySelector('#global-cookie-message')
    this.$cookieBannerMainContent = document.querySelector('#dm-cookie-banner-message')
    this.$cookieBannerConfirmationMessage = document.querySelector('#dm-cookie-banner-confirmation')

    this.hideCookieMessage = this.hideCookieMessage.bind(this)
    this.showConfirmationMessage = this.showConfirmationMessage.bind(this)
    this.setCookieConsent = this.setCookieConsent.bind(this)

    this.setupCookieMessage()
  }

  CookieBanner.prototype.setupCookieMessage = function () {
    this.$hideLink = this.$cookieBanner.querySelector('#dm-hide-cookie-banner')
    if (this.$hideLink) {
      this.$hideLink.addEventListener('click', this.hideCookieMessage)
    }

    this.$acceptCookiesLink = this.$cookieBanner.querySelector('#dm-accept-cookies')
    if (this.$acceptCookiesLink) {
      this.$acceptCookiesLink.addEventListener('click', this.setCookieConsent)
    }

    // Force the new cookie banner to show if we don't think the user has seen it before
    // This involves resetting the seen_cookie_message cookie, which may be set to true if they've seen the old cookie banner
    if (!window.GOVUK.GDM.cookie('cookie_policy')) {
      if (window.GOVUK.GDM.cookie('seen_cookie_message') === 'true') {
        window.GOVUK.GDM.cookie('seen_cookie_message', false, { days: 365 })
      }
    }
    this.showCookieMessage()
  }

  CookieBanner.prototype.showCookieMessage = function () {
    // Show the cookie banner if not in the cookie settings page or in an iframe
    if (!this.isInCookiesPage() && !this.isInIframe()) {
      var shouldHaveCookieMessage = (this.$cookieBanner && window.GOVUK.GDM.cookie('seen_cookie_message') !== 'true')
      if (shouldHaveCookieMessage) {
        this.$cookieBanner.style.display = 'block'

        // Set the default consent cookie if it isn't already present
        if (!window.GOVUK.GDM.cookie('cookie_policy')) {
          window.GOVUK.GDM.setDefaultConsentCookie()
        }
      } else {
        this.$cookieBanner.style.display = 'none'
      }
    } else {
      this.$cookieBanner.style.display = 'none'
    }
  }

  CookieBanner.prototype.hideCookieMessage = function (event) {
    if (this.$cookieBanner) {
      this.$cookieBanner.style.display = 'none'
      window.GOVUK.GDM.cookie('seen_cookie_message', 'true', { days: 365 })
    }

    if (event.target) {
      event.preventDefault()
    }
  }

  CookieBanner.prototype.setCookieConsent = function () {
    window.GOVUK.GDM.approveAllCookieTypes()
    this.showConfirmationMessage()
    this.$cookieBannerConfirmationMessage.focus()
    window.GOVUK.GDM.cookie('seen_cookie_message', 'true', { days: 365 })
  }

  CookieBanner.prototype.showConfirmationMessage = function () {
    this.$cookieBannerMainContent.style.display = 'none'
    this.$cookieBannerConfirmationMessage.style.display = 'block'
  }

  CookieBanner.prototype.listenForCrossOriginMessages = function () {
    window.addEventListener('message', this.receiveMessage.bind(this), false)
  }

  CookieBanner.prototype.isInCookiesPage = function () {
    return window.location.pathname === '/cookie-settings'
  }

  CookieBanner.prototype.isInIframe = function () {
    return window.parent && window.location !== window.parent.location
  }

  window.GOVUK.GDM.CookieBanner = CookieBanner

})(window);

(function (window) {
  // Initialise the module above
  window.GOVUK.GDM = window.GOVUK.GDM || {}

  var _cookieBanner = new window.GOVUK.GDM.CookieBanner();
  _cookieBanner.init()

})(window);
