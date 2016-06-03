(function (root, GOVUK) {
  "use strict";

  // wrapper around access to window.location
  GOVUK.GDM.analytics.location = {
    'hostname': function () {
      return root.location.hostname;
    },
    'pathname': function () {
      return root.location.pathname;
    },
    'protocol': function () {
      return root.location.protocol;
    }
  };

  var LinkClick = function (e) {
      this.$target = $(e.target);
      this.text = this.$target.text(),
      this.href = this.$target.prop('href');

      // if the node clicked wasn't the link but a child of it
      if (this.$target[0].nodeName.toLowerCase() !== 'a') {
        this.$target = this.$target.closest('a');
        this.href = this.$target.prop('href');
      }
  };
  
  LinkClick.prototype.category = function () {
      var category = 'internal-link';

      if (this.fileType() !== null) { // download link
        category = 'download';
      }
      else if ($.inArray(GOVUK.GDM.analytics.location.protocol(), ['http:', 'https:']) && !this.isOnHostDomain(this.href)) {
        category = 'external-link';
      }
      return category;
  };
  LinkClick.prototype.isOnHostDomain = function (url) {
      var currentHost = GOVUK.GDM.analytics.location.hostname(),
          currentHostRegExp = (currentHost !== '') ? new RegExp(currentHost) : /^$/g;

      return url.match(currentHostRegExp) !== null;
  };
  LinkClick.prototype.fileType = function () {
      var match = this.href.match(/\.(pdf|pda|odt|ods|odp|zip|csv)$/),
          getExtensionFromHTML;

      getExtensionFromHTML = function ($link) {
        var $linkIcon = $link.find('.document-icon').clone();

        if (!$linkIcon.length) { return false; }

        $linkIcon.find('span').remove();
        return $linkIcon.text().toLowerCase();
      };

      if (match !== null) { 
        return match[1];
      } else {
        return getExtensionFromHTML(this.$target);
      }
  };
  
  var downloadLinkLabel = function (linkClick) {
    var path = GOVUK.GDM.analytics.location.pathname().match(/\/buyers\/frameworks\/([a-z\-]+)\/requirements\/([a-z\-]+)\/*(\d+)*/),
        lot = path[2],
        lots = {
          'digital-specialists': 'specialists',
          'digital-outcomes': 'outcomes',
          'user-research-participants': 'user research participants',
          'user-research-studios': 'user research studios'
        },
        briefId;

    if (linkClick.text.match('Download supplier responses') !== null) {
        briefId = path[3];
        return 'supplier response list' + ' | ' + lots[lot] + ' | ' + briefId;
    } else {
        switch (lot) {
          case 'digital-specialists':
            return 'list of specialists suppliers';
            break;
          case 'digital-outcomes':
            return 'list of outcomes suppliers';
            break;
          case 'user-research-participants':
            return 'list of user research participant suppliers';
            break;
          case 'user-research-studios':
            return 'list of user research labs';
            break;
          default:
            return false;
        }
    } 
  };

  GOVUK.GDM.analytics.LinkClick = LinkClick;

  GOVUK.GDM.analytics.events = {
    'supplierListDownload': function (e) {
      var linkClick = new LinkClick(e);

      if ((linkClick.category() === 'download') && (linkClick.fileType() === 'csv')) {
        GOVUK.analytics.trackEvent('download', 'csv', {
          'label': downloadLinkLabel(linkClick),
          'transport': 'beacon'
        });
      }
    },
    'init': function () {
      $('body').on('click', 'a', this.supplierListDownload)
    }
  };
})(window, window.GOVUK);
