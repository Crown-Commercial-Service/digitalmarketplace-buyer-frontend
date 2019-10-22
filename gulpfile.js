const gulp = require('gulp')
const uglify = require('gulp-uglify')
const deleteFiles = require('del')
const sass = require('gulp-sass')
const filelog = require('gulp-filelog')
const include = require('gulp-include')
const jasmine = require('gulp-jasmine-phantom')
const path = require('path')
const sourcemaps = require('gulp-sourcemaps')

// Paths
let environment
const repoRoot = path.join(__dirname)
const npmRoot = path.join(repoRoot, 'node_modules')
const govukToolkitRoot = path.join(npmRoot, 'govuk_frontend_toolkit')
const govukElementsRoot = path.join(npmRoot, 'govuk-elements-sass')
const dmToolkitRoot = path.join(npmRoot, 'digitalmarketplace-frontend-toolkit', 'toolkit')
const sspContentRoot = path.join(npmRoot, 'digitalmarketplace-frameworks')
const assetsFolder = path.join(repoRoot, 'app', 'assets')
const staticFolder = path.join(repoRoot, 'app', 'static')
const govukTemplateFolder = path.join(repoRoot, 'node_modules', 'govuk_template')
const govukTemplateAssetsFolder = path.join(govukTemplateFolder, 'assets')
const govukTemplateLayoutsFolder = path.join(govukTemplateFolder, 'views', 'layouts')

// JavaScript paths
const jsSourceFile = path.join(assetsFolder, 'javascripts', 'application.js')
const jsDistributionFolder = path.join(staticFolder, 'javascripts')
const jsDistributionFile = 'application.js'

// CSS paths
const cssSourceGlob = path.join(assetsFolder, 'scss', 'application*.scss')
const cssDistributionFolder = path.join(staticFolder, 'stylesheets')

// Configuration
const sassOptions = {
  development: {
    outputStyle: 'expanded',
    lineNumbers: true,
    includePaths: [
      path.join(assetsFolder, 'scss'),
      path.join(dmToolkitRoot, 'scss'),
      path.join(govukToolkitRoot, 'stylesheets'),
      path.join(govukElementsRoot, 'public', 'sass')
    ],
    sourceComments: true,
    errLogToConsole: true
  },
  production: {
    outputStyle: 'compressed',
    lineNumbers: true,
    includePaths: [
      path.join(assetsFolder, 'scss'),
      path.join(dmToolkitRoot, 'scss'),
      path.join(govukToolkitRoot, 'stylesheets'),
      path.join(govukElementsRoot, 'public', 'sass')
    ]
  }
}

const uglifyOptions = {
  development: {
    mangle: false,
    output: {
      beautify: true,
      semicolons: true,
      comments: true,
      indent_level: 2
    },
    compress: false
  },
  production: {
    mangle: true
  }
}

const logErrorAndExit = function logErrorAndExit (err) {
  // coloured text: https://coderwall.com/p/yphywg/printing-colorful-text-in-terminal-when-run-node-js-script
  console.log('\x1b[41m\x1b[37m  Error: ' + err.message + '\x1b[0m')
  process.exit(1)
}

gulp.task('clean', function (cb) {
  var fileTypes = []
  const complete = function (fileType) {
    fileTypes.push(fileType)
    if (fileTypes.length === 2) {
      cb()
    }
  }
  const logOutputFor = function (fileType) {
    return function (_, paths) {
      if (paths !== undefined) {
        console.log('💥  Deleted the following ' + fileType + ' files:\n', paths.join('\n'))
      }
      complete(fileType)
    }
  }

  deleteFiles(path.join(jsDistributionFolder, '**', '*'), logOutputFor('JavaScript'))
  deleteFiles(path.join(cssDistributionFolder, '**', '*'), logOutputFor('CSS'))
})

gulp.task('sass', function () {
  const stream = gulp.src(cssSourceGlob)
    .pipe(filelog('Compressing SCSS files'))
    .pipe(
      sass(sassOptions[environment]))
    .on('error', logErrorAndExit)
    .pipe(gulp.dest(cssDistributionFolder))

  stream.on('end', function () {
    console.log('💾  Compressed CSS saved as .css files in ' + cssDistributionFolder)
  })

  return stream
})

gulp.task('js', function () {
  const stream = gulp.src(jsSourceFile)
    .pipe(filelog('Compressing JavaScript files'))
    .pipe(include({ hardFail: true }))
    .pipe(sourcemaps.init())
    .pipe(uglify(
      uglifyOptions[environment]
    ))
    .pipe(sourcemaps.write('./maps'))
    .pipe(gulp.dest(jsDistributionFolder))

  stream.on('end', function () {
    console.log('💾 Compressed JavaScript saved as ' + jsDistributionFolder + '/' + jsDistributionFile)
  })

  return stream
})

function copyFactory (resourceName, sourceFolder, targetFolder) {
  return function () {
    return gulp
      .src(path.join(sourceFolder, '**', '*'), { base: sourceFolder })
      .pipe(gulp.dest(targetFolder))
      .on('end', function () {
        console.log('📂  Copied ' + resourceName)
      })
  }
}

gulp.task(
  'copy:template_assets:stylesheets',
  copyFactory(
    'GOV.UK template stylesheets',
    path.join(govukTemplateAssetsFolder, 'stylesheets'),
    path.join(staticFolder, 'stylesheets')
  )
)

gulp.task(
  'copy:template_assets:images',
  copyFactory(
    'GOV.UK template images',
    path.join(govukTemplateAssetsFolder, 'images'),
    path.join(staticFolder, 'images')
  )
)

gulp.task(
  'copy:template_assets:javascripts',
  copyFactory(
    'GOV.UK template Javascript files',
    path.join(govukTemplateAssetsFolder, 'javascripts'),
    path.join(staticFolder, 'javascripts')
  )
)

gulp.task(
  'copy:dm_toolkit_assets:stylesheets',
  copyFactory(
    'stylesheets from the Digital Marketplace frontend toolkit',
    path.join(dmToolkitRoot, 'scss'),
    path.join('app', 'assets', 'scss', 'toolkit')
  )
)

gulp.task(
  'copy:dm_toolkit_assets:images',
  copyFactory(
    'images from the Digital Marketplace frontend toolkit',
    path.join(dmToolkitRoot, 'images'),
    path.join(staticFolder, 'images')
  )
)

gulp.task(
  'copy:govuk_toolkit_assets:images',
  copyFactory(
    'images from the GOVUK frontend toolkit',
    path.join(govukToolkitRoot, 'images'),
    path.join(staticFolder, 'images')
  )
)

gulp.task(
  'copy:dm_toolkit_assets:templates',
  copyFactory(
    'templates from the Digital Marketplace frontend toolkit',
    path.join(dmToolkitRoot, 'templates'),
    path.join('app', 'templates', 'toolkit')
  )
)

gulp.task(
  'copy:images',
  copyFactory(
    'image assets from app to static folder',
    path.join(assetsFolder, 'images'),
    path.join(staticFolder, 'images')
  )
)

gulp.task(
  'copy:svg',
  copyFactory(
    'image assets from app to static folder',
    path.join(assetsFolder, 'svg'),
    path.join(staticFolder, 'svg')
  )
)

gulp.task(
  'copy:govuk_template',
  copyFactory(
    'GOV.UK template into app folder',
    govukTemplateLayoutsFolder,
    path.join('app', 'templates', 'govuk')
  )
)

gulp.task(
  'copy:frameworks',
  copyFactory(
    'frameworks YAML into app folder',
    path.join(sspContentRoot, 'frameworks'),
    path.join('app', 'content', 'frameworks')
  )
)

gulp.task('test', function () {
  const manifest = require(path.join(repoRoot, 'spec', 'javascripts', 'manifest.js')).manifest

  manifest.support = manifest.support.map(function (val) {
    return val.replace(/^(\.\.\/){3}/, '')
  })
  manifest.test = manifest.test.map(function (val) {
    return val.replace(/^\.\.\//, 'spec/javascripts/')
  })

  return gulp.src(manifest.test)
    .pipe(jasmine({
      jasmine: '2.0',
      integration: true,
      abortOnFail: true,
      vendor: manifest.support
    }))
})

gulp.task('watch', ['build:development'], function () {
  const jsWatcher = gulp.watch([path.join(assetsFolder, '**', '*.js')], ['js'])
  const cssWatcher = gulp.watch([path.join(assetsFolder, '**', '*.scss')], ['sass'])
  const dmWatcher = gulp.watch([path.join(npmRoot, 'digitalmarketplace-frameworks', '**')], ['copy:frameworks'])
  const notice = function (event) {
    console.log('File ' + event.path + ' was ' + event.type + ' running tasks...')
  }

  cssWatcher.on('change', notice)
  jsWatcher.on('change', notice)
  dmWatcher.on('change', notice)
})

gulp.task('set_environment_to_development', function (cb) {
  environment = 'development'
  cb()
})

gulp.task('set_environment_to_production', function (cb) {
  environment = 'production'
  cb()
})

gulp.task(
  'copy',
  [
    'copy:frameworks',
    'copy:template_assets:images',
    'copy:template_assets:stylesheets',
    'copy:template_assets:javascripts',
    'copy:govuk_toolkit_assets:images',
    'copy:dm_toolkit_assets:stylesheets',
    'copy:dm_toolkit_assets:images',
    'copy:dm_toolkit_assets:templates',
    'copy:images',
    'copy:svg',
    'copy:govuk_template'
  ]
)

gulp.task(
  'compile',
  [
    'copy'
  ],
  function () {
    gulp.start('sass')
    gulp.start('js')
  }
)

gulp.task('build:development', ['set_environment_to_development', 'clean'], function () {
  gulp.start('compile')
})

gulp.task('build:production', ['set_environment_to_production', 'clean'], function () {
  gulp.start('compile')
})
