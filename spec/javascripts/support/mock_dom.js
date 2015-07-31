var jsdom = require('node-jsdom'),
    fs = require('fs'),
    path = require('path');

module.exports = {
  'onReady' : function (callback) {
    var manifestPath = path.normalize(__dirname + '/../manifest.js'),
        scripts;

    // makes the 'manifest' variable available
    eval(fs.readFileSync(manifestPath, { encoding : 'utf-8' }));

    scripts = manifest.support.map(function (filePath) {
      return fs.readFileSync(filePath.replace(/^(\.\.\/){3}/, ''), { encoding : 'utf-8' });
    });
    jsdom.env({
      html : '<html><body></body></html>',
      src : scripts,
      done : function(err, windowObj) {
        if (err) console.log(err);
        callback(windowObj);
      }
    });
  }
};
