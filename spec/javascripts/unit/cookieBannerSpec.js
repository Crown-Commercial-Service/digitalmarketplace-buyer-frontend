// https://github.com/alphagov/govuk_publishing_components/blob/master/spec/javascripts/components/cookie-banner-spec.js

/* eslint-env jasmine, jquery */
var GOVUK = window.GOVUK || {};
'use strict';
describe('Cookie banner', function () {
  var container,
      cookieBanner,
      element;

  var DEFAULT_COOKIE_CONSENT

  beforeEach(function () {
    cookieBanner = new GOVUK.GDM.CookieBanner()
    container = document.createElement('div')
    container.innerHTML =
      '<div id="global-cookie-message">' +
        '<div id="dm-cookie-banner-message" class="cookie-banner__wrapper govuk-width-container" style="display: block;">' +
          '<p class="cookie-banner__message">GOV.UK uses cookies which are essential for the site to work. We also use non-essential cookies to help us improve government digital services. Any data collected is anonymised. By continuing to use this site, you agree to our use of cookies.</p>' +
          '<div class="cookie-banner__buttons">' +
            '<button id="dm-accept-cookies" class="button govuk-button button--secondary-quiet button--inline" type="submit">Accept cookies</button>' +
            '<a class="button govuk-button button--secondary-quiet button--inline" role="button" href="/cookies">Cookie settings</a>' +
          '</div>' +
        '</div>' +
        '<div id="dm-cookie-banner-confirmation" class="cookie-banner__confirmation govuk-width-container" style="display: none;">' +
          '<p class="cookie-banner__confirmation-message">' +
            'You have accepted all cookies' +
          '</p>' +
          '<button id="dm-hide-cookie-banner" class="cookie-banner__hide-button">Hide</button>' +
        '</div>' +
      '</div>'

    document.body.appendChild(container)

    // set and store default cookie consent to use as basis of comparison
    GOVUK.GDM.setDefaultConsentCookie()
    DEFAULT_COOKIE_CONSENT = GOVUK.GDM.getCookie('cookie_policy')
    element = document.querySelector('#global-cookie-message')
    GOVUK.GDM.setCookie('seen_cookie_message', null)
  })

  afterEach(function () {
    document.body.removeChild(container)
  })

  it('should show the cookie banner', function () {
    cookieBanner.start()
    var cookieBannerMain = document.querySelector('#dm-cookie-banner-message')
    var cookieBannerConfirmation = document.querySelector('#dm-cookie-banner-confirmation')

    expect(element.style.display).toEqual('block')
    expect(cookieBannerMain.style.display).toEqual('block')
    expect(cookieBannerConfirmation.style.display).toEqual('none')
  })

  it('sets a default consent cookie', function () {
    cookieBanner.start()
    expect(GOVUK.GDM.getCookie('cookie_policy')).toEqual(DEFAULT_COOKIE_CONSENT)
  })

  it('sets consent cookie when accepting cookies', function () {
    spyOn(GOVUK.GDM, 'setCookie').and.callThrough()
    cookieBanner.start()
    // Manually reset the consent cookie so we can check the accept button works as intended
    expect(GOVUK.GDM.getCookie('cookie_policy')).toEqual(DEFAULT_COOKIE_CONSENT)
    GOVUK.GDM.cookie('cookie_policy', null)

    var acceptCookiesButton = document.querySelector('#dm-accept-cookies')
    acceptCookiesButton.click()

    expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('seen_cookie_message', 'true', { days: 365 })
    expect(GOVUK.GDM.getCookie('cookie_policy')).toEqual(DEFAULT_COOKIE_CONSENT)
  })

  it('shows a confirmation message when cookies have been accepted', function () {
    cookieBanner.start()
    var acceptCookiesButton = document.querySelector('#dm-accept-cookies')
    var cookieBannerMain = document.querySelector('#dm-cookie-banner-message')
    var cookieBannerConfirmation = document.querySelector('#dm-cookie-banner-confirmation')

    expect(cookieBannerMain.style.display).toEqual('block')
    expect(cookieBannerConfirmation.style.display).toEqual('none')

    acceptCookiesButton.dispatchEvent(new window.Event('click'))

    expect(cookieBannerMain.style.display).toEqual('none')
    expect(cookieBannerConfirmation.style.display).toEqual('block')
  })

  it('should hide when pressing the "hide" link', function () {
    spyOn(GOVUK.GDM, 'setCookie').and.callThrough()
    cookieBanner.start()
    var hideLink = document.querySelector('#dm-hide-cookie-banner')
    hideLink.dispatchEvent(new window.Event('click'))

    expect(element.style.display).toEqual('none')
    expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('seen_cookie_message', 'true', { days: 365 })
    expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeTruthy()
  })

  it('does not show the banner if user has acknowledged the banner previously and consent cookie is present', function () {
    GOVUK.GDM.setCookie('seen_cookie_message', 'true')
    GOVUK.GDM.setDefaultConsentCookie()
    cookieBanner.start()

    expect(element.style.display).toEqual('none')
  })

  describe('when rendered inside an iframe', function () {
    var windowParent = window.parent
    var mockWindowParent = {} // window.parent would be different than window when used inside an iframe

    beforeEach(function () {
      window.parent = mockWindowParent
    })

    afterEach(function () {
      window.parent = windowParent
    })

    it('should hide the cookie banner', function () {
      cookieBanner.start()
      expect(element.style.display).toEqual('none')
    })
  })
})
