// See https://github.com/alphagov/govuk_publishing_components/blob/master/spec/javascripts/govuk_publishing_components/lib/cookie-functions-spec.js

var GOVUK = window.GOVUK || {}
describe('Cookie helper functions', function () {
  'use strict'

  var resetCookies = function () {
    document.cookie.split(';').forEach(function (c) { document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/') })
  }

  afterEach(function() {
    resetCookies()
  })

  describe('GOVUK.cookie', function () {
    it('returns the cookie value if not provided with a value to set', function () {
      GOVUK.GDM.cookie('seen_cookie_message', 'testing fetching cookie value')

      GOVUK.GDM.cookie('seen_cookie_message')

      expect(GOVUK.GDM.cookie('seen_cookie_message')).toBe('testing fetching cookie value')
    })

    it('can create a new cookie', function () {
      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeFalsy()

      GOVUK.GDM.cookie('seen_cookie_message', 'test')

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBe('test')
    })

    it('sets a default expiry of 30 days if no options are provided', function () {
      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeFalsy()

      GOVUK.GDM.cookie('seen_cookie_message', 'test')

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('seen_cookie_message', 'test', { days: 30 })
    })

    it('sets the expiry if one is provided', function () {
      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeFalsy()

      GOVUK.GDM.cookie('seen_cookie_message', 'test', { days: 100 })

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('seen_cookie_message', 'test', { days: 100 })
    })

    it('can change the value of an existing cookie', function () {
      GOVUK.GDM.cookie('seen_cookie_message', 'test1')

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBe('test1')

      GOVUK.GDM.cookie('seen_cookie_message', 'test2')

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBe('test2')
    })

    it('deletes the cookie if value is set to false', function () {
      GOVUK.GDM.cookie('seen_cookie_message', false)

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeFalsy()
    })

    it('deletes the cookie if value is set to null', function () {
      GOVUK.GDM.cookie('seen_cookie_message', null)

      expect(GOVUK.GDM.getCookie('seen_cookie_message')).toBeFalsy()
    })
  })

  describe('consent cookie methods', function () {
    it('can set the consent cookie to default values', function () {
      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()

      expect(GOVUK.GDM.getCookie('cookie_policy')).toBeFalsy()

      GOVUK.GDM.setDefaultConsentCookie()

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('cookie_policy', '{"essential":true,"settings":true,"usage":true}', Object({ days: 365 }))
      expect(GOVUK.GDM.getConsentCookie()).toEqual({ 'essential': true, 'settings': true, 'usage': true })
    })

    it('can set the consent cookie to approve all cookie categories', function () {
      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()

      GOVUK.GDM.setConsentCookie({ 'usage': false, 'essential': false })

      expect(GOVUK.GDM.getConsentCookie().essential).toBe(false)
      expect(GOVUK.GDM.getConsentCookie().usage).toBe(false)

      GOVUK.GDM.approveAllCookieTypes()

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('cookie_policy', '{"essential":true,"settings":true,"usage":true}', Object({ days: 365 }))
      expect(GOVUK.GDM.getConsentCookie()).toEqual({ 'essential': true, 'settings': true, 'usage': true })
    })

    it('returns null if the consent cookie does not exist', function () {
      expect(GOVUK.GDM.getConsentCookie()).toEqual(null)
    })

    it('returns null if the consent cookie is malformed', function () {
      GOVUK.GDM.cookie('cookie_policy', 'malformed consent cookie')

      expect(GOVUK.GDM.getConsentCookie()).toBe(null)
    })

    it('deletes relevant cookies in that category if consent is set to false', function () {
      GOVUK.GDM.setConsentCookie({ 'essential': true })

      GOVUK.GDM.setCookie('seen_cookie_message', 'this is an essential cookie')

      expect(GOVUK.GDM.cookie('seen_cookie_message')).toBe('this is an essential cookie')

      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()
      GOVUK.GDM.setConsentCookie({ 'essential': false })

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith('cookie_policy', '{"essential":false,"settings":true,"usage":true}', Object({ days: 365 }))
      expect(GOVUK.GDM.getConsentCookie().essential).toBe(false)
      expect(GOVUK.GDM.cookie('seen_cookie_message')).toBeFalsy()
    })
  })

  describe('check cookie consent', function () {
    it('returns true if trying to set the consent cookie', function () {
      expect(GOVUK.GDM.checkConsentCookie('cookie_policy', { 'essential': true })).toBe(true)
    })

    it('returns true if deleting a cookie', function () {
      expect(GOVUK.GDM.checkConsentCookie('test_cookie', null)).toBe(true)
      expect(GOVUK.GDM.checkConsentCookie('test_cookie', false)).toBe(true)
    })

    it('does not set a default consent cookie if one is not present', function () {
      GOVUK.GDM.cookie('cookie_policy', null)

      GOVUK.GDM.checkConsentCookieCategory('seen_cookie_message', true)

      expect(GOVUK.GDM.getConsentCookie()).toBeFalsy()
    })

    it('returns true if the consent cookie does not exist and the cookie name is recognised', function () {
      expect(GOVUK.GDM.getConsentCookie()).toBeFalsy()

      expect(GOVUK.GDM.checkConsentCookie('seen_cookie_message', true)).toBe(true)
    })

    it('returns false if the consent cookie does not exist and the cookie name is not recognised', function () {
      expect(GOVUK.GDM.getConsentCookie()).toBeFalsy()

      expect(GOVUK.GDM.checkConsentCookie('fake_cookie')).toBe(false)
    })

    it('returns the consent for a given cookie', function () {
      GOVUK.GDM.setConsentCookie({ 'usage': false })

      expect(GOVUK.GDM.checkConsentCookie('_ga', 'set a usage cookie')).toBeFalsy()

      GOVUK.GDM.setConsentCookie({ 'usage': true })

      expect(GOVUK.GDM.checkConsentCookie('_ga', 'set a usage cookie')).toBeTruthy()
    })

    it('denies consent for cookies not in our list of cookies', function () {
      expect(GOVUK.GDM.checkConsentCookie('fake_cookie', 'just for testing')).toBeFalsy()
    })
  })
})
