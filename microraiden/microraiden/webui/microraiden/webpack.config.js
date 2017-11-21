const path = require('path'),
      webpack = require('webpack');

module.exports = {
  entry: {
    'microraiden': './src/index.ts',
    'microraiden.min': './src/index.ts'
  },
  output: {
    path: path.resolve(__dirname, 'dist', 'umd'),
    filename: '[name].js',
    libraryTarget: 'umd',
    library: 'MicroRaiden',
    umdNamedDefine: true
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js']
  },
  devtool: 'source-map',
  plugins: [
    new webpack.optimize.UglifyJsPlugin({
      minimize: true,
      sourceMap: true,
      include: /\.min\.js$/,
    })
  ],
  module: {
    loaders: [{
      test: /\.tsx?$/,
      loader: 'awesome-typescript-loader',
      exclude: /node_modules/,
      query: {
        declaration: false,
      }
    }]
  }
}
