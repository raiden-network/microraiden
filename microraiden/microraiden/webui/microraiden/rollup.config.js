// rollup.config.js
import commonjs from 'rollup-plugin-commonjs';
import resolve from 'rollup-plugin-node-resolve';
import builtins from 'rollup-plugin-node-builtins';
import json from 'rollup-plugin-json';

export default {
  input: 'dist/esm/index.js',
  output: {
    file: 'dist/umd/microraiden.js',
    format: 'umd',
  },
  name: 'microraiden',
  sourceMap: true,
  external: ['web3'],
  globals: ['web3:web3'],
  plugins: [
    json(),
    commonjs(),
    resolve({preferBuiltins: false, module: true}),
    builtins({crypto: true}),
  ]
};
