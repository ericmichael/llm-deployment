const path = require('path');

module.exports = {
  entry: './static/js/application.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'static/js'),
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      // Add this rule for CSS files
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  }
};