// See https://github.com/alphagov/frontend/blob/master/spec/javascripts/unit/modules/cookie-settings.spec.js
var GOVUK = window.GOVUK || {}
"use strict";
describe('cookieSettings', function() {
  var cookieSettings,
      container,
      element,
      confirmationContainer,
      errorContainer,
      warningContainer,
      fakePreviousURL;

  beforeEach(function() {
    GOVUK.analytics = {trackEvent: function () {}}
    cookieSettings = new GOVUK.GDM.CookieSettings()
    // Setting new cookie to make existing tests valid
    GOVUK.GDM.setCookie('cookie_preferences_set', true, { days: 365 });
    GOVUK.GDM.CookieSettings.prototype.getReferrerLink = function () {
      return fakePreviousURL
    }

    container = document.createElement('div')
    container.innerHTML =
      '<form id="cookie-settings">' +
        '<input type="radio" id="settings-on" name="cookies-settings" value="On">' +
        '<input type="radio" id="settings-off" name="cookies-settings" value="Off">' +
        '<input type="radio" id="usage-on" name="cookies-usage" value="On">' +
        '<input type="radio" id="usage-off" name="cookies-usage" value="Off">' +
        '<button id="submit-button" type="submit">Submit</button>' +
      '</form>'

    document.body.appendChild(container)

    confirmationContainer = document.createElement('div')
    confirmationContainer.style.display = "none"
    confirmationContainer.setAttribute('id', 'cookie-settings-confirmation')
    confirmationContainer.innerHTML =
      '<a class="cookie-settings__prev-page" href="#">View previous page</a>'

    document.body.appendChild(confirmationContainer)


    warningContainer = document.createElement('div')
    warningContainer.setAttribute('id', 'cookie-settings-warning')
    warningContainer.setAttribute('class', 'cookie-settings__warning')
    warningContainer.innerHTML =
      '<p>warning message<p>'

    document.body.appendChild(warningContainer)


    errorContainer = document.createElement('div')
    errorContainer.style.display = "none"
    errorContainer.setAttribute('id', 'cookie-settings-error')
    errorContainer.setAttribute('class', 'cookie-settings__error')
    errorContainer.innerHTML =
      '<p>Please select \'On\' or \'Off\' for all cookie choices<p>'

    document.body.appendChild(errorContainer)

    element = document.querySelector('#cookie-settings')
  });

  afterEach(function() {
    document.body.removeChild(container)
    document.body.removeChild(confirmationContainer)
    document.body.removeChild(errorContainer)
    document.body.removeChild(warningContainer)
  });

  describe('setInitialFormValues', function () {
    it('sets a consent cookie by default', function() {
      GOVUK.GDM.cookie('cookie_policy', null)

      spyOn(GOVUK.GDM, 'setDefaultConsentCookie').and.callThrough()
      cookieSettings.start()

      expect(GOVUK.GDM.setDefaultConsentCookie).toHaveBeenCalled()
    });

    it('sets all radio buttons to the default values', function() {
      cookieSettings.start()

      var radioButtons = element.querySelectorAll('input[value=on]')

      var consentCookieJSON = JSON.parse(GOVUK.GDM.cookie('cookie_policy'))

      for(var i = 0; i < radioButtons.length; i++) {
        var name = radioButtons[i].name.replace('cookies-', '')

        if (consentCookieJSON[name]) {
          expect(radioButtons[i].checked).toBeTruthy()
        } else {
          expect(radioButtons[i].checked).not.toBeTruthy()
        }
      }
    });
  });

  describe('submitSettingsForm', function() {
    it('updates consent cookie with any changes', function() {
      spyOn(GOVUK.GDM, 'setConsentCookie').and.callThrough()
      cookieSettings.start()

      element.querySelector('#settings-on').checked = false
      element.querySelector('#settings-off').checked = true
      element.querySelector('#usage-on').checked = true
      element.querySelector('#usage-off').checked = false

      var button = element.querySelector("#submit-button")
      button.click()

      var cookie = JSON.parse(GOVUK.GDM.cookie('cookie_policy'))

      expect(GOVUK.GDM.setConsentCookie).toHaveBeenCalledWith({"settings": false, "usage": true})
      expect(cookie['settings']).toBeFalsy()
    });

    it('sets seen_cookie_message cookie on form submit', function() {
      spyOn(GOVUK.GDM, 'setCookie').and.callThrough()
      cookieSettings.start()

      GOVUK.GDM.cookie('seen_cookie_message', null)

      expect(GOVUK.GDM.cookie('seen_cookie_message')).toEqual(null)

      var button = element.querySelector("#submit-button")
      button.click()

      expect(GOVUK.GDM.setCookie).toHaveBeenCalledWith("seen_cookie_message", true, { days: 365 } )
      expect(GOVUK.GDM.cookie('seen_cookie_message')).toBeTruthy()
    });

    it('fires a Google Analytics event', function() {
      spyOn(GOVUK.GDM.analytics.events, 'sendEvent').and.callThrough()
      cookieSettings.start()

      element.querySelector('#settings-on').checked = false
      element.querySelector('#settings-off').checked = true
      element.querySelector('#usage-on').checked = true
      element.querySelector('#usage-off').checked = false

      var button = element.querySelector("#submit-button")
      button.click()

      expect(GOVUK.GDM.analytics.events.sendEvent).toHaveBeenCalledWith('cookieSettings', 'Save changes', { label: 'settings-no usage-yes ' })
    });
  });

  describe('showConfirmationMessage', function () {
    it('sets the previous referrer link if one is present', function() {
      fakePreviousURL = "/student-finance"

      cookieSettings.start()

      var button = element.querySelector("#submit-button")
      button.click()

      var previousLink = document.querySelector('.cookie-settings__prev-page')

      expect(previousLink.style.display).toEqual("block")
      expect(previousLink.href).toContain('/student-finance')
    });

    it('does not set a referrer if one is not present', function() {
      fakePreviousURL = null

      cookieSettings.start()

      var button = element.querySelector("#submit-button")
      button.click()

      var previousLink = document.querySelector('.cookie-settings__prev-page')

      expect(previousLink.style.display).toEqual("none")
    });

    it('does not set a referrer if URL is the same as current page (cookies page)', function() {
      fakePreviousURL = document.location.pathname

      cookieSettings.start()

      var button = element.querySelector("#submit-button")
      button.click()

      var previousLink = document.querySelector('.cookie-settings__prev-page')

      expect(previousLink.style.display).toEqual("none")
    });

    it('shows a confirmation message', function() {
      var confirmationMessage = document.querySelector('#cookie-settings-confirmation')

      cookieSettings.start()

      var button = element.querySelector("#submit-button")
      button.click()

      expect(confirmationMessage.style.display).toEqual('block')
    });
  });

  describe('formBeforeUserSetsPreferences', function () {

    it('does not autofill any radio values', function() {
      GOVUK.GDM.setCookie('cookie_preferences_set', null);
      cookieSettings.start()
      var radioButtons = element.querySelectorAll('input[checked=true]')
      expect(radioButtons.length).toEqual(0);
    });

    it('does not set the cookie_preferences_set cookie on an invalid submit', function() {
      GOVUK.GDM.setCookie('cookie_preferences_set', null);
      cookieSettings.start()

      var button = element.querySelector("#submit-button")

      element.querySelector('#settings-off').checked = false
      element.querySelector('#settings-on').checked = false

      button.click()

      var errorMessage = document.querySelector('#cookie-settings-error')
      expect(errorMessage.style.display).toEqual('block')

      var cookie = JSON.parse(GOVUK.GDM.cookie('cookie_preferences_set'))
      expect(cookie).toBeFalsy()

    });

    it('sets the cookie_preferences_set cookie on a valid submit', function() {
      GOVUK.GDM.setCookie('cookie_preferences_set', null);
      cookieSettings.start()

      element.querySelector('#settings-off').checked = true
      element.querySelector('#usage-off').checked = true

      var button = element.querySelector("#submit-button")
      button.click()

      var cookie = JSON.parse(GOVUK.GDM.cookie('cookie_preferences_set'))
      expect(cookie).toBeTruthy()
    });

  });

});
