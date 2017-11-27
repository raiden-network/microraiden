// rollup.config.js
import commonjs from 'rollup-plugin-commonjs';
import resolve from 'rollup-plugin-node-resolve';
import builtins from 'rollup-plugin-node-builtins';
import json from 'rollup-plugin-json';
import babel from 'rollup-plugin-babel';

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
    commonjs({
      namedExports: {
        'node_modules/eth-sig-util/index.js': ['typedSignatureHash', 'recoverTypedSignature'],
      }
    }),
    resolve({preferBuiltins: false, module: true}),
    builtins({crypto: true}),
    babel({
      exclude: ["node_modules/ethjs-util/**"],
      externalHelpers: true,
      presets: [ ["env", { modules: false, forceAllTransforms: true, targets: { node: 'current', browsers: 'last 2 versions', uglify: true } }] ],
      plugins: ["external-helpers"],
    })
  ]
};
