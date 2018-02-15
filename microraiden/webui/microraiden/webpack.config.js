// webpack.config.js
const webpack = require('webpack');
const path = require('path');

module.exports = {
  entry: {
    'microraiden': './dist/esm/index.js',
  },
  output: {
    path: path.resolve(__dirname, 'dist', 'umd'),
    filename: 'microraiden.js',
    library: 'microraiden',
    libraryTarget: 'umd'
  },
  module: {
    rules: [{
      test: /\.js$/,
      exclude: /ethjs-util/,
      use: [{
        loader: 'babel-loader',
        options: {
          presets: [
            ['env', { modules: false }]
          ]
        }
      }]
    }]
  }
};
